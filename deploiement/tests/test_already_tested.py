import urllib.error

import pytest

import already_tested
from already_tested import Api, proves_tested
from deployer import REPOSITORY

MAIN, HEAD, MERGE = "main1", "head2", "merge3"
GREEN_JOBS = [
    {"name": "tests", "conclusion": "success"},
    {"name": "specs", "conclusion": "success"},
]


def make_commit(tree, parents=()):
    return {"parents": [{"sha": sha} for sha in parents], "commit": {"tree": {"sha": tree}}}


def pr_run(run_id=1, conclusion="success", status="completed", repository=REPOSITORY, sha=HEAD):
    return {
        "id": run_id,
        "event": "pull_request",
        "head_sha": sha,
        "head_repository": {"full_name": repository},
        "status": status,
        "conclusion": conclusion,
    }


class FakeApi:
    """A merge of HEAD into MAIN with HEAD's tree, HEAD up to date, one green PR run"""

    def __init__(self):
        self.commits = {
            MERGE: make_commit("tree-a", (MAIN, HEAD)),
            HEAD: make_commit("tree-a", (MAIN,)),
        }
        self.behind = 0
        self.runs = [pr_run()]
        self.jobs_by_run = {1: GREEN_JOBS}

    def commit(self, sha):
        return self.commits[sha]

    def behind_by(self, base, head):
        assert (base, head) == (MAIN, HEAD)
        return self.behind

    def pull_request_runs(self, sha):
        return self.runs

    def jobs(self, run_id):
        return self.jobs_by_run[run_id]


@pytest.fixture
def api():
    return FakeApi()


def tested(api):
    return proves_tested(MERGE, api)[0]


def test_tree_tested_by_the_pr(api):
    assert tested(api)


def test_different_tree(api):
    api.commits[HEAD] = make_commit("tree-b", (MAIN,))

    assert not tested(api)


def test_head_that_does_not_contain_main(api):
    api.behind = 1

    assert not tested(api)


@pytest.mark.parametrize("parents", [(MAIN,), (MAIN, HEAD, "third")])
def test_not_a_merge_of_two_parents(api, parents):
    api.commits[MERGE] = make_commit("tree-a", parents)

    assert not tested(api)


def test_no_pr_run(api):
    api.runs = []

    assert not tested(api)


@pytest.mark.parametrize(
    "run",
    [
        pr_run(conclusion="failure"),
        pr_run(conclusion="cancelled"),
        pr_run(status="in_progress", conclusion=None),
        pr_run(sha="other"),
        {**pr_run(), "event": "push"},
    ],
    ids=["failed", "cancelled", "unfinished", "other-sha", "push"],
)
def test_run_that_proves_nothing(api, run):
    api.runs = [run]

    assert not tested(api)


def test_rerun_with_success_counts(api):
    # The runs list shows a run's latest attempt; the jobs endpoint, that attempt's jobs.
    api.runs = [pr_run(run_id=2)]
    api.jobs_by_run = {2: GREEN_JOBS}

    assert tested(api)


def test_run_of_a_fork(api):
    api.runs = [pr_run(repository="someone/outillerie")]

    assert not tested(api)


def test_run_of_a_deleted_fork_does_not_hide_a_green_run(api):
    api.runs = [{**pr_run(run_id=4), "head_repository": None}, pr_run(run_id=1)]

    assert tested(api)


@pytest.mark.parametrize("failed", ["tests", "specs"])
def test_required_job_not_successful(api, failed):
    api.jobs_by_run = {
        1: [
            {"name": job["name"], "conclusion": "skipped" if job["name"] == failed else "success"}
            for job in GREEN_JOBS
        ]
    }

    assert not tested(api)


def test_a_failed_run_next_to_a_green_one(api):
    api.runs = [pr_run(run_id=3, conclusion="failure"), pr_run(run_id=1)]

    assert tested(api)


def outputs_of_main(monkeypatch, tmp_path, api_class):
    output = tmp_path / "output"
    monkeypatch.setenv("GITHUB_SHA", MERGE)
    monkeypatch.setenv("GITHUB_TOKEN", "github_token_secret")
    monkeypatch.setenv("GITHUB_OUTPUT", str(output))
    monkeypatch.setattr(already_tested, "Api", api_class)
    already_tested.main()
    return output.read_text()


def test_main_writes_true_when_proven(monkeypatch, tmp_path):
    assert outputs_of_main(monkeypatch, tmp_path, lambda token: FakeApi()) == "tested=true\n"


def test_main_writes_false_on_an_http_error(monkeypatch, tmp_path, capsys):
    def failing_opener(request, timeout):
        raise urllib.error.HTTPError(request.full_url, 502, "Bad Gateway", {}, None)

    output = outputs_of_main(monkeypatch, tmp_path, lambda token: Api(token, failing_opener))

    assert output == "tested=false\n"
    assert "github_token_secret" not in capsys.readouterr().out
