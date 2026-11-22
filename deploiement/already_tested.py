#!/usr/bin/env python3
"""Tells the CI whether a main commit's tree was already tested by its pull request (ADR 0026).

Run by the already-tested job of ci.yml on a push to main; writes tested=true or tested=false to
$GITHUB_OUTPUT. Any doubt, an API error included, gives tested=false: the tests run again.
Standard library only, like deployer.py.
"""

import os
import sys

from deployer import REPOSITORY, REQUIRED_JOBS, GitHub


class Api(GitHub):
    def commit(self, sha):
        return self._request("GET", f"/repos/{REPOSITORY}/commits/{sha}")

    def behind_by(self, base, head):
        return self._request("GET", f"/repos/{REPOSITORY}/compare/{base}...{head}")["behind_by"]

    def pull_request_runs(self, sha):
        path = f"/repos/{REPOSITORY}/actions/workflows/ci.yml/runs"
        return self._request("GET", f"{path}?head_sha={sha}&event=pull_request&per_page=100")[
            "workflow_runs"
        ]


def proves_tested(sha, api):
    """Whether the merge commit's tree is the one a successful run of its PR tested, and why

    api: commit(sha), behind_by(base, head), pull_request_runs(sha) and jobs(run_id), the jobs
    of the run's latest attempt.
    """
    commit = api.commit(sha)
    parents = [parent["sha"] for parent in commit["parents"]]
    if len(parents) != 2:
        return False, "pas un commit de merge"
    main, head = parents
    if api.behind_by(main, head) != 0:
        return False, "la tête de la PR ne contient pas main"
    if api.commit(head)["commit"]["tree"]["sha"] != commit["commit"]["tree"]["sha"]:
        return False, "arbre différent de celui de la tête de la PR"
    for run in api.pull_request_runs(head):
        if _is_successful_run_of(run, head) and _required_jobs_succeeded(api.jobs(run["id"])):
            return True, f"arbre testé par le run {run['id']} de la PR"
    return False, "aucun run réussi de la PR sur cet arbre"


def _is_successful_run_of(run, head):
    return (
        run["event"] == "pull_request"
        and run["head_sha"] == head
        # None once the fork it came from is deleted.
        and (run["head_repository"] or {}).get("full_name") == REPOSITORY
        and (run["status"], run["conclusion"]) == ("completed", "success")
    )


def _required_jobs_succeeded(jobs):
    succeeded = {job["name"] for job in jobs if job["conclusion"] == "success"}
    return all(name in succeeded for name in REQUIRED_JOBS)


def main():
    try:
        tested, reason = proves_tested(os.environ["GITHUB_SHA"], Api(os.environ["GITHUB_TOKEN"]))
    except Exception as error:  # noqa: BLE001 - any doubt replays the tests
        tested, reason = False, f"preuve introuvable : {type(error).__name__}"
    print(f"tested={str(tested).lower()} : {reason}")
    with open(os.environ["GITHUB_OUTPUT"], "a") as output:
        output.write(f"tested={str(tested).lower()}\n")


if __name__ == "__main__":
    sys.exit(main())
