"""Ticket lifecycle: intake, status transitions, criteria edits, work queue."""

import re
from pathlib import Path

from .board import write_board
from .constants import STATUSES, tickets_dir
from .io import load_tickets, next_ticket_num, write_ticket
from .parse import criteria_ready, parse_ticket


def new_ticket(root: Path, cfg: dict, title: str, *, why: str = "",
               priority: str = "medium", criteria: list[str] | None = None,
               kind: str = "feature", source: str = "intent",
               status: str = "proposed") -> dict:
    """Intent intake: a human idea becomes a first-class ticket.

    Same lifecycle as scan-proposed tickets, so the loop (research -> spec ->
    act -> PR) picks it up identically. Fingerprinted by kind+title slug so
    re-submitting the same idea dedups instead of duplicating.
    """
    from ..radar.sources import slugify
    title = title.strip()
    if not title:
        raise ValueError("ticket title required")
    fingerprint = f"{kind}:{slugify(title, 60)}"
    existing = load_tickets(root, cfg)
    dup = next((t for t in existing if t.get("fingerprint") == fingerprint), None)
    if dup:
        return dup
    ticket = {
        "id": f"tkt-{next_ticket_num(existing):04d}",
        "title": title,
        "status": status if status in STATUSES else "proposed",
        "origin": "human",
        "source": source,
        "priority": priority if priority in ("high", "medium", "low") else "medium",
        "fingerprint": fingerprint,
        "tags": [kind],
        "why": why or "_captured from intent — refine before approving_",
        "criteria": criteria or ["define acceptance criteria before approving"],
    }
    if ticket["status"] == "approved" and not criteria_ready(ticket["criteria"]):
        raise ValueError("acceptance criteria required before approving")
    write_ticket(root, cfg, ticket)
    write_board(root, cfg, load_tickets(root, cfg))
    ticket["path"] = tickets_dir(root, cfg) / f"{ticket['id']}.md"
    return ticket


def set_ticket_status(root: Path, cfg: dict, ticket_id: str, status: str) -> dict:
    """Update a ticket's frontmatter status and rebuild the board."""
    if status not in STATUSES:
        raise ValueError(f"invalid status {status!r} — one of {', '.join(STATUSES)}")
    tickets = load_tickets(root, cfg)
    ticket = next((t for t in tickets if t["id"] == ticket_id), None)
    if ticket is None:
        raise KeyError(f"no ticket with id {ticket_id!r}")
    if status == "approved" and not ticket.get("criteria_ready"):
        raise ValueError("acceptance criteria required before approving")
    path: Path = ticket["path"]
    text = path.read_text(encoding="utf-8")
    new_text, n = re.subn(r'^status: ".*?"', f'status: "{status}"', text,
                          count=1, flags=re.M)
    if n == 0:
        raise ValueError(f"{path.name} has no status frontmatter line")
    path.write_text(new_text, encoding="utf-8")
    ticket["status"] = status
    write_board(root, cfg, tickets)
    return ticket


def append_ticket_note(root: Path, cfg: dict, ticket_id: str, note: str):
    """Append a line under the ticket's ## Notes section."""
    tickets = load_tickets(root, cfg)
    ticket = next((t for t in tickets if t["id"] == ticket_id), None)
    if ticket is None:
        return
    path: Path = ticket["path"]
    text = path.read_text(encoding="utf-8")
    if "## Notes" in text:
        text = text.rstrip() + f"\n- {note}\n"
    else:
        text = text.rstrip() + f"\n\n## Notes\n\n- {note}\n"
    path.write_text(text, encoding="utf-8")


def update_ticket_criteria(root: Path, cfg: dict, ticket_id: str,
                           criteria: list[str]) -> dict:
    """Replace the ticket's acceptance-criteria checklist in markdown."""
    tickets = load_tickets(root, cfg)
    ticket = next((t for t in tickets if t["id"] == ticket_id), None)
    if ticket is None:
        raise KeyError(f"no ticket with id {ticket_id!r}")
    cleaned = [c.strip() for c in criteria if c.strip()]
    if not cleaned:
        raise ValueError("at least one acceptance criterion required")
    path: Path = ticket["path"]
    text = path.read_text(encoding="utf-8")
    block = "\n".join(f"- [ ] {c}" for c in cleaned) + "\n"
    if re.search(r"^## Acceptance criteria\n", text, re.M):
        new_text, n = re.subn(
            r"(^## Acceptance criteria\n+)(.+?)(?=\n## |\Z)",
            r"\1" + block,
            text,
            count=1,
            flags=re.S | re.M,
        )
        if n == 0:
            raise ValueError(f"{path.name} acceptance criteria section is malformed")
    else:
        anchor = "## Notes"
        if anchor in text:
            new_text = text.replace(anchor, f"## Acceptance criteria\n\n{block}\n{anchor}", 1)
        else:
            new_text = text.rstrip() + f"\n\n## Acceptance criteria\n\n{block}"
    path.write_text(new_text, encoding="utf-8")
    write_board(root, cfg, load_tickets(root, cfg))
    parsed = parse_ticket(path)
    assert parsed is not None
    return parsed


def approved_tickets(root: Path, cfg: dict) -> list[dict]:
    """Approved tickets with real acceptance criteria, highest priority
    first — the radar work queue (parallel loops take from the top)."""
    order = {"high": 0, "medium": 1, "low": 2}
    approved = [t for t in load_tickets(root, cfg)
                if t.get("status") == "approved" and t.get("criteria_ready")]
    approved.sort(key=lambda t: (order.get(t.get("priority", "medium"), 1), t["id"]))
    return approved


def pick_approved_ticket(root: Path, cfg: dict) -> dict | None:
    """Highest-priority approved ticket (single-loop callers, e.g. radar full)."""
    approved = approved_tickets(root, cfg)
    return approved[0] if approved else None
