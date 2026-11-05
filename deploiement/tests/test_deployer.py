import io
import urllib.error

import pytest

import deployer
from deployer import (
    GitHub,
    TransientError,
    backups_to_delete,
    choose_commit,
    excluded_commits,
    images_to_delete,
    is_green,
    new_state,
    record_failure,
    record_success,
    record_transient,
)

TOKEN = "github_pat_secret"
GREEN_JOBS = [
    {"name": "tests", "conclusion": "success"},
    {"name": "specs", "conclusion": "success"},
]


def make_run(sha, run_id=1, event="push", status="completed", conclusion="success", attempt=1):
    return {
        "id": run_id,
        "head_sha": sha,
        "head_branch": "main",
        "event": event,
        "status": status,
        "conclusion": conclusion,
        "run_attempt": attempt,
    }


def all_green(run_id):
    return GREEN_JOBS


def test_successful_push_run_is_green():
    assert is_green(make_run("a"), GREEN_JOBS)


@pytest.mark.parametrize("status", ["queued", "in_progress"])
def test_unfinished_run_is_not_green(status):
    assert not is_green(make_run("a", status=status, conclusion=None), GREEN_JOBS)


def test_failed_run_is_not_green():
    assert not is_green(make_run("a", conclusion="failure"), GREEN_JOBS)


@pytest.mark.parametrize(
    "jobs",
    [
        [{"name": "tests", "conclusion": "success"}, {"name": "specs", "conclusion": "skipped"}],
        [{"name": "specs", "conclusion": "success"}],
    ],
    ids=["skipped", "missing"],
)
def test_run_without_both_required_jobs_is_not_green(jobs):
    assert not is_green(make_run("a"), jobs)


def test_pull_request_run_is_not_green():
    assert not is_green(make_run("a", event="pull_request"), GREEN_JOBS)


def test_rerun_whose_latest_attempt_succeeded_is_green():
    assert is_green(make_run("a", attempt=2), GREEN_JOBS)


def test_newest_green_candidate_is_chosen():
    runs = [make_run("new", 2), make_run("old", 1)]

    assert choose_commit(["new", "old"], runs, all_green, set()) == "new"


def test_older_green_commit_is_chosen_when_main_head_is_red():
    jobs = {2: [{"name": "tests", "conclusion": "failure"}], 1: GREEN_JOBS}
    runs = [make_run("head", 2), make_run("older", 1)]

    assert choose_commit(["head", "older"], runs, jobs.__getitem__, set()) == "older"


def test_commit_without_run_is_not_chosen():
    assert choose_commit(["no-run"], [make_run("elsewhere")], all_green, set()) is None


def test_nothing_to_deploy_without_candidates():
    assert choose_commit([], [make_run("deployed")], all_green, set()) is None


def test_failed_commit_is_not_retried():
    assert choose_commit(["failed"], [make_run("failed")], all_green, {"failed"}) is None


def test_jobs_are_only_fetched_for_candidate_runs():
    fetched = []

    def jobs_of(run_id):
        fetched.append(run_id)
        return GREEN_JOBS

    choose_commit(["new"], [make_run("new", 2), make_run("unrelated", 1)], jobs_of, set())

    assert fetched == [2]


def test_success_makes_the_commit_deployed_and_keeps_the_previous_one():
    state = new_state("a")
    state["attempts"]["b"] = 1

    record_success(state, "b")

    assert (state["deployed"], state["previous"], state["attempts"]) == ("b", "a", {})


def test_failed_commit_is_excluded():
    state = new_state("a")

    record_failure(state, "b")
    record_failure(state, "b")

    assert state["failed"] == ["b"]
    assert excluded_commits(state) == {"b"}


def test_commit_is_excluded_after_three_transient_failures():
    state = new_state("a")

    outcomes = [record_transient(state, "b") for _ in range(3)]

    assert outcomes == [False, False, True]
    assert excluded_commits(state) == {"b"}
    assert "b" not in state["failed"]


def test_only_the_ten_newest_backups_are_kept():
    names = [f"20261104T{hour:02}0000Z-abc.dump" for hour in range(12)]

    assert backups_to_delete(names) == names[:2]


def test_no_backup_deleted_under_the_limit():
    assert backups_to_delete(["20261104T000000Z-abc.dump"]) == []


def test_images_of_deployed_and_previous_commits_are_kept():
    state = new_state("c")
    state["previous"] = "b"

    assert images_to_delete(["a", "b", "c", "dev"], state) == ["a", "dev"]


def failing_opener(error):
    def open_request(request, timeout):
        raise error

    return open_request


@pytest.mark.parametrize(
    "error",
    [
        urllib.error.HTTPError(
            "https://api.github.com", 401, TOKEN, {}, io.BytesIO(TOKEN.encode())
        ),
        urllib.error.URLError(TOKEN),
    ],
    ids=["http", "network"],
)
def test_api_failure_is_transient_and_never_shows_the_token(error):
    with pytest.raises(TransientError) as failure:
        GitHub(TOKEN, failing_opener(error)).push_runs()

    assert TOKEN not in str(failure.value)
    assert failure.value.__cause__ is None


def test_status_failure_is_logged_without_the_token(capsys):
    error = urllib.error.HTTPError("https://api.github.com", 403, TOKEN, {}, None)

    GitHub(TOKEN, failing_opener(error)).post_status("abc", "failure")

    output = capsys.readouterr().out
    assert "403" in output
    assert TOKEN not in output


def test_token_travels_in_a_header_only():
    sent = []

    def open_request(request, timeout):
        sent.append(request)
        return io.BytesIO(b'{"jobs": []}')

    GitHub(TOKEN, open_request).jobs(7)

    assert sent[0].get_header("Authorization") == f"Bearer {TOKEN}"
    assert TOKEN not in sent[0].full_url


def test_status_carries_no_description():
    sent = []

    def open_request(request, timeout):
        sent.append(request)
        return io.BytesIO(b"{}")

    GitHub(TOKEN, open_request).post_status("abc", "success")

    assert deployer.json.loads(sent[0].data) == {"state": "success", "context": "deploiement"}
