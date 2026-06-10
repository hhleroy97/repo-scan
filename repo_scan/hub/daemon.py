"""The resident loop runner.

One tick:
1. Resume any waiting run whose gate decision arrived (checkpoints make this
   cheap — completed LLM stages skip). Act runs resume on threads.
2. If the scan is stale and nothing is mid-flight, rescan (proposes tickets).
3. Fan out act runs (approved specs) into isolated worktrees, up to
   max_parallel_acts at once — each on its own thread, each on its own
   radar/<ticket> branch, so agents never collide.
4. Start a research loop for the next approved ticket (one at a time —
   loops share the vault).

All state is file-backed, so the daemon can die and restart at any point;
the dashboard and CLI keep working against the same files either way.
"""

import json
import threading
import time
from pathlib import Path

from ..utils import header, info, ok, warn
from .notify import notify
from .state import (active_runs, create_run, load_meta, peek_decision,
                    save_meta, update_run)

# run id -> thread, for in-flight act runs owned by this process
_act_threads: dict[str, threading.Thread] = {}


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
    rc = cmd_loop(root, cfg, run["problem"])

    if rc == 0:
        update_run(root, cfg, run["id"], "done")
        if run.get("ticket"):
            set_ticket_status(root, cfg, run["ticket"], "in-progress")
            append_ticket_note(root, cfg, run["ticket"],
                               "radar spec approved (daemon run) — status moved to in-progress")
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
    rc = cmd_act(root, cfg, ticket_id=run.get("ticket"), worktree=True)

    if rc == 0:
        update_run(root, cfg, run["id"], "done")
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


def _spawn_act(root: Path, cfg: dict, run: dict, parallel: bool) -> None:
    """Run an act either inline (tests, single-slot configs) or on a thread."""
    if not parallel:
        _run_act(root, cfg, run)
        return
    t = threading.Thread(target=_run_act, args=(root, cfg, run),
                         name=f"act-{run['id']}", daemon=True)
    _act_threads[run["id"]] = t
    t.start()


def daemon_tick(root: Path, cfg: dict) -> list[str]:
    """One scheduling pass. Returns the actions taken (for logs and tests)."""
    actions: list[str] = []
    for rid in [r for r, t in _act_threads.items() if not t.is_alive()]:
        del _act_threads[rid]

    max_acts = int(cfg.get("max_parallel_acts", 2))
    parallel = max_acts > 1
    active = active_runs(root, cfg)
    busy = {r["id"] for r in _act_threads}  # threads this process is running

    # 1 — resume paused runs whose decisions arrived
    for run in active:
        if run["status"] != "waiting-on-gate" or run["id"] in busy:
            continue
        if run.get("gate") and peek_decision(root, cfg, run["gate"], run["problem"]):
            info(f"decision arrived for gate {run['gate']} — resuming run {run['id']}")
            if run.get("kind") == "act":
                _spawn_act(root, cfg, run, parallel)
            else:
                _run_loop(root, cfg, run)
            actions.append(f"resumed:{run['id']}")
    if actions:
        active = active_runs(root, cfg)
        busy = {r["id"] for r in _act_threads}

    mid_flight = [r for r in active
                  if r["status"] in ("queued", "running") and r["id"] not in busy]
    if mid_flight:
        # another tick/process owns these; leave them alone
        return actions

    # 2 — scheduled scan (skip while anything is actively running)
    if not _act_threads:
        meta = load_meta(root, cfg)
        scan_interval = float(cfg.get("daemon_scan_hours", 6)) * 3600
        if time.time() - float(meta.get("last_scan", 0)) >= scan_interval:
            from ..scanner import scan
            info("scheduled scan starting")
            try:
                scan(root, quiet=True)
                actions.append("scanned")
            except Exception as e:
                warn(f"scheduled scan failed: {e}")
                actions.append("scan-failed")
            meta["last_scan"] = time.time()
            save_meta(root, cfg, meta)
            from ..tickets import load_tickets
            proposed = [t for t in load_tickets(root, cfg) if t["status"] == "proposed"]
            if proposed:
                notify(cfg, f"repo-scan: {len(proposed)} ticket(s) awaiting review",
                       "; ".join(t["title"][:60] for t in proposed[:3]),
                       tags=["ticket"], click=_dashboard_url(cfg))
            return actions

    # 3 — fan out acts on approved specs, up to max_parallel_acts
    if cfg.get("act_enabled"):
        from ..radar.act import act_problem, find_act_tickets
        covered = {r.get("ticket") for r in active_runs(root, cfg)}
        slots = max_acts - len(_act_threads)
        for ticket, spec_stem in find_act_tickets(root, cfg):
            if slots <= 0:
                break
            if ticket["id"] in covered:
                continue
            problem = act_problem(ticket["id"], spec_stem)
            run = create_run(root, cfg, problem, ticket=ticket["id"], kind="act")
            info(f"starting act run {run['id']} for ticket {ticket['id']}")
            _spawn_act(root, cfg, run, parallel)
            actions.append(f"act-started:{run['id']}")
            slots -= 1
        if actions:
            return actions

    # 4 — start a research loop for the next approved ticket (one at a time)
    loops_active = [r for r in active_runs(root, cfg) if r.get("kind") != "act"]
    if cfg.get("radar_enabled") and not loops_active:
        from ..radar.pipeline import ticket_problem
        from ..tickets import pick_approved_ticket
        ticket = pick_approved_ticket(root, cfg)
        if ticket:
            problem = ticket_problem(ticket)
            run = create_run(root, cfg, problem, ticket=ticket["id"])
            info(f"starting run {run['id']} for ticket {ticket['id']}")
            _run_loop(root, cfg, run)
            actions.append(f"started:{run['id']}")

    return actions


def cmd_daemon(root: Path, cfg: dict, poll_seconds: int | None = None) -> int:
    header("radar daemon")
    poll = int(poll_seconds or cfg.get("daemon_poll_seconds", 20))
    info(f"polling every {poll}s — scans every {cfg.get('daemon_scan_hours', 6)}h "
         f"(state: {cfg['docs_dir']}/.radar/)")
    try:
        while True:
            for action in daemon_tick(root, cfg):
                ok(f"tick: {action}")
            time.sleep(poll)
    except KeyboardInterrupt:
        info("daemon stopped")
        return 0
