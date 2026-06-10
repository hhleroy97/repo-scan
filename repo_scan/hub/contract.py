"""Published hub API/state contract for server, UI, and TUI.

Single importable surface for ``/api/*`` route paths, ticket workflow maps,
and the ``build_state()`` JSON wire shape. ``js_contract_block()`` injects
the client-side literals into ``DASHBOARD_HTML`` at assembly time (no build
step). Distinct from ``state.py`` (run lifecycle helpers).
"""

from __future__ import annotations

import json
from typing import TypedDict

from ..tickets import OPEN_STATUSES, STATUSES

# --- HTTP routes (server handlers and embedded dashboard fetch paths) --------

API_STATE = "/api/state"
API_EVENTS = "/api/events"
API_DOC = "/api/doc"
API_GATE = "/api/gate"
API_PR_PREFIX = "/api/pr/"
API_TICKET = "/api/ticket"
API_TICKET_NEW = "/api/ticket/new"

# Dashboard POST ``action`` → ticket ``status`` (``tickets.STATUSES`` members).
TICKET_ACTION_STATUSES: dict[str, str] = {
    "approve": "approved",
    "reject": "rejected",
    "start": "in-progress",
    "done": "done",
}

# Client sort order — mirrors ``tickets.STATUSES`` workflow sequence.
TICKET_STATUS_ORDER: dict[str, int] = {s: i for i, s in enumerate(STATUSES)}

# Dashboard badge CSS classes (presentation-only; not in tickets.py).
TICKET_BADGE_CLS: dict[str, str] = {
    "proposed": "warn",
    "approved": "info",
    "in-progress": "info",
    "done": "ok",
    "rejected": "bad",
}


class RepoInfo(TypedDict):
    name: str
    branch: str


class ScanSummary(TypedDict, total=False):
    generated_at: str | None
    files: int
    lines: int
    hotspots: int
    critical: int
    languages: dict


class GateDrawer(TypedDict, total=False):
    ticket_id: str
    criteria: list[str]
    criteria_checked: list[bool]
    excerpt: str
    analysis_doc: str
    stale_warning: str


class GateRow(TypedDict, total=False):
    gate: str | None
    written_at: str | None
    summary: str
    problem: str
    detail: dict
    drawer: GateDrawer


class TicketRow(TypedDict, total=False):
    id: str
    status: str
    title: str
    priority: str
    why: str
    criteria: list[str]
    criteria_checked: list[bool]
    criteria_count: int
    criteria_ready: bool
    criteria_summary: str
    card: dict
    doc: str
    kind: str | None


class RunRow(TypedDict, total=False):
    id: str
    problem: str
    ticket: str
    kind: str
    status: str
    stage: str
    stage_detail: str
    gate: str
    updated_at: str


class HubState(TypedDict, total=False):
    version: str
    boot: str
    repo: RepoInfo
    now: str
    scan: ScanSummary
    gates: list[GateRow]
    tickets: list[TicketRow]
    runs: list[RunRow]
    live_runs: list[RunRow]
    activity: list[dict]
    events: list[dict]
    usage: dict
    prs: list[dict]


HUB_STATE_KEYS = frozenset({
    "version", "boot", "repo", "now", "scan", "gates", "tickets",
    "runs", "live_runs", "activity", "events", "usage", "prs",
})


def js_contract_block() -> str:
    """JavaScript literals for ticket workflow and API paths (injected into UI)."""
    open_list = sorted(OPEN_STATUSES)
    lines = [
        f"const OPEN_TICKET_STATUSES=new Set({json.dumps(open_list)});",
        f"const TICKET_STATUS_ORDER={json.dumps(TICKET_STATUS_ORDER, separators=(',', ':'))};",
        f"const TICKET_BADGE_CLS={json.dumps(TICKET_BADGE_CLS, separators=(',', ':'))};",
        f"const API_STATE={json.dumps(API_STATE)};",
        f"const API_EVENTS={json.dumps(API_EVENTS)};",
        f"const API_DOC={json.dumps(API_DOC)};",
        f"const API_GATE={json.dumps(API_GATE)};",
        f"const API_PR_PREFIX={json.dumps(API_PR_PREFIX)};",
        f"const API_TICKET={json.dumps(API_TICKET)};",
        f"const API_TICKET_NEW={json.dumps(API_TICKET_NEW)};",
    ]
    return "\n".join(lines)
