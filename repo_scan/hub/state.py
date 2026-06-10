"""File-backed run lifecycle + decision inbox.

Decisions are the multi-writer primitive: any surface (web UI, CLI, future
chat bots) submits a decision file keyed by (problem, gate); the gate itself
consumes it on the next pipeline pass. Files persist until the loop finishes

Vault: docs/tickets/tkt-0035
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
    from .events import broadcast
    broadcast({"type": "gate", "gate": gate, "decision": decision,
               "problem": problem[:80]})
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
    from .events import broadcast
    broadcast({"type": "run", "id": run["id"], "status": run["status"],
               "ticket": run.get("ticket")})
    return run


def update_run(root: Path, cfg: dict, run_id: str, status: str, **fields):
    if status not in RUN_STATUSES:
        raise ValueError(f"unknown run status {status!r}")
    with _RUNS_LOCK:
        runs = load_runs(root, cfg)
        updated = None
        for r in runs:
            if r["id"] == run_id:
                r["status"] = status
                r["updated_at"] = now_iso()
                r.update(fields)
                updated = dict(r)
                break
        _save_runs(root, cfg, runs)
    if updated:
        from .events import broadcast
        broadcast({"type": "run", "id": run_id, "status": status,
                   "gate": updated.get("gate"), "ticket": updated.get("ticket"),
                   "stage": updated.get("stage")})


def active_runs(root: Path, cfg: dict) -> list[dict]:
    return [r for r in load_runs(root, cfg)
            if r["status"] in ("queued", "running", "waiting-on-gate")]


def active_run(root: Path, cfg: dict) -> dict | None:
    active = active_runs(root, cfg)
    return active[-1] if active else None


def set_run_stage(root: Path, cfg: dict, problem: str, stage: str, detail: str = ""):
    """Update the live stage on a run record (no status change). No-op when
    no run record exists (e.g. manual CLI invocations outside the daemon)."""
    rid = problem_key(problem)
    with _RUNS_LOCK:
        runs = load_runs(root, cfg)
        for r in runs:
            if r["id"] == rid:
                r["stage"] = stage
                r["stage_detail"] = detail[:160]
                r["stage_started_at"] = now_iso()
                r["updated_at"] = now_iso()
                _save_runs(root, cfg, runs)
                from .events import broadcast
                broadcast({"type": "run", "id": rid, "status": r["status"],
                             "stage": stage, "stage_detail": detail[:80],
                             "ticket": r.get("ticket")})
                return


# --- agent event feed -----------------------------------------------------------

_EVENTS_LOCK = threading.Lock()
EVENTS_KEEP = 250


def append_event(root: Path, cfg: dict, kind: str, text: str, **fields):
    """One line in the shared agent feed (docs/.radar/events.jsonl).

    Every surface tails this to show what the agents are actually doing;
    capped so it never grows unbounded.
    """
    import time as _time
    path = state_dir(root, cfg) / "events.jsonl"
    event = {"ts": int(_time.time()), "when": now_iso(), "kind": kind,
             "text": text[:200], **fields}
    with _EVENTS_LOCK:
        with path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(event, separators=(",", ":")) + "\n")
        lines = path.read_text(encoding="utf-8").splitlines()
        if len(lines) > EVENTS_KEEP * 2:
            path.write_text("\n".join(lines[-EVENTS_KEEP:]) + "\n", encoding="utf-8")
    from .events import broadcast
    broadcast({"type": "feed", "feed_kind": kind, "text": text[:120]})


def load_events(root: Path, cfg: dict, limit: int = 30) -> list[dict]:
    path = state_dir(root, cfg) / "events.jsonl"
    if not path.exists():
        return []
    events = []
    for line in path.read_text(encoding="utf-8").splitlines()[-limit:]:
        try:
            events.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return events


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
