"""File-backed run lifecycle + decision inbox.

Decisions are the multi-writer primitive: any surface (web UI, CLI, future
chat bots) submits a decision file keyed by (problem, gate); the gate itself
consumes it on the next pipeline pass. Files persist until the loop finishes
so re-running a paused loop is idempotent — earlier gates re-pass from their
recorded decisions instead of re-prompting.

Run records give remote surfaces something to render: each loop run moves
through queued -> running -> waiting-on-gate -> done/stopped/failed.
"""

import hashlib
import json
import secrets
import threading
from pathlib import Path

from ..utils import now_iso

RUN_STATUSES = ("queued", "running", "waiting-on-gate", "done", "stopped", "failed")

# guards runs.json read-modify-write within one process (daemon thread,
# server thread, and parallel act threads all share it)
_RUNS_LOCK = threading.Lock()


def state_dir(root: Path, cfg: dict) -> Path:
    d = root / cfg["docs_dir"] / ".radar"
    d.mkdir(parents=True, exist_ok=True)
    return d


def problem_key(problem: str) -> str:
    return hashlib.sha1(problem.strip().encode("utf-8")).hexdigest()[:12]


# --- decision inbox ---------------------------------------------------------

def _decisions_dir(root: Path, cfg: dict) -> Path:
    d = state_dir(root, cfg) / "decisions"
    d.mkdir(parents=True, exist_ok=True)
    return d


def submit_decision(root: Path, cfg: dict, gate: str, problem: str,
                    decision: str, comment: str = "", source: str = "web") -> Path:
    """Record a human decision for a (problem, gate) pair. First write wins."""
    if decision not in ("approve", "reject"):
        raise ValueError(f"decision must be approve|reject, got {decision!r}")
    path = _decisions_dir(root, cfg) / f"{problem_key(problem)}-{gate}.json"
    if path.exists():
        return path  # idempotency guard: a decision already stands
    path.write_text(json.dumps({
        "gate": gate,
        "problem": problem,
        "decision": decision,
        "comment": comment,
        "source": source,
        "decided_at": now_iso(),
    }, indent=2) + "\n", encoding="utf-8")
    return path


def peek_decision(root: Path, cfg: dict, gate: str, problem: str) -> dict | None:
    path = _decisions_dir(root, cfg) / f"{problem_key(problem)}-{gate}.json"
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None


def clear_decisions(root: Path, cfg: dict, problem: str):
    """Drop all decisions for a problem once its loop fully ends."""
    key = problem_key(problem)
    for path in _decisions_dir(root, cfg).glob(f"{key}-*.json"):
        path.unlink()


# --- loop checkpoints -------------------------------------------------------

def _checkpoints_dir(root: Path, cfg: dict) -> Path:
    d = state_dir(root, cfg) / "checkpoints"
    d.mkdir(parents=True, exist_ok=True)
    return d


def load_checkpoint(root: Path, cfg: dict, problem: str) -> dict:
    path = _checkpoints_dir(root, cfg) / f"{problem_key(problem)}.json"
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def save_checkpoint(root: Path, cfg: dict, problem: str, ckpt: dict):
    path = _checkpoints_dir(root, cfg) / f"{problem_key(problem)}.json"
    path.write_text(json.dumps(ckpt, indent=2, default=str) + "\n", encoding="utf-8")


def clear_checkpoint(root: Path, cfg: dict, problem: str):
    path = _checkpoints_dir(root, cfg) / f"{problem_key(problem)}.json"
    if path.exists():
        path.unlink()


# --- run records -------------------------------------------------------------

def _runs_path(root: Path, cfg: dict) -> Path:
    return state_dir(root, cfg) / "runs.json"


def load_runs(root: Path, cfg: dict) -> list[dict]:
    path = _runs_path(root, cfg)
    if not path.exists():
        return []
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return []


def _save_runs(root: Path, cfg: dict, runs: list[dict]):
    _runs_path(root, cfg).write_text(
        json.dumps(runs, indent=2) + "\n", encoding="utf-8")


def create_run(root: Path, cfg: dict, problem: str, ticket: str | None = None,
               kind: str = "loop") -> dict:
    with _RUNS_LOCK:
        runs = load_runs(root, cfg)
        run = {
            "id": problem_key(problem),
            "problem": problem,
            "ticket": ticket,
            "kind": kind,
            "status": "queued",
            "gate": None,
            "created_at": now_iso(),
            "updated_at": now_iso(),
        }
        # one record per problem: restarting a known problem reuses its slot
        runs = [r for r in runs if r["id"] != run["id"]]
        runs.append(run)
        _save_runs(root, cfg, runs[-50:])
        return run


def update_run(root: Path, cfg: dict, run_id: str, status: str, **fields):
    if status not in RUN_STATUSES:
        raise ValueError(f"unknown run status {status!r}")
    with _RUNS_LOCK:
        runs = load_runs(root, cfg)
        for r in runs:
            if r["id"] == run_id:
                r["status"] = status
                r["updated_at"] = now_iso()
                r.update(fields)
                break
        _save_runs(root, cfg, runs)


def active_runs(root: Path, cfg: dict) -> list[dict]:
    return [r for r in load_runs(root, cfg)
            if r["status"] in ("queued", "running", "waiting-on-gate")]


def active_run(root: Path, cfg: dict) -> dict | None:
    active = active_runs(root, cfg)
    return active[-1] if active else None


# --- meta (daemon bookkeeping) ------------------------------------------------

def load_meta(root: Path, cfg: dict) -> dict:
    path = state_dir(root, cfg) / "meta.json"
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def save_meta(root: Path, cfg: dict, meta: dict):
    (state_dir(root, cfg) / "meta.json").write_text(
        json.dumps(meta, indent=2) + "\n", encoding="utf-8")


# --- auth token ----------------------------------------------------------------

def get_token(root: Path, cfg: dict) -> str:
    """Stable per-repo bearer token for the dashboard. Created on first use."""
    path = state_dir(root, cfg) / "token"
    if path.exists():
        token = path.read_text(encoding="utf-8").strip()
        if token:
            return token
    token = secrets.token_urlsafe(16)
    path.write_text(token + "\n", encoding="utf-8")
    return token
