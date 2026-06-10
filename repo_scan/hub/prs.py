"""GitHub PR visibility + merge for the hub — `gh` CLI as the backend.

The act stage opens PRs; this module lets every surface (dashboard first)
see whether their checks pass and land the merge without leaving the phone.
Reads are cached briefly so the dashboard's poll loop doesn't hammer the
GitHub API; any write (merge, update-branch) invalidates the cache.

Check rollup -> one word: failing > pending > passing ("none" when the repo
has no checks configured). Merge is squash + delete-branch, matching the
one-commit-per-ticket shape acts produce.
"""

import json
import shutil
import subprocess
import threading
import time
from pathlib import Path

PR_CACHE_SECONDS = 60
_CACHE: dict = {"ts": 0.0, "root": None, "prs": []}
_CACHE_LOCK = threading.Lock()

_BAD = {"FAILURE", "ERROR", "TIMED_OUT", "CANCELLED", "STARTUP_FAILURE"}
_OK = {"SUCCESS", "NEUTRAL", "SKIPPED"}


def _gh(root: Path, *args: str, timeout: int = 30) -> subprocess.CompletedProcess:
    return subprocess.run(["gh", *args], cwd=root, capture_output=True,
                          text=True, timeout=timeout)


def checks_state(rollup: list[dict]) -> str:
    """Collapse a statusCheckRollup into failing | pending | passing | none."""
    if not rollup:
        return "none"
    verdicts = []
    for c in rollup:
        # CheckRun rows have status/conclusion; StatusContext rows have state
        v = (c.get("conclusion") or c.get("state") or c.get("status") or "").upper()
        verdicts.append(v)
    if any(v in _BAD for v in verdicts):
        return "failing"
    if any(v not in _OK for v in verdicts):
        return "pending"
    return "passing"


def list_open_prs(root: Path, fresh: bool = False) -> list[dict]:
    """Open PRs with check status, newest first. Cached for PR_CACHE_SECONDS."""
    with _CACHE_LOCK:
        if (not fresh and _CACHE["root"] == str(root)
                and time.time() - _CACHE["ts"] < PR_CACHE_SECONDS):
            return _CACHE["prs"]
    prs = _fetch_open_prs(root)
    with _CACHE_LOCK:
        _CACHE.update(ts=time.time(), root=str(root), prs=prs)
    return prs


def invalidate_cache():
    with _CACHE_LOCK:
        _CACHE["ts"] = 0.0


def _fetch_open_prs(root: Path) -> list[dict]:
    if not shutil.which("gh"):
        return []
    try:
        r = _gh(root, "pr", "list", "--state", "open", "--json",
                "number,title,headRefName,url,mergeable,isDraft,statusCheckRollup")
    except (subprocess.TimeoutExpired, OSError):
        return []
    if r.returncode != 0:
        return []
    try:
        rows = json.loads(r.stdout or "[]")
    except json.JSONDecodeError:
        return []
    prs = []
    for p in rows:
        branch = p.get("headRefName", "")
        ticket = branch.split("/", 1)[1] if branch.startswith("radar/") else None
        prs.append({
            "number": p.get("number"),
            "title": p.get("title", ""),
            "branch": branch,
            "ticket": ticket,
            "url": p.get("url", ""),
            "draft": bool(p.get("isDraft")),
            "mergeable": str(p.get("mergeable", "UNKNOWN")).upper(),
            "checks": checks_state(p.get("statusCheckRollup") or []),
        })
    prs.sort(key=lambda p: -(p["number"] or 0))
    return prs


def merge_pr(root: Path, cfg: dict, number: int) -> tuple[bool, str]:
    """Squash-merge a PR and delete its branch. Returns (ok, message)."""
    if not shutil.which("gh"):
        return False, "gh CLI not found on the hub machine"
    try:
        r = _gh(root, "pr", "merge", str(number), "--squash", "--delete-branch",
                timeout=120)
    except subprocess.TimeoutExpired:
        return False, "gh pr merge timed out"
    invalidate_cache()
    if r.returncode != 0:
        return False, (r.stderr.strip() or r.stdout.strip())[:300]
    _note_merged(root, cfg, number)
    return True, f"PR #{number} squash-merged, branch deleted"


def update_pr_branch(root: Path, number: int) -> tuple[bool, str]:
    """Merge the base branch into the PR branch (re-runs CI against current
    main — the fix for PRs failing on errors already solved upstream)."""
    if not shutil.which("gh"):
        return False, "gh CLI not found on the hub machine"
    try:
        r = _gh(root, "pr", "update-branch", str(number), timeout=60)
        if r.returncode != 0 and "unknown command" in (r.stderr or ""):
            # gh < 2.56 has no `pr update-branch` — same operation via REST
            r = _gh(root, "api", "-X", "PUT",
                    f"repos/:owner/:repo/pulls/{number}/update-branch", timeout=60)
    except subprocess.TimeoutExpired:
        return False, "gh pr update-branch timed out"
    invalidate_cache()
    if r.returncode != 0:
        return False, (r.stderr.strip() or r.stdout.strip())[:300]
    return True, f"PR #{number} branch updated — checks re-running"


def _note_merged(root: Path, cfg: dict, number: int):
    """Close the loop in the vault: ticket note + event + done status."""
    from ..tickets import append_ticket_note, load_tickets, set_ticket_status
    from .state import append_event
    # the PR just left the open list — the last cached snapshot still maps
    # its number to a ticket (invalidate_cache resets ts, not the list)
    with _CACHE_LOCK:
        cached = next((p for p in _CACHE["prs"] if p["number"] == number), None)
    ticket_id = cached["ticket"] if cached else None
    append_event(root, cfg, "run", f"PR #{number} merged from dashboard"
                 + (f" ({ticket_id})" if ticket_id else ""))
    if ticket_id and any(t["id"] == ticket_id for t in load_tickets(root, cfg)):
        append_ticket_note(root, cfg, ticket_id,
                           f"PR #{number} merged — rescan will confirm metrics")
        set_ticket_status(root, cfg, ticket_id, "done")
