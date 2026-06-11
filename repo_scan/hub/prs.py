"""GitHub PR visibility + merge/remediation for the hub — `gh` CLI backend.

The act stage opens PRs; this module lets every surface (dashboard first)
see whether their checks pass, land the merge without leaving the phone,
and when checks fail or the branch conflicts, diagnose the blocker and
(optionally) spawn an agent fix on the PR branch.

Reads are cached briefly so the dashboard's poll loop doesn't hammer the
GitHub API; any write (merge, update-branch, remediate) invalidates it.

Vault: docs/tickets/tkt-0014
Vault: docs/changelog/2026-06-11-boundary-hardening
"""

import json
import shutil
import subprocess
import tempfile
import threading
import time
import uuid
from pathlib import Path

PR_CACHE_SECONDS = 60
_DIAG_DIR = ".radar/pr-diagnosis"
_CACHE: dict = {"ts": 0.0, "root": None, "prs": []}
_CACHE_LOCK = threading.Lock()
_REMEDIATE_THREADS: dict[int, threading.Thread] = {}

_BAD = {"FAILURE", "ERROR", "TIMED_OUT", "CANCELLED", "STARTUP_FAILURE"}
_OK = {"SUCCESS", "NEUTRAL", "SKIPPED"}

CONFLICT_PROMPT = """This branch has merge conflicts with {base}.
Resolve them: keep this branch's intent (the RADAR implementation) while
incorporating upstream changes from {base}. Edit conflict markers in place.
Do NOT commit or create branches. Reply with a one-paragraph summary.

Conflicting files:
{files}

Conflict excerpt (truncated):
---
{excerpt}
---"""

CI_FIX_PROMPT = """A pull request branch has failing CI. Fix the failures.
Keep changes minimal and consistent with the repo. Do NOT commit or create
branches. Reply with a one-paragraph summary.

Test command: {test_cmd}

CI failure log (truncated):
---
{ci_log}
---

Local test output (if any):
---
{local_log}
---"""


def _gh(root: Path, *args: str, timeout: int = 30) -> subprocess.CompletedProcess:
    return subprocess.run(["gh", *args], cwd=root, capture_output=True,
                          text=True, timeout=timeout)


def _git(root: Path, *args: str, timeout: int = 60) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *args], cwd=root, capture_output=True,
                          text=True, timeout=timeout)


def checks_state(rollup: list[dict]) -> str:
    """Collapse a statusCheckRollup into failing | pending | passing | none."""
    if not rollup:
        return "none"
    verdicts = []
    for c in rollup:
        v = (c.get("conclusion") or c.get("state") or c.get("status") or "").upper()
        verdicts.append(v)
    if any(v in _BAD for v in verdicts):
        return "failing"
    if any(v not in _OK for v in verdicts):
        return "pending"
    return "passing"


def _ticket_from_branch(branch: str) -> str | None:
    return branch.split("/", 1)[1] if branch.startswith("radar/") else None


def _pr_row(p: dict) -> dict:
    branch = p.get("headRefName", "")
    return {
        "number": p.get("number"),
        "title": p.get("title", ""),
        "branch": branch,
        "ticket": _ticket_from_branch(branch),
        "url": p.get("url", ""),
        "draft": bool(p.get("isDraft")),
        "mergeable": str(p.get("mergeable", "UNKNOWN")).upper(),
        "checks": checks_state(p.get("statusCheckRollup") or []),
    }


def list_open_prs(root: Path, cfg: dict | None = None, fresh: bool = False) -> list[dict]:
    """Open PRs with check status, newest first. Cached for PR_CACHE_SECONDS."""
    with _CACHE_LOCK:
        if (not fresh and _CACHE["root"] == str(root)
                and time.time() - _CACHE["ts"] < PR_CACHE_SECONDS):
            prs = [dict(p) for p in _CACHE["prs"]]
        else:
            prs = _fetch_open_prs(root)
            _CACHE.update(ts=time.time(), root=str(root), prs=prs)
    if cfg:
        for pr in prs:
            diag = load_diagnosis(root, cfg, pr["number"])
            if diag:
                pr["diagnosis"] = diag
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
    prs = [_pr_row(p) for p in rows]
    prs.sort(key=lambda p: -(p["number"] or 0))
    return prs


def fetch_pr(root: Path, number: int) -> dict | None:
    """Single open PR with base branch + rollup (not cached)."""
    if not shutil.which("gh"):
        return None
    try:
        r = _gh(root, "pr", "view", str(number), "--json",
                "number,title,headRefName,baseRefName,url,mergeable,"
                "mergeStateStatus,isDraft,statusCheckRollup")
    except (subprocess.TimeoutExpired, OSError):
        return None
    if r.returncode != 0:
        return None
    try:
        return _pr_row(json.loads(r.stdout or "{}"))
    except json.JSONDecodeError:
        return None


def _diag_path(root: Path, cfg: dict, number: int) -> Path:
    return root / cfg["docs_dir"] / _DIAG_DIR / f"{number}.json"


def load_diagnosis(root: Path, cfg: dict, number: int) -> dict | None:
    path = _diag_path(root, cfg, number)
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None


def _save_diagnosis(root: Path, cfg: dict, number: int, diagnosis: dict):
    path = _diag_path(root, cfg, number)
    path.parent.mkdir(parents=True, exist_ok=True)
    diagnosis["updated_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    path.write_text(json.dumps(diagnosis, indent=2), encoding="utf-8")


def _gh_text(r: subprocess.CompletedProcess) -> str:
    """gh 2.4 writes errors to stdout; newer versions use stderr."""
    return (r.stderr or "") + (r.stdout or "")


def _update_branch_unsupported(r: subprocess.CompletedProcess) -> bool:
    return r.returncode != 0 and "unknown command" in _gh_text(r).lower()


def _try_update_branch(root: Path, number: int) -> tuple[bool, str]:
    if not shutil.which("gh"):
        return False, "gh CLI not found on the hub machine"
    try:
        r = _gh(root, "pr", "update-branch", str(number), timeout=60)
        if _update_branch_unsupported(r):
            # gh < 2.56 — same operation via REST
            r = _gh(root, "api", "-X", "PUT",
                    f"repos/:owner/:repo/pulls/{number}/update-branch", timeout=60)
    except subprocess.TimeoutExpired:
        return False, "gh pr update-branch timed out"
    invalidate_cache()
    if r.returncode != 0:
        return False, _gh_text(r).strip()[:300]
    return True, f"PR #{number} branch updated — checks re-running"


def update_pr_branch(root: Path, number: int) -> tuple[bool, str]:
    """Merge base into PR branch (legacy one-liner; prefer remediate_pr)."""
    return _try_update_branch(root, number)


def _failed_ci_details(root: Path, branch: str, max_lines: int = 80) -> dict:
    """Latest failed workflow run log tail for this branch."""
    out = {"failed_checks": [], "log_tail": "", "run_url": None}
    if not shutil.which("gh"):
        return out
    try:
        r = _gh(root, "run", "list", "--branch", branch, "--limit", "8",
                "--json", "databaseId,conclusion,name,displayTitle,url,workflowName",
                timeout=45)
    except (subprocess.TimeoutExpired, OSError):
        return out
    if r.returncode != 0:
        out["log_tail"] = (r.stderr or r.stdout or "")[:500]
        return out
    try:
        runs = json.loads(r.stdout or "[]")
    except json.JSONDecodeError:
        return out
    failed = [x for x in runs if (x.get("conclusion") or "").lower() == "failure"]
    if not failed:
        return out
    run = failed[0]
    out["failed_checks"] = [{
        "name": run.get("name") or run.get("displayTitle"),
        "workflow": run.get("workflowName"),
    }]
    out["run_url"] = run.get("url")
    try:
        lr = _gh(root, "run", "view", str(run["databaseId"]), "--log-failed",
                 timeout=120)
        log = (lr.stdout or lr.stderr or "")
        lines = log.splitlines()
        out["log_tail"] = "\n".join(lines[-max_lines:])
    except (subprocess.TimeoutExpired, OSError) as e:
        out["log_tail"] = f"(could not fetch log: {e})"
    return out


def _probe_merge_conflicts(root: Path, branch: str, base: str = "main") -> dict:
    """Try merging origin/base into the PR branch; report conflict files."""
    result = {"files": [], "excerpt": "", "merged_clean": False, "error": None}
    probe = f"_pr_probe_{uuid.uuid4().hex[:8]}"
    wt = Path(tempfile.mkdtemp(prefix="pr-probe-"))
    try:
        fr = _git(root, "fetch", "origin", base, branch, timeout=120)
        if fr.returncode != 0:
            result["error"] = fr.stderr.strip()[:300]
            return result
        ar = _git(root, "worktree", "add", "-B", probe, str(wt),
                  f"origin/{branch}", timeout=60)
        if ar.returncode != 0:
            result["error"] = ar.stderr.strip()[:300]
            return result
        mr = _git(wt, "merge", f"origin/{base}", "--no-commit", "--no-ff",
                  timeout=60)
        if mr.returncode == 0:
            result["merged_clean"] = True
            _git(wt, "merge", "--abort")
            return result
        files = [l.strip() for l in _git(wt, "diff", "--name-only",
                                          "--diff-filter=U").stdout.splitlines()
                 if l.strip()]
        excerpt = _git(wt, "diff").stdout
        if not excerpt:
            excerpt = mr.stderr + "\n" + mr.stdout
        result["files"] = files
        result["excerpt"] = excerpt[-4000:]
        _git(wt, "merge", "--abort")
        return result
    except subprocess.TimeoutExpired:
        result["error"] = "merge probe timed out"
        return result
    finally:
        _git(root, "worktree", "remove", "--force", str(wt))
        _git(root, "branch", "-D", probe)


def _local_test_tail(root: Path, cfg: dict, branch: str) -> str:
    """Run the test suite on the PR branch; return output tail (best-effort)."""
    from ..radar.act import default_test_cmd, run_tests

    wt = Path(tempfile.mkdtemp(prefix="pr-test-"))
    probe = f"_pr_test_{uuid.uuid4().hex[:8]}"
    try:
        fr = _git(root, "fetch", "origin", branch, timeout=120)
        if fr.returncode != 0:
            return ""
        ar = _git(root, "worktree", "add", "-B", probe, str(wt),
                  f"origin/{branch}", timeout=60)
        if ar.returncode != 0:
            return ""
        passed, output = run_tests(wt, cfg)
        if passed:
            return ""
        return output[-3000:]
    except (subprocess.TimeoutExpired, OSError):
        return ""
    finally:
        _git(root, "worktree", "remove", "--force", str(wt))
        _git(root, "branch", "-D", probe)


def _pr_worktree(root: Path, ticket_id: str | None, number: int) -> Path:
    if ticket_id:
        from ..radar.act import worktree_path
        return worktree_path(root, ticket_id)
    return Path.home() / ".cache" / "repo-scan" / "worktrees" / f"{root.name}-pr-{number}"


def _ensure_pr_worktree(root: Path, wt: Path, branch: str) -> tuple[bool, str]:
    """Checkout the latest origin/branch in an isolated worktree."""
    fr = _git(root, "fetch", "origin", branch, timeout=120)
    if fr.returncode != 0:
        return False, fr.stderr.strip()[:200]
    ref = f"origin/{branch}"
    if (wt / ".git").exists():
        _git(wt, "fetch", "origin", branch, timeout=120)
        rr = _git(wt, "reset", "--hard", ref)
        if rr.returncode != 0:
            return False, rr.stderr.strip()[:200]
        return True, f"worktree {wt.name} reset to {ref}"
    wt.parent.mkdir(parents=True, exist_ok=True)
    safe = branch.replace("/", "_")
    ar = _git(root, "worktree", "add", "-B", safe, str(wt), ref, timeout=60)
    if ar.returncode != 0:
        return False, ar.stderr.strip()[:200]
    return True, f"worktree {wt.name} on {ref}"


def _agent_remediate_pr(root: Path, cfg: dict, number: int, ticket_id: str,
                        branch: str, base: str, diagnosis: dict):
    """Background: merge base if needed, agent-fix, test, commit, push."""
    from ..radar.act import default_test_cmd, run_tests
    from ..radar.llm import LLMError, complete
    from ..tickets import append_ticket_note
    from .state import append_event

    wt = _pr_worktree(root, ticket_id, number)
    timeout = int(cfg.get("act_timeout", 1800))
    test_cmd = cfg.get("test_cmd") or default_test_cmd(root) or "python3 -m pytest -q"
    kind = diagnosis.get("kind")
    notes: list[str] = []

    try:
        ok_wt, msg = _ensure_pr_worktree(root, wt, branch)
        if not ok_wt:
            append_event(root, cfg, "run", f"PR #{number} remediate failed: {msg}")
            return
        notes.append(msg)

        if kind == "conflict" or diagnosis.get("mergeable") == "CONFLICTING":
            mr = _git(wt, "merge", f"origin/{base}", "--no-commit", timeout=120)
            if mr.returncode != 0:
                files = diagnosis.get("conflict_files") or []
                excerpt = diagnosis.get("excerpt") or mr.stderr
                try:
                    complete(CONFLICT_PROMPT.format(
                        base=base, files="\n".join(f"- {f}" for f in files) or "(unknown)",
                        excerpt=excerpt[:8000],
                    ), cfg, timeout=timeout, cwd=str(wt), role="act_fix", root=root)
                    notes.append("agent resolved merge conflicts")
                except LLMError as e:
                    append_event(root, cfg, "run",
                                 f"PR #{number} conflict fix failed: {e}")
                    append_ticket_note(root, cfg, ticket_id,
                                       f"PR #{number} conflict fix failed: {e}")
                    return

        if kind == "tests":
            ci_log = diagnosis.get("log_tail") or "(no CI log captured)"
            local_log = _local_test_tail(root, cfg, branch)
            try:
                complete(CI_FIX_PROMPT.format(
                    test_cmd=test_cmd, ci_log=ci_log[:8000],
                    local_log=local_log[:4000] or "(tests passed locally or not run)",
                ), cfg, timeout=timeout, cwd=str(wt), role="act_fix", root=root)
                notes.append("agent applied CI failure fix")
            except LLMError as e:
                append_event(root, cfg, "run", f"PR #{number} CI fix failed: {e}")
                append_ticket_note(root, cfg, ticket_id,
                                   f"PR #{number} CI fix failed: {e}")
                return

        rounds = int(cfg.get("act_fix_rounds", 2))
        passed, output = run_tests(wt, cfg)
        attempt = 0
        from ..radar.act import FIX_PROMPT
        while not passed and attempt < rounds:
            attempt += 1
            try:
                complete(FIX_PROMPT.format(test_cmd=test_cmd, output=output),
                         cfg, timeout=timeout, cwd=str(wt), role="act_fix", root=root)
            except LLMError as e:
                append_event(root, cfg, "run",
                             f"PR #{number} test fix round {attempt} failed: {e}")
                break
            passed, output = run_tests(wt, cfg)

        status = _git(wt, "status", "--porcelain").stdout.strip()
        if not status:
            msg = "no local changes after remediate"
            append_event(root, cfg, "run", f"PR #{number}: {msg}")
            append_ticket_note(root, cfg, ticket_id, f"PR #{number}: {msg}")
            return

        if not passed:
            append_event(root, cfg, "run",
                         f"PR #{number} tests still failing after remediate")
            append_ticket_note(root, cfg, ticket_id,
                               f"PR #{number} tests still failing — branch kept")
            return

        _git(wt, "add", "-A")
        cm = _git(wt, "commit", "-m",
                  f"fix: remediate PR #{number} ({kind or 'update'})", timeout=120)
        if cm.returncode != 0:
            append_event(root, cfg, "run",
                         f"PR #{number} commit failed: {cm.stderr[:200]}")
            return
        commit = _git(wt, "rev-parse", "--short", "HEAD").stdout.strip()
        pr = _git(wt, "push", "origin", f"HEAD:{branch}", timeout=120)
        if pr.returncode != 0:
            append_event(root, cfg, "run",
                         f"PR #{number} push failed: {pr.stderr[:200]}")
            append_ticket_note(root, cfg, ticket_id,
                               f"PR #{number} fix committed locally ({commit}) but push failed")
            return

        invalidate_cache()
        summary = f"PR #{number} remediated ({commit}) — {'; '.join(notes)}"
        append_event(root, cfg, "run", summary)
        append_ticket_note(root, cfg, ticket_id, summary)
        diagnosis["fix_status"] = "pushed"
        diagnosis["fix_commit"] = commit
        _save_diagnosis(root, cfg, number, diagnosis)
    except Exception as e:
        append_event(root, cfg, "run", f"PR #{number} remediate error: {e}")
    finally:
        with _CACHE_LOCK:
            _REMEDIATE_THREADS.pop(number, None)


def _spawn_pr_remediate(root: Path, cfg: dict, number: int, ticket_id: str,
                        branch: str, base: str, diagnosis: dict):
    with _CACHE_LOCK:
        if number in _REMEDIATE_THREADS and _REMEDIATE_THREADS[number].is_alive():
            return
        t = threading.Thread(
            target=_agent_remediate_pr,
            args=(root, cfg, number, ticket_id, branch, base, diagnosis),
            name=f"pr-remediate-{number}", daemon=True)
        _REMEDIATE_THREADS[number] = t
        t.start()


def remediate_pr(root: Path, cfg: dict, number: int) -> dict:
    """Update branch, diagnose conflicts/CI failures, optionally agent-fix.

    Returns {ok, message, diagnosis, fix_started, actions}."""
    from .state import append_event

    pr = fetch_pr(root, number)
    if not pr:
        return {"ok": False, "message": f"PR #{number} not found",
                "diagnosis": {}, "fix_started": False, "actions": []}

    branch = pr["branch"]
    base = "main"  # gh list doesn't always carry base; fetch single pr for it
    try:
        r = _gh(root, "pr", "view", str(number), "--json", "baseRefName")
        if r.returncode == 0:
            base = json.loads(r.stdout or "{}").get("baseRefName", base)
    except (subprocess.TimeoutExpired, OSError, json.JSONDecodeError):
        pass

    actions: list[str] = []
    mergeable = pr["mergeable"]
    checks = pr["checks"]
    diagnosis: dict = {
        "number": number,
        "branch": branch,
        "base": base,
        "mergeable": mergeable,
        "checks": checks,
        "kind": None,
    }

    needs_work = (mergeable in ("CONFLICTING", "BEHIND", "UNKNOWN")
                  or checks == "failing")
    if needs_work:
        ok_up, msg_up = _try_update_branch(root, number)
        actions.append(msg_up if ok_up else f"update failed: {msg_up}")
        pr = fetch_pr(root, number) or pr
        mergeable = pr["mergeable"]
        checks = pr["checks"]
        diagnosis["mergeable"] = mergeable
        diagnosis["checks"] = checks

    conflict = mergeable == "CONFLICTING"
    tests_bad = checks == "failing"

    if conflict:
        probe = _probe_merge_conflicts(root, branch, base)
        diagnosis.update(kind="conflict",
                           conflict_files=probe.get("files", []),
                           excerpt=(probe.get("excerpt") or "")[:4000])
        if probe.get("merged_clean"):
            diagnosis["kind"] = None
            diagnosis["mergeable"] = "MERGEABLE"
            conflict = False
        if probe.get("error"):
            diagnosis["probe_error"] = probe["error"]

    if tests_bad and not conflict:
        ci = _failed_ci_details(root, branch)
        diagnosis.update(kind="tests",
                         failed_checks=ci.get("failed_checks", []),
                         log_tail=(ci.get("log_tail") or "")[:6000],
                         run_url=ci.get("run_url"))
        # local test run happens inside the background agent (not here — it
        # would block the dashboard for minutes on a real suite)

    _save_diagnosis(root, cfg, number, diagnosis)
    append_event(root, cfg, "run",
                 f"PR #{number} diagnosed: {diagnosis.get('kind') or 'clear'} "
                 f"({mergeable}, checks {checks})")

    fix_started = False
    ticket_id = pr.get("ticket")
    if (cfg.get("pr_auto_remediate", True) and ticket_id
            and diagnosis.get("kind") and cfg.get("act_enabled")):
        _spawn_pr_remediate(root, cfg, number, ticket_id, branch, base, diagnosis)
        fix_started = True
        actions.append("agent fix started — watch the feed")

    parts = list(actions)
    if diagnosis.get("kind") == "conflict":
        files = diagnosis.get("conflict_files") or []
        parts.append(f"conflicts: {', '.join(files[:4])}"
                     + ("…" if len(files) > 4 else ""))
    elif diagnosis.get("kind") == "tests":
        names = [c.get("name") for c in diagnosis.get("failed_checks") or []
                 if c.get("name")]
        parts.append("CI failing" + (f" ({names[0]})" if names else ""))
    elif not needs_work:
        parts.append("nothing to fix")

    message = " · ".join(parts) if parts else "done"
    diagnosis["status_note"] = message
    diagnosis["fix_started"] = fix_started
    # `ok` = PR is merge-ready, not "HTTP succeeded" — always return 200
    # with diagnosis so the dashboard can show what happened.
    merge_ready = (not conflict and checks != "failing"
                   and diagnosis.get("kind") is None)
    return {"ok": merge_ready, "message": message, "diagnosis": diagnosis,
            "fix_started": fix_started, "actions": actions}


def merge_pr(root: Path, cfg: dict, number: int) -> tuple[bool, str]:
    """Squash-merge a PR, delete its branch, and sync the local checkout."""
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
    sync = sync_local(root)
    return True, f"PR #{number} squash-merged, branch deleted — {sync}"


def sync_local(root: Path) -> str:
    """Fetch origin and fast-forward the current branch."""
    try:
        r = _git(root, "fetch", "origin", timeout=120)
        if r.returncode != 0:
            return f"fetch failed: {r.stderr.strip()[:120]}"
        branch = _git(root, "rev-parse", "--abbrev-ref", "HEAD").stdout.strip()
        r = _git(root, "pull", "--ff-only", "origin", branch)
        if r.returncode != 0:
            return (f"fetched, but {branch} not fast-forwarded "
                    f"({r.stderr.strip()[:120]})")
        return f"local {branch} synced with origin"
    except (subprocess.TimeoutExpired, OSError) as e:
        return f"sync skipped ({e})"


def _note_merged(root: Path, cfg: dict, number: int):
    """Close the loop in the vault: rescan, verify fingerprint, note + done."""
    from ..tickets import load_tickets, record_merge_verification
    from .state import append_event
    with _CACHE_LOCK:
        cached = next((p for p in _CACHE["prs"] if p["number"] == number), None)
    ticket_id = cached["ticket"] if cached else None
    append_event(root, cfg, "run", f"PR #{number} merged from dashboard"
                 + (f" ({ticket_id})" if ticket_id else ""))
    if ticket_id and any(t["id"] == ticket_id for t in load_tickets(root, cfg)):
        record_merge_verification(root, cfg, ticket_id, number)
