"""Markdown ticket engine — the vault is the tracker.

One file per ticket in docs/tickets/, YAML frontmatter (Dataview-queryable),
plus a generated board.md in Obsidian Kanban format. The scan auto-proposes
tickets from its signals; humans review by editing `status` (or dragging
cards), and add their own tickets as plain files.

Each ticket's markdown is ground truth. ``parse_ticket()`` derives a PM-facing
``card`` (``title``, ``outcome``, ``story``, ``why_line``, ``criteria_summary``)
on read — never a parallel file. Override order: optional ``## Card`` block
(``Outcome:``, ``Story:``, ``Title:``), then frontmatter ``card_*`` keys, then
heuristics from fingerprint kind, ``Why``, and ``title``.

Approval is blocked until at least one non-placeholder acceptance criterion
exists (not ``define done`` or ``define acceptance criteria before approving``,
including case/whitespace variants). The same gate applies in hub, CLI, TUI,
and ``pick_approved_ticket()`` so legacy approved placeholders do not enter the
radar loop.

Dedup: every auto-ticket carries a content-stable `fingerprint`
(signal:file). A fingerprint that exists in ANY status — including
rejected — is never re-proposed, so saying no sticks.

Implementation lives in ``repo_scan/tickets/`` submodules; this package
re-exports the public surface for stable ``from repo_scan.tickets import …``
call sites.
"""

from ..utils import now_date

from .board import write_board
from .cli import tickets_main
from .constants import (
    BOARD_COLUMNS,
    METRIC_FINGERPRINT_PREFIXES,
    OPEN_STATUSES,
    PLACEHOLDER_CRITERIA,
    STATUSES,
    tickets_dir,
)
from .evidence import ticket_evidence_diagrams
from .generation import (
    auto_close_resolved_proposed,
    fingerprint_still_triggers,
    generate_tickets,
    is_metric_fingerprint,
    signals_from_scan_json,
)
from .io import load_tickets, next_ticket_num, write_ticket
from .merge import record_merge_verification
from .parse import criteria_ready, derive_card, parse_ticket
from .propose import propose_from_scan
from .workflow import (
    append_ticket_note,
    approved_tickets,
    new_ticket,
    pick_approved_ticket,
    set_ticket_status,
    update_ticket_criteria,
)

__all__ = [
    "STATUSES",
    "BOARD_COLUMNS",
    "OPEN_STATUSES",
    "PLACEHOLDER_CRITERIA",
    "METRIC_FINGERPRINT_PREFIXES",
    "tickets_dir",
    "criteria_ready",
    "derive_card",
    "parse_ticket",
    "load_tickets",
    "next_ticket_num",
    "ticket_evidence_diagrams",
    "write_ticket",
    "propose_from_scan",
    "new_ticket",
    "set_ticket_status",
    "append_ticket_note",
    "update_ticket_criteria",
    "approved_tickets",
    "pick_approved_ticket",
    "generate_tickets",
    "is_metric_fingerprint",
    "auto_close_resolved_proposed",
    "signals_from_scan_json",
    "fingerprint_still_triggers",
    "record_merge_verification",
    "write_board",
    "tickets_main",
    "now_date",
]
