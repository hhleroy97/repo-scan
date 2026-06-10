"""Hub adapter between daemon run records and ``radar.act.cmd_act``.

Owns the act-run lifecycle for daemon-scheduled work: invoke ``cmd_act`` with
``worktree=True``, vault commit in ``finally``, map return codes to run state,
events, and notifications.

RC semantics (aligned with ``cmd_act``):
- ``ACT_RC_SUCCESS`` (0): implementation committed — run → ``done``
- ``ACT_RC_PAUSED`` (2): paused at gate or stopped/rejected — run →
  ``waiting-on-gate`` when a pending gate exists, else ``stopped``
- other: run → ``failed``

``commit_vault``, ``pending_gate_for``, and ``dashboard_url`` are injected by
the daemon wrapper so this module never imports ``daemon`` (avoids cycles).
"""

from pathlib import Path
from typing import Callable

from .notify import notify
from .state import append_event, update_run

ACT_RC_SUCCESS = 0
ACT_RC_PAUSED = 2


def run_act(
    root: Path,
    cfg: dict,
    run: dict,
    *,
    pending_gate_for: Callable[[Path, dict, str], str | None],
    dashboard_url: Callable[[dict], str | None],
    commit_vault: Callable[[Path, dict, str], bool],
) -> int:
    """Execute one act run and translate ``cmd_act`` outcome into run state."""
    from ..radar.act import cmd_act

    update_run(root, cfg, run["id"], "running")
    try:
        rc = cmd_act(root, cfg, ticket_id=run.get("ticket"), worktree=True)
    finally:
        commit_vault(
            root,
            cfg,
            f"vault: act trail — {run.get('ticket') or run['problem'][:60]}",
        )

    if rc == ACT_RC_SUCCESS:
        update_run(root, cfg, run["id"], "done")
        append_event(
            root,
            cfg,
            "run",
            f"implementation committed on radar/{run.get('ticket')} — review and merge",
        )
        notify(
            cfg,
            "RADAR: implementation committed",
            f"{run.get('ticket')}: review the branch and merge.",
            tags=["white_check_mark"],
            click=dashboard_url(cfg),
        )
        return rc

    if rc == ACT_RC_PAUSED:
        gate_name = pending_gate_for(root, cfg, run["problem"])
        if gate_name:
            update_run(root, cfg, run["id"], "waiting-on-gate", gate=gate_name)
            notify(
                cfg,
                f"RADAR: gate {gate_name} needs you",
                run["problem"][:160],
                priority="high",
                tags=["raised_hand"],
                click=dashboard_url(cfg),
            )
        else:
            update_run(root, cfg, run["id"], "stopped")
            notify(
                cfg,
                "RADAR: act run stopped",
                f"{run.get('ticket')}: rejected or tests failing — branch kept for review.",
                priority="high",
                tags=["x"],
                click=dashboard_url(cfg),
            )
        return rc

    update_run(root, cfg, run["id"], "failed")
    notify(
        cfg,
        "RADAR: act run failed",
        run["problem"][:160],
        priority="high",
        tags=["rotating_light"],
        click=dashboard_url(cfg),
    )
    return rc
