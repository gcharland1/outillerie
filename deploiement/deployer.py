#!/usr/bin/env python3
"""Deploys the newest green commit of main on the production server (ADR 0017).

Run every 5 minutes by outillerie-deploiement.timer, from the copy installer.sh puts next to the
deployment state; the unit gives the checkout in OUTILLERIE_CHECKOUT. See deploiement/README.md.
Standard library only: it runs on the server's python3, outside the app's environment.
"""

import fcntl
import json
import os
import shutil
import subprocess
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

REPOSITORY = "gcharland1/outillerie"
API = "https://api.github.com"
COMPOSE_PROJECT = "outillerie-prod"
APP_IMAGE = "outillerie-app"
REQUIRED_JOBS = ("tests", "specs")
WAIT_TIMEOUT_SECONDS = 120
BACKUPS_KEPT = 10
MAX_TRANSIENT_ATTEMPTS = 3
MIN_FREE_BYTES = 2 * 1024**3

# No server path in this public repository: installer.sh writes them into the unit.
CHECKOUT = Path(os.getenv("OUTILLERIE_CHECKOUT", ""))
HOME = Path(os.getenv("OUTILLERIE_DEPLOIEMENT") or Path(__file__).resolve().parent)
STATE_FILE = HOME / "etat.json"
TOKEN_FILE = HOME / "jeton"
LOCK_FILE = HOME / "verrou"
BACKUPS = HOME / "sauvegardes"


class TransientError(Exception):
    """A failure that does not come from the deployed code: retried on a later run"""


class StateError(Exception):
    """The installation needs a manual fix before any deploy"""


class DirtyCheckoutError(Exception):
    """A tracked file of the production checkout was modified by hand"""


def is_green(run, jobs):
    """Whether a CI run proves its commit green: a finished, successful push run on main
    whose required jobs all succeeded (a skipped job leaves the run itself successful)"""
    if (run["event"], run["head_branch"]) != ("push", "main"):
        return False
    if (run["status"], run["conclusion"]) != ("completed", "success"):
        return False
    succeeded = {job["name"] for job in jobs if job["conclusion"] == "success"}
    return all(name in succeeded for name in REQUIRED_JOBS)


def choose_commit(candidates, runs, jobs_of, excluded):
    """Returns the first green candidate that is not excluded, or None.

    candidates: main commits descending from the deployed one, newest first.
    jobs_of: run id -> jobs of the run's latest attempt; only called for plausible runs.
    """
    runs_by_sha = {}
    for run in runs:
        runs_by_sha.setdefault(run["head_sha"], []).append(run)
    for sha in candidates:
        if sha in excluded:
            continue
        if any(is_green(run, jobs_of(run["id"])) for run in runs_by_sha.get(sha, [])):
            return sha
    return None


def new_state(deployed):
    return {"deployed": deployed, "previous": None, "failed": [], "attempts": {}, "blocked": False}


def excluded_commits(state):
    """Commits never retried: failed to deploy, or out of transient attempts"""
    exhausted = {sha for sha, n in state["attempts"].items() if n >= MAX_TRANSIENT_ATTEMPTS}
    return set(state["failed"]) | exhausted


def record_success(state, sha):
    state["previous"] = state["deployed"]
    state["deployed"] = sha
    state["attempts"].pop(sha, None)
    state.pop("dirty_reported", None)


def record_failure(state, sha):
    if sha not in state["failed"]:
        state["failed"].append(sha)
    state["attempts"].pop(sha, None)


def record_transient(state, sha):
    """Counts a transient failure; returns whether the commit is now out of attempts"""
    state["attempts"][sha] = state["attempts"].get(sha, 0) + 1
    return state["attempts"][sha] >= MAX_TRANSIENT_ATTEMPTS


def backups_to_delete(names, kept=BACKUPS_KEPT):
    """Backup file names beyond the newest `kept`; names start with a sortable timestamp"""
    return sorted(names)[:-kept] if len(names) > kept else []


def images_to_delete(tags, state):
    """App image tags other than the deployed and previous commits'"""
    kept = {state["deployed"], state["previous"]}
    return [tag for tag in tags if tag not in kept]


class GitHub:
    """Minimal GitHub REST client; the token only ever travels in a request header"""

    def __init__(self, token, opener=urllib.request.urlopen):
        self._token = token
        self._open = opener

    def _request(self, method, path, body=None):
        request = urllib.request.Request(
            API + path,
            method=method,
            data=None if body is None else json.dumps(body).encode(),
            headers={
                "Accept": "application/vnd.github+json",
                "Authorization": f"Bearer {self._token}",
                "X-GitHub-Api-Version": "2022-11-28",
            },
        )
        try:
            with self._open(request, timeout=30) as response:
                return json.load(response)
        except urllib.error.HTTPError as error:
            raise TransientError(f"GitHub {method} {path}: HTTP {error.code}") from None
        except (urllib.error.URLError, TimeoutError) as error:
            raise TransientError(f"GitHub {method} {path}: {type(error).__name__}") from None

    def push_runs(self):
        path = f"/repos/{REPOSITORY}/actions/workflows/ci.yml/runs"
        query = "?branch=main&event=push&status=success&per_page=100"
        return self._request("GET", path + query)["workflow_runs"]

    def jobs(self, run_id):
        return self._request("GET", f"/repos/{REPOSITORY}/actions/runs/{run_id}/jobs")["jobs"]

    def post_status(self, sha, state):
        """Publishes success or failure on the commit, without details; never fails a deploy"""
        try:
            self._request(
                "POST",
                f"/repos/{REPOSITORY}/statuses/{sha}",
                {"state": state, "context": "deploiement"},
            )
        except TransientError as error:
            log(f"Statut {state} non publié : {error}")


def log(message):
    print(message, flush=True)


def run(*command, env=None, stdout=None):
    """Runs a command in the checkout; its output goes to the journal"""
    return subprocess.run(command, cwd=CHECKOUT, env=env, stdout=stdout, check=True, text=True)


def git_output(*args):
    return run("git", *args, stdout=subprocess.PIPE).stdout.split()


def compose(*args, tag, stdout=None, skip_db_upgrade=False):
    env = {**os.environ, "APP_TAG": tag, "SKIP_DB_UPGRADE": "1" if skip_db_upgrade else "0"}
    return run("docker", "compose", "-p", COMPOSE_PROJECT, *args, env=env, stdout=stdout)


def up(tag, *options, skip_db_upgrade=False):
    wait = ("--wait", "--wait-timeout", str(WAIT_TIMEOUT_SECONDS))
    compose("up", "-d", *wait, *options, tag=tag, skip_db_upgrade=skip_db_upgrade)


def load_state():
    if not STATE_FILE.exists():
        sys.exit(f"{STATE_FILE} absent : amorcer le déploiement (deploiement/README.md)")
    return json.loads(STATE_FILE.read_text())


def save_state(state):
    temporary = STATE_FILE.with_suffix(".tmp")
    temporary.write_text(json.dumps(state, indent=2) + "\n")
    temporary.replace(STATE_FILE)


def candidates(deployed):
    try:
        run("git", "fetch", "--quiet", "origin", "main")
    except subprocess.CalledProcessError as error:
        raise TransientError("git fetch en échec") from error
    # Bootstrapped on a branch that main then squashed or rebased: nothing would ever deploy.
    on_main = subprocess.run(
        ("git", "merge-base", "--is-ancestor", deployed, "origin/main"), cwd=CHECKOUT
    )
    if on_main.returncode != 0:
        raise StateError(f"{deployed} absent de main : réamorcer (deploiement/README.md)")
    try:
        return git_output("rev-list", "--ancestry-path", "--topo-order", f"{deployed}..origin/main")
    except subprocess.CalledProcessError as error:
        raise TransientError("git rev-list en échec") from error


def ensure_clean_checkout():
    changes = run("git", "status", "--porcelain", "--untracked-files=no", stdout=subprocess.PIPE)
    if changes.stdout.strip():
        raise DirtyCheckoutError(changes.stdout.strip())


def ensure_free_space():
    docker_root = run(
        "docker", "info", "--format", "{{.DockerRootDir}}", stdout=subprocess.PIPE
    ).stdout.strip()
    for path in (Path(docker_root), BACKUPS):
        try:
            free = shutil.disk_usage(path).free
        except PermissionError:
            free = shutil.disk_usage(path.parent).free
        if free < MIN_FREE_BYTES:
            raise TransientError(f"Espace libre insuffisant pour {path} : {free // 1024**2} Mio")


def back_up(state, sha):
    """Dumps the production database; credentials stay inside the db container"""
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    target = BACKUPS / f"{stamp}-{sha[:12]}.dump"
    descriptor = os.open(target, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        with os.fdopen(descriptor, "w") as output:
            compose(
                "exec",
                "-T",
                "db",
                "sh",
                "-c",
                'pg_dump -Fc -U "$POSTGRES_USER" "$POSTGRES_DB"',
                tag=state["deployed"],
                stdout=output,
            )
    except subprocess.CalledProcessError as error:
        target.unlink(missing_ok=True)
        raise TransientError("Sauvegarde en échec") from error
    for name in backups_to_delete([path.name for path in BACKUPS.glob("*.dump")]):
        (BACKUPS / name).unlink()
    log(f"Sauvegarde : {target}")


def remove_old_images(state):
    """Frees disk space; a failure here never fails the deploy that just succeeded"""
    try:
        tags = run(
            "docker", "image", "ls", APP_IMAGE, "--format", "{{.Tag}}", stdout=subprocess.PIPE
        ).stdout.split()
        for tag in images_to_delete(tags, state):
            run("docker", "image", "rm", f"{APP_IMAGE}:{tag}")
        run("docker", "image", "prune", "-f")
    except subprocess.CalledProcessError as error:
        log(f"Nettoyage des images incomplet : {error}")


def restore_checkout(state):
    try:
        run("git", "checkout", "--quiet", "--detach", state["deployed"])
    except subprocess.CalledProcessError as error:
        # The checkout no longer matches the running version: stop until someone looks.
        state["blocked"] = True
        raise StateError(f"Checkout non ramené sur {state['deployed']} : intervention") from error


def roll_back(state, sha):
    """Restarts the deployed commit's checkout and image, without running any migration:
    the old code does not know a revision the failed commit may have applied (ADR 0007)"""
    deployed = state["deployed"]
    log(f"{sha} ne devient pas sain : retour à {deployed}")
    record_failure(state, sha)
    try:
        run("git", "checkout", "--quiet", "--detach", deployed)
        up(deployed, "--no-build", "--pull", "never", skip_db_upgrade=True)
    except subprocess.CalledProcessError:
        state["blocked"] = True
        log("Retour arrière en échec : déploiements bloqués jusqu'à une intervention manuelle")


def deploy(state, github):
    """Deploys the commit to deploy, if any; returns (sha, "success" | "failure") or None"""
    sha = choose_commit(
        candidates(state["deployed"]), github.push_runs(), github.jobs, excluded_commits(state)
    )
    if sha is None:
        log("Aucun commit à déployer")
        return None
    log(f"Déploiement de {sha}")
    try:
        ensure_clean_checkout()
        ensure_free_space()
        back_up(state, sha)
        run("git", "checkout", "--quiet", "--detach", sha)
        compose("build", "app", tag=sha)
    except DirtyCheckoutError as error:
        log(f"Checkout modifié à la main, déploiement refusé :\n{error}")
        # Published once per commit, not on every 5-minute run.
        if state.get("dirty_reported") == sha:
            return None
        state["dirty_reported"] = sha
        return sha, "failure"
    except (TransientError, subprocess.CalledProcessError) as error:
        exhausted = record_transient(state, sha)
        log(f"Échec transitoire ({error}) ; tentative {state['attempts'][sha]}")
        restore_checkout(state)
        return (sha, "failure") if exhausted else None
    try:
        up(sha)
    except subprocess.CalledProcessError:
        roll_back(state, sha)
        return sha, "failure"
    record_success(state, sha)
    remove_old_images(state)
    log(f"{sha} déployé")
    return sha, "success"


def main():
    if not os.getenv("OUTILLERIE_CHECKOUT"):
        sys.exit("OUTILLERIE_CHECKOUT absent : lancer par l'unité qu'installe installer.sh")
    with open(LOCK_FILE, "w") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            log("Un déploiement est déjà en cours")
            return 0
        state = load_state()
        if state["blocked"]:
            log(f'Déploiements bloqués : retirer "blocked" de {STATE_FILE} après intervention')
            return 1
        github = GitHub(TOKEN_FILE.read_text().strip())
        try:
            outcome = deploy(state, github)
        except TransientError as error:
            log(f"Échec transitoire : {error}")
            return 1
        except StateError as error:
            log(str(error))
            return 1
        except subprocess.CalledProcessError as error:
            log(f"Commande en échec : {error}")
            return 1
        finally:
            save_state(state)
        if outcome is not None:
            github.post_status(*outcome)
        return 0 if outcome is None or outcome[1] == "success" else 1


if __name__ == "__main__":
    sys.exit(main())
