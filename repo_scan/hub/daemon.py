"""The resident loop runner.

One tick:
1. If a run is waiting on a gate and a decision has arrived in the inbox,
   resume the loop (checkpoints make this cheap — completed LLM stages skip).
2. Otherwise, if the scan is stale, rescan (which also proposes tickets).
3. Otherwise, if an approved ticket is queued and nothing is running,
   start a loop for it.

All state is file-backed, so the daemon can die and restart at any point;
the dashboard and CLI keep working against the same files either way.
"""

import json
import time
from pathlib import Path

from ..utils import header, info, ok, warn
from .notify import notify
from .state import (active_run, create_run, load_meta, peek_decision,
                    save_meta, update_run)


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
    rc = cmd_act(root, cfg, ticket_id=run.get("ticket"))

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


def daemon_tick(root: Path, cfg: dict) -> list[str]:
    """One scheduling pass. Returns the actions taken (for logs and tests)."""
    actions: list[str] = []
    run = active_run(root, cfg)

    # 1 — resume a paused run if its decision arrived
    if run and run["status"] == "waiting-on-gate":
        if run.get("gate") and peek_decision(root, cfg, run["gate"], run["problem"]):
            info(f"decision arrived for gate {run['gate']} — resuming run {run['id']}")
            if run.get("kind") == "act":
                _run_act(root, cfg, run)
            else:
                _run_loop(root, cfg, run)
            actions.append(f"resumed:{run['id']}")
        return actions  # while waiting, don't start anything else

    if run and run["status"] in ("queued", "running"):
        # a previous tick (or process) is mid-flight; leave it alone
        return actions

    # 2 — scheduled scan
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

    # 3 — act on an approved spec (finish started work before starting new)
    if cfg.get("act_enabled"):
        from ..radar.act import act_problem, find_act_ticket
        picked = find_act_ticket(root, cfg)
        if picked:
            ticket, spec_stem = picked
            problem = act_problem(ticket["id"], spec_stem)
            run = create_run(root, cfg, problem, ticket=ticket["id"])
            update_run(root, cfg, run["id"], "queued", kind="act")
            run["kind"] = "act"
            info(f"starting act run {run['id']} for ticket {ticket['id']}")
            _run_act(root, cfg, run)
            actions.append(f"act-started:{run['id']}")
            return actions

    # 4 — start a research loop for the next approved ticket
    if cfg.get("radar_enabled"):
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
