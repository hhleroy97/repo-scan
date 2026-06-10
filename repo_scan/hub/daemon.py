"""The resident loop runner.

One tick (user-facing phases):
1. Resume any waiting run whose gate decision arrived (checkpoints make this
   cheap — completed LLM stages skip). Act runs resume on threads.
2. If the scan is stale and nothing is mid-flight, rescan (proposes tickets).
3. Fan out act runs (approved specs) into isolated worktrees, up to
   max_parallel_acts at once — each on its own thread, each on its own
   radar/<ticket> branch, so agents never collide.
4. Start a research loop for the next approved ticket (one at a time —
   loops share the vault).

Tick internals also include a mid-flight guard (foreign-owned queued/running
runs block new work) and a daily budget gate (caps block starting new work
only; resumes and in-flight runs continue).

All state is file-backed, so the daemon can die and restart at any point;
the dashboard and CLI keep working against the same files either way.
"""

import json
import threading
import time
from pathlib import Path

from ..utils import header, info, now_date, ok, warn
from .notify import notify
from .state import (active_runs, append_event, create_run, load_meta,
                    load_runs, peek_decision, save_meta, update_run)

# run id -> thread, for in-flight runs (acts AND loops) owned by this process
_run_threads: dict[str, threading.Thread] = {}

# parallel acts must not race each other (or a human) on the git index
_VAULT_LOCK = threading.Lock()


def _pending_gate_for(root: Path, cfg: dict, problem: str) -> str | None:
    """Which gate (if any) is currently paused for this problem."""
    pending = root / cfg["docs_dir"] / "research" / "pending"
    for path in sorted(pending.glob("*.json")) if pending.exists() else []:
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        if str(data.get("payload", {}).get("problem", "")) == problem:
            return data.get("gate")
    return None


def _dashboard_url(cfg: dict) -> str | None:
    # explicit override wins — needed when a proxy (e.g. `tailscale serve`)
    # fronts the hub at a different scheme/host than the bind address
    if cfg.get("dashboard_url"):
        return str(cfg["dashboard_url"])
    host = cfg.get("serve_host")
    port = cfg.get("serve_port", 8800)
    return f"http://{host}:{port}/" if host else None


def _run_loop(root: Path, cfg: dict, run: dict) -> int:
    """Execute/resume one loop and translate the outcome into run state."""
    from ..radar.pipeline import cmd_loop
    from ..tickets import append_ticket_note, set_ticket_status

    update_run(root, cfg, run["id"], "running")
    try:
        rc = cmd_loop(root, cfg, run["problem"])
    finally:
        commit_vault(root, cfg,
                     f"vault: loop artifacts — {run.get('ticket') or run['problem'][:60]}")

    if rc == 0:
        update_run(root, cfg, run["id"], "done")
        append_event(root, cfg, "run", f"loop done — spec approved ({run.get('ticket')})")
        if run.get("ticket"):
            # the spec wikilink is what makes this ticket an act candidate;
            # resolved by problem slug — parallel loops finish out of order
            from ..radar.pipeline import spec_for_problem
            set_ticket_status(root, cfg, run["ticket"], "in-progress")
            spec = spec_for_problem(root, cfg, run["problem"])
            link = f": [[{spec}]]" if spec else ""
            append_ticket_note(root, cfg, run["ticket"],
                               f"radar spec approved (daemon run){link} — status moved to in-progress")
        notify(cfg, "RADAR: spec approved",
               f"Loop finished for: {run['problem'][:120]}",
               tags=["white_check_mark"], click=_dashboard_url(cfg))
        return rc

    if rc == 2:
        gate_name = _pending_gate_for(root, cfg, run["problem"])
        if gate_name:
            update_run(root, cfg, run["id"], "waiting-on-gate", gate=gate_name)
            notify(cfg, f"RADAR: gate {gate_name} needs you",
                   run["problem"][:160], priority="high",
                   tags=["raised_hand"], click=_dashboard_url(cfg))
        else:
            # gate consumed a reject decision — loop is over
            update_run(root, cfg, run["id"], "stopped")
            notify(cfg, "RADAR: loop rejected", run["problem"][:160],
                   tags=["x"], click=_dashboard_url(cfg))
        return rc

    update_run(root, cfg, run["id"], "failed")
    notify(cfg, "RADAR: loop failed", run["problem"][:160],
           priority="high", tags=["rotating_light"], click=_dashboard_url(cfg))
    return rc


def _run_act(root: Path, cfg: dict, run: dict) -> int:
    """Execute/resume one act run and translate the outcome into run state."""
    from ..radar.act import cmd_act

    update_run(root, cfg, run["id"], "running")
    try:
        rc = cmd_act(root, cfg, ticket_id=run.get("ticket"), worktree=True)
    finally:
        commit_vault(root, cfg,
                     f"vault: act trail — {run.get('ticket') or run['problem'][:60]}")

    if rc == 0:
        update_run(root, cfg, run["id"], "done")
        append_event(root, cfg, "run",
                     f"implementation committed on radar/{run.get('ticket')} — review and merge")
        notify(cfg, "RADAR: implementation committed",
               f"{run.get('ticket')}: review the branch and merge.",
               tags=["white_check_mark"], click=_dashboard_url(cfg))
        return rc
    if rc == 2:
        gate_name = _pending_gate_for(root, cfg, run["problem"])
        if gate_name:
            update_run(root, cfg, run["id"], "waiting-on-gate", gate=gate_name)
            notify(cfg, f"RADAR: gate {gate_name} needs you",
                   run["problem"][:160], priority="high",
                   tags=["raised_hand"], click=_dashboard_url(cfg))
        else:
            update_run(root, cfg, run["id"], "stopped")
            notify(cfg, "RADAR: act run stopped",
                   f"{run.get('ticket')}: rejected or tests failing — branch kept for review.",
                   priority="high", tags=["x"], click=_dashboard_url(cfg))
        return rc
    update_run(root, cfg, run["id"], "failed")
    notify(cfg, "RADAR: act run failed", run["problem"][:160],
           priority="high", tags=["rotating_light"], click=_dashboard_url(cfg))
    return rc


def _spawn(root: Path, cfg: dict, run: dict, runner, parallel: bool) -> None:
    """Run a loop/act either inline (tests, single-slot configs) or on a
    thread — threaded runs never block the scheduler tick."""
    if not parallel:
        runner(root, cfg, run)
        return
    t = threading.Thread(target=runner, args=(root, cfg, run),
                         name=f"{run.get('kind', 'run')}-{run['id']}", daemon=True)
    _run_threads[run["id"]] = t
    t.start()


def commit_vault(root: Path, cfg: dict, message: str) -> bool:
    """Auto-commit vault churn so agentic history is never lost.

    Loops and scans write artifacts (specs, analyses, sources, tickets,
    logs) continuously, but nothing committed them — humans periodically
    rescued them in catch-up commits. The daemon now commits docs/ after
    every run and scan, pathspec-scoped so a human's staged code work is
    never swept in. Push is best-effort (fast-forward sync first); offline
    just means the commits accumulate locally. Disable with
    "vault_autocommit": false.
    """
    import subprocess
    if not cfg.get("vault_autocommit", True):
        return False
    docs = cfg["docs_dir"]

    def _git(*args: str, timeout: int = 60) -> subprocess.CompletedProcess:
        return subprocess.run(["git", *args], cwd=root, capture_output=True,
                              text=True, timeout=timeout)
    try:
        with _VAULT_LOCK:
            return _commit_vault_locked(root, cfg, message, _git)
    except (subprocess.TimeoutExpired, OSError) as e:
        warn(f"vault commit skipped: {e}")
        return False


def _commit_vault_locked(root: Path, cfg: dict, message: str, _git) -> bool:
    docs = cfg["docs_dir"]
    _git("add", "-A", "--", docs)
    if _git("diff", "--cached", "--quiet", "--", docs).returncode == 0:
        return False  # nothing new in the vault
    # pathspec commit: only docs/ lands, whatever else is in the index
    r = _git("commit", "-m", message, "--", docs)
    if r.returncode != 0:
        warn(f"vault commit failed: {r.stderr.strip()[:120]}")
        return False
    append_event(root, cfg, "run", f"vault committed: {message[:80]}")
    from .prs import sync_local
    sync_local(root)  # ff first so the push isn't rejected
    r = _git("push", "origin", "HEAD", timeout=120)
    if r.returncode != 0:
        info(f"vault commit kept locally (push: {r.stderr.strip()[:80]})")
    return True


def over_budget(root: Path, cfg: dict) -> str | None:
    """Governance: daily spend caps. Returns the reason if a cap is hit.

        "budget_daily_tokens": 2000000,   # in+out tokens per day (usage ledger)
        "max_acts_per_day": 6             # act runs started per day

    Caps block STARTING new work; runs already mid-flight (paused at a gate,
    resuming from checkpoints) finish normally so spent tokens aren't wasted.
    """
    cap_tokens = int(cfg.get("budget_daily_tokens", 0))
    if cap_tokens:
        from ..radar.llm import usage_summary
        today = usage_summary(root, cfg).get("today", {})
        used = int(today.get("input_tokens", 0)) + int(today.get("output_tokens", 0))
        if used >= cap_tokens:
            return f"daily token budget reached ({used:,}/{cap_tokens:,})"
    cap_acts = int(cfg.get("max_acts_per_day", 0))
    if cap_acts:
        started = [r for r in load_runs(root, cfg)
                   if r.get("kind") == "act"
                   and str(r.get("created_at", "")).startswith(now_date())]
        if len(started) >= cap_acts:
            return f"daily act cap reached ({len(started)}/{cap_acts})"
    return None


def _prune_finished_threads() -> None:
    """Drop dead thread handles from the process-local run registry."""
    for rid in [r for r, t in _run_threads.items() if not t.is_alive()]:
        del _run_threads[rid]


def _resume_gate_waiting_runs(
    root: Path,
    cfg: dict,
    active: list[dict],
    busy: set[str],
    parallel_acts: bool,
    parallel_loops: bool,
) -> list[str]:
    """Resume paused runs whose gate decisions arrived."""
    actions: list[str] = []
    for run in active:
        if run["status"] != "waiting-on-gate" or run["id"] in busy:
            continue
        if run.get("gate") and peek_decision(root, cfg, run["gate"], run["problem"]):
            info(f"decision arrived for gate {run['gate']} — resuming run {run['id']}")
            if run.get("kind") == "act":
                _spawn(root, cfg, run, _run_act, parallel_acts)
            else:
                _spawn(root, cfg, run, _run_loop, parallel_loops)
            actions.append(f"resumed:{run['id']}")
    return actions


def _tick_midflight_guard(active: list[dict], busy: set[str], actions: list[str]) -> list[str] | None:
    """Return early when foreign-owned queued/running runs are mid-flight."""
    mid_flight = [r for r in active
                  if r["status"] in ("queued", "running") and r["id"] not in busy]
    if mid_flight:
        return actions
    return None


def _maybe_run_scheduled_scan(root: Path, cfg: dict, actions: list[str]) -> list[str] | None:
    """Run a scheduled scan when idle; return immediately (skip budget/act/loop)."""
    if _run_threads:
        return None
    meta = load_meta(root, cfg)
    scan_interval = float(cfg.get("daemon_scan_hours", 6)) * 3600
    if time.time() - float(meta.get("last_scan", 0)) < scan_interval:
        return None
    from ..scanner import scan
    info("scheduled scan starting")
    append_event(root, cfg, "scan", "scheduled scan started")
    try:
        scan(root, quiet=True)
        actions.append("scanned")
    except Exception as e:
        warn(f"scheduled scan failed: {e}")
        actions.append("scan-failed")
    meta["last_scan"] = time.time()
    save_meta(root, cfg, meta)
    commit_vault(root, cfg, "vault: scheduled scan")
    from ..tickets import load_tickets
    proposed = [t for t in load_tickets(root, cfg) if t["status"] == "proposed"]
    if proposed:
        notify(cfg, f"repo-scan: {len(proposed)} ticket(s) awaiting review",
               "; ".join(t["title"][:60] for t in proposed[:3]),
               tags=["ticket"], click=_dashboard_url(cfg))
    return actions


def _apply_budget_gate(root: Path, cfg: dict, actions: list[str]) -> list[str] | None:
    """Block starting new work when daily budgets are exhausted; notify once/day."""
    budget_reason = over_budget(root, cfg)
    if not budget_reason:
        return None
    meta = load_meta(root, cfg)
    if meta.get("budget_notified") != now_date():
        warn(f"budget: {budget_reason} — not starting new runs")
        append_event(root, cfg, "run", f"budget: {budget_reason}")
        notify(cfg, "RADAR: daily budget reached", budget_reason,
               tags=["money_with_wings"], click=_dashboard_url(cfg))
        meta["budget_notified"] = now_date()
        save_meta(root, cfg, meta)
    return actions


def _act_threads_alive(root: Path, cfg: dict) -> int:
    """Count act runs owned by live threads in this process."""
    ids = {r["id"] for r in active_runs(root, cfg) if r.get("kind") == "act"}
    return len(ids & set(_run_threads))


def _fan_out_acts(
    root: Path,
    cfg: dict,
    max_acts: int,
    parallel_acts: bool,
    actions: list[str],
) -> list[str] | None:
    """Start act runs up to max_parallel_acts; return early when actions is non-empty."""
    if not cfg.get("act_enabled"):
        return None
    from ..radar.act import act_problem, find_act_tickets
    covered = {r.get("ticket") for r in active_runs(root, cfg)}
    slots = max_acts - _act_threads_alive(root, cfg)
    for ticket, spec_stem in find_act_tickets(root, cfg):
        if slots <= 0:
            break
        if ticket["id"] in covered:
            continue
        problem = act_problem(ticket["id"], spec_stem)
        run = create_run(root, cfg, problem, ticket=ticket["id"], kind="act")
        info(f"starting act run {run['id']} for ticket {ticket['id']}")
        _spawn(root, cfg, run, _run_act, parallel_acts)
        actions.append(f"act-started:{run['id']}")
        slots -= 1
    if actions:
        return actions
    return None


def _loop_slots_available(root: Path, cfg: dict, max_loops: int) -> int:
    """Non-act queued/running runs consume loop parallelism slots."""
    in_flight = len([r for r in active_runs(root, cfg)
                     if r.get("kind") != "act"
                     and r["status"] in ("queued", "running")])
    return max_loops - in_flight


def _fan_out_loops(
    root: Path,
    cfg: dict,
    max_loops: int,
    parallel_loops: bool,
    actions: list[str],
) -> list[str]:
    """Start loop runs up to max_parallel_loops for approved tickets."""
    if not cfg.get("radar_enabled"):
        return actions
    from ..radar.pipeline import ticket_problem
    from ..tickets import approved_tickets
    covered = {r.get("ticket") for r in active_runs(root, cfg)}
    slots = _loop_slots_available(root, cfg, max_loops)
    for ticket in approved_tickets(root, cfg):
        if slots <= 0:
            break
        if ticket["id"] in covered:
            continue
        problem = ticket_problem(ticket)
        run = create_run(root, cfg, problem, ticket=ticket["id"])
        info(f"starting run {run['id']} for ticket {ticket['id']}")
        _spawn(root, cfg, run, _run_loop, parallel_loops)
        actions.append(f"started:{run['id']}")
        slots -= 1
    return actions


def reclaim_orphan_runs(root: Path, cfg: dict) -> list[str]:
    """Mark queued/running runs with no owning thread as stopped.

    Called at daemon startup: if a previous process died mid-run, its run
    records would otherwise sit in "running" forever and starve the
    scheduler. Stopping them lets the normal fan-out resurrect the work —
    checkpoints (branch, worktree, completed stages) and inbox decisions
    survive, so the resume is cheap and consistent.
    """
    reclaimed = []
    for r in active_runs(root, cfg):
        if r["status"] in ("queued", "running") and r["id"] not in _run_threads:
            update_run(root, cfg, r["id"], "stopped",
                       note="reclaimed at daemon startup (owner died)")
            warn(f"reclaimed orphaned run {r['id']} ({r.get('ticket')})")
            reclaimed.append(r["id"])
    return reclaimed


def daemon_tick(root: Path, cfg: dict) -> list[str]:
    """One scheduling pass. Returns the actions taken (for logs and tests)."""
    _prune_finished_threads()

    max_acts = int(cfg.get("max_parallel_acts", 2))
    max_loops = int(cfg.get("max_parallel_loops", 2))
    parallel_acts = max_acts > 1
    parallel_loops = max_loops > 1
    actions: list[str] = []
    active = active_runs(root, cfg)
    busy = set(_run_threads)

    resumed = _resume_gate_waiting_runs(
        root, cfg, active, busy, parallel_acts, parallel_loops)
    actions.extend(resumed)
    if resumed:
        active = active_runs(root, cfg)
        busy = set(_run_threads)

    early = _tick_midflight_guard(active, busy, actions)
    if early is not None:
        return early

    early = _maybe_run_scheduled_scan(root, cfg, actions)
    if early is not None:
        return early

    early = _apply_budget_gate(root, cfg, actions)
    if early is not None:
        return early

    early = _fan_out_acts(root, cfg, max_acts, parallel_acts, actions)
    if early is not None:
        return early

    return _fan_out_loops(root, cfg, max_loops, parallel_loops, actions)


def cmd_daemon(root: Path, cfg: dict, poll_seconds: int | None = None) -> int:
    header("radar daemon")
    reclaim_orphan_runs(root, cfg)
    poll = int(poll_seconds or cfg.get("daemon_poll_seconds", 20))
    info(f"polling every {poll}s — scans every {cfg.get('daemon_scan_hours', 6)}h "
         f"(state: {cfg['docs_dir']}/.radar/)")
    try:
        while True:
            try:
                for action in daemon_tick(root, cfg):
                    ok(f"tick: {action}")
            except Exception as e:  # a bad tick must never kill the scheduler
                import traceback
                warn(f"tick failed: {e}")
                traceback.print_exc()
            time.sleep(poll)
    except KeyboardInterrupt:
        info("daemon stopped")
        return 0
