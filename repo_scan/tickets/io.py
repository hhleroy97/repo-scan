"""Load and write ticket markdown files on disk."""

import re
from pathlib import Path

import repo_scan.tickets as tickets_pkg

from ..radar.sources import frontmatter
from ..utils import write_doc
from .constants import tickets_dir
from .evidence import ticket_evidence_diagrams
from .parse import parse_ticket


def load_tickets(root: Path, cfg: dict) -> list[dict]:
    tdir = tickets_dir(root, cfg)
    if not tdir.is_dir():
        return []
    tickets = []
    for f in sorted(tdir.glob("tkt-*.md")):
        meta = parse_ticket(f)
        if meta:
            tickets.append(meta)
    # human tickets may use any filename — pick up everything else with status
    for f in sorted(tdir.glob("*.md")):
        if f.name == "board.md" or f.name.startswith("tkt-"):
            continue
        meta = parse_ticket(f)
        if meta:
            tickets.append(meta)
    return tickets


def next_ticket_num(tickets: list[dict]) -> int:
    nums = []
    for t in tickets:
        m = re.match(r"tkt-(\d+)", str(t.get("id", "")))
        if m:
            nums.append(int(m.group(1)))
    return max(nums, default=0) + 1


def write_ticket(root: Path, cfg: dict, ticket: dict,
                 signals: dict | None = None) -> Path:
    """Write a new ticket file. Never overwrites an existing one.

    When ``signals`` is provided for scan-origin tickets, inserts a ``## Evidence``
    section (Mermaid diagrams keyed by fingerprint) before ``## Notes``.
    """
    tdir = tickets_dir(root, cfg)
    tdir.mkdir(parents=True, exist_ok=True)
    path = tdir / f"{ticket['id']}.md"
    if path.exists():
        return path
    criteria = ticket.get("criteria", [])
    evidence_body: list[str] = []
    if signals and ticket.get("origin", "auto") != "human":
        fp = ticket.get("fingerprint", "")
        if fp:
            evidence_body = ticket_evidence_diagrams(fp, signals, cfg)
    lines = [
        frontmatter({
            "id": ticket["id"],
            "title": ticket["title"],
            "status": ticket.get("status", "proposed"),
            "origin": ticket.get("origin", "auto"),
            "source": ticket.get("source", "scan"),
            "priority": ticket.get("priority", "medium"),
            "fingerprint": ticket.get("fingerprint", ""),
            "evidence": ticket.get("evidence", []),
            "created": tickets_pkg.now_date(),
            "tags": ["ticket"] + ticket.get("tags", []),
        }),
        "",
        f"# {ticket['title']}",
        "",
        "## Why",
        "",
        ticket.get("why", "_no rationale recorded_"),
        "",
        "## Acceptance criteria",
        "",
    ]
    lines += [f"- [ ] {c}" for c in criteria] or ["- [ ] define done"]
    if evidence_body:
        lines += ["", "## Evidence", "", f"_Created {tickets_pkg.now_date()} from scan data_", ""]
        lines += evidence_body
    lines += ["", "## Notes", "", "_yours to annotate_", ""]
    write_doc(path, "\n".join(lines), root)
    return path
