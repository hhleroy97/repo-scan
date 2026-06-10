"""Markdown ticket engine — the vault is the tracker.

One file per ticket in docs/tickets/, YAML frontmatter (Dataview-queryable),
plus a generated board.md in Obsidian Kanban format. The scan auto-proposes
tickets from its signals; humans review by editing `status` (or dragging
cards), and add their own tickets as plain files.

Dedup: every auto-ticket carries a content-stable `fingerprint`
(signal:file). A fingerprint that exists in ANY status — including
rejected — is never re-proposed, so saying no sticks.
"""

import re
from pathlib import Path

from .radar.sources import frontmatter, parse_frontmatter
from .utils import now_date, ok, write_doc

STATUSES = ["proposed", "approved", "in-progress", "done", "rejected"]
BOARD_COLUMNS = [("Proposed", "proposed"), ("Approved", "approved"),
                 ("In progress", "in-progress"), ("Done", "done"),
                 ("Rejected", "rejected")]


def tickets_dir(root: Path, cfg: dict) -> Path:
    return root / cfg["docs_dir"] / "tickets"


def parse_ticket(path: Path) -> dict | None:
    text = path.read_text(encoding="utf-8", errors="ignore")
    meta = parse_frontmatter(text)
    if not meta or "status" not in meta:
        return None
    title = next((l[2:].strip() for l in text.splitlines() if l.startswith("# ")),
                 meta.get("title", path.stem))
    meta.setdefault("id", path.stem)
    meta["title"] = meta.get("title") or title
    meta["path"] = path
    m = re.search(r"^## Why\n+(.+?)(?:\n##|\Z)", text, re.S | re.M)
    meta["why"] = m.group(1).strip() if m else ""
    return meta


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


def write_ticket(root: Path, cfg: dict, ticket: dict) -> Path:
    """Write a new ticket file. Never overwrites an existing one."""
    tdir = tickets_dir(root, cfg)
    tdir.mkdir(parents=True, exist_ok=True)
    path = tdir / f"{ticket['id']}.md"
    if path.exists():
        return path
    criteria = ticket.get("criteria", [])
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
            "created": now_date(),
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
    lines += ["", "## Notes", "", "_yours to annotate_", ""]
    write_doc(path, "\n".join(lines), root)
    return path


def propose_from_scan(cfg: dict, *, line_counts: dict, ranking: list,
                      churn: list, complexity: list, tested: set,
                      behavior: dict, seams: list) -> list[dict]:
    """Build ticket proposals from every scan signal, strongest first."""
    churn_by_file = {c["file"]: c["commits"] for c in churn}
    cc_by_file: dict[str, int] = {}
    for item in complexity:
        cc_by_file[item["file"]] = cc_by_file.get(item["file"], 0) + item["complexity"]

    proposals: list[dict] = []

    # 1. refactor: high churn x high complexity (untested = high priority)
    for f in sorted(set(churn_by_file) & set(cc_by_file),
                    key=lambda f: churn_by_file[f] * cc_by_file[f], reverse=True):
        untested = f not in tested
        proposals.append({
            "fingerprint": f"refactor:{f}",
            "title": f"Refactor {f} (CC {cc_by_file[f]}, {churn_by_file[f]} commits"
                     + (", untested)" if untested else ")"),
            "priority": "high" if untested else "medium",
            "tags": ["refactor"],
            "evidence": ["[[reports/health]]", "[[research/candidates]]"],
            "why": f"`{f}` is both high-churn ({churn_by_file[f]} commits) and "
                   f"high-complexity (total CC {cc_by_file[f]})"
                   + (" with no matching test file." if untested else "."),
            "criteria": [
                "Complexity of every function below rank C",
                *(["Test file exists and passes"] if untested else []),
                "Trend delta confirms complexity drop",
            ],
        })

    # 2. hidden seams: coupled in history, no import edge
    for s in seams:
        proposals.append({
            "fingerprint": f"seam:{s['a']}+{s['b']}",
            "title": f"Hidden seam: {s['a']} <-> {s['b']} ({s['degree']}% coupled)",
            "priority": "medium",
            "tags": ["architecture"],
            "evidence": ["[[reports/coupling]]"],
            "why": f"`{s['a']}` and `{s['b']}` changed together in {s['shared']} commits "
                   f"({s['degree']}% degree) but share no import edge — an implicit "
                   "contract the dependency graph can't see.",
            "criteria": ["Make the dependency explicit (shared module or import)",
                         "Coupling degree drops below threshold in coupling.md"],
        })

    # 3. size: files over the critical line threshold
    crit = cfg["line_crit"]
    for f, s in sorted(line_counts.items(), key=lambda x: x[1]["lines"], reverse=True):
        if s["lines"] >= crit:
            proposals.append({
                "fingerprint": f"size:{f}",
                "title": f"Split {f} ({s['lines']} lines)",
                "priority": "medium",
                "tags": ["refactor"],
                "evidence": ["[[reports/health]]"],
                "why": f"`{f}` is {s['lines']} lines — past the {crit}-line critical "
                       "threshold where files become hard to navigate and review.",
                "criteria": [f"No resulting file above {cfg['line_warn']} lines",
                             "All tests still pass"],
            })

    # 4. stale hubs: top-ranked files untouched for a long time
    age = behavior.get("age_days", {})
    stale_days = cfg.get("stale_days", 180)
    for r in ranking[:5]:
        f = r["file"]
        if age.get(f, 0) >= stale_days:
            proposals.append({
                "fingerprint": f"stale:{f}",
                "title": f"Review stale hub {f} ({age[f]} days untouched)",
                "priority": "low",
                "tags": ["maintenance"],
                "evidence": ["[[index]]", "[[reports/health]]"],
                "why": f"`{f}` ranks in the top 5 by importance but hasn't changed in "
                       f"{age[f]} days — high-risk surface if a change is ever needed.",
                "criteria": ["Confirm tests cover current behavior",
                             "Document any implicit invariants"],
            })

    # 5. knowledge silos — only meaningful with more than one contributor
    all_authors = {o["top_author"] for o in behavior.get("ownership", [])}
    if len(all_authors) > 1:
        silo_share = cfg.get("silo_min_share", 0.9)
        for o in behavior.get("ownership", []):
            if o["top_share"] >= silo_share and o["authors"] == 1 and o["commits"] >= 5:
                proposals.append({
                    "fingerprint": f"silo:{o['file']}",
                    "title": f"Knowledge silo: {o['file']} ({o['top_author']} owns 100%)",
                    "priority": "low",
                    "tags": ["bus-factor"],
                    "evidence": ["[[reports/health]]"],
                    "why": f"`{o['file']}` has {o['commits']} commits, all by one author "
                           "— a bus-factor risk.",
                    "criteria": ["Pair/review the next change with a second person",
                                 "Add or expand docs for this area"],
                })
    return proposals


OPEN_STATUSES = {"proposed", "approved", "in-progress"}


def set_ticket_status(root: Path, cfg: dict, ticket_id: str, status: str) -> dict:
    """Update a ticket's frontmatter status and rebuild the board."""
    if status not in STATUSES:
        raise ValueError(f"invalid status {status!r} — one of {', '.join(STATUSES)}")
    tickets = load_tickets(root, cfg)
    ticket = next((t for t in tickets if t["id"] == ticket_id), None)
    if ticket is None:
        raise KeyError(f"no ticket with id {ticket_id!r}")
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


def pick_approved_ticket(root: Path, cfg: dict) -> dict | None:
    """Highest-priority approved ticket — the radar loop's work queue."""
    order = {"high": 0, "medium": 1, "low": 2}
    approved = [t for t in load_tickets(root, cfg) if t.get("status") == "approved"]
    approved.sort(key=lambda t: (order.get(t.get("priority", "medium"), 1), t["id"]))
    return approved[0] if approved else None


def generate_tickets(root: Path, cfg: dict, signals: dict) -> tuple[int, list[dict]]:
    """Dedup proposals against every existing fingerprint (any status,
    including rejected) and write the top N new tickets.

    Returns (created_count, metrics_resolved) where metrics_resolved are open
    tickets whose fingerprint no longer triggers — the underlying metric
    cleared, so they're likely ready to close."""
    existing = load_tickets(root, cfg)
    known = {t.get("fingerprint") for t in existing if t.get("fingerprint")}
    proposals = propose_from_scan(cfg, **signals)
    current_fps = {p["fingerprint"] for p in proposals}
    fresh = [p for p in proposals if p["fingerprint"] not in known]
    cap = cfg.get("tickets_max_new_per_scan", 5)
    num = next_ticket_num(existing)
    created = 0
    for p in fresh[:cap]:
        p["id"] = f"tkt-{num + created:04d}"
        write_ticket(root, cfg, p)
        created += 1

    resolved = [t for t in existing
                if t.get("status") in OPEN_STATUSES
                and t.get("fingerprint") and t["fingerprint"] not in current_fps]
    if created or existing:
        write_board(root, cfg, load_tickets(root, cfg),
                    resolved_ids={t["id"] for t in resolved})
    return created, resolved


def write_board(root: Path, cfg: dict, tickets: list[dict],
                resolved_ids: set | None = None):
    """Obsidian Kanban-plugin board — review tickets by dragging cards."""
    resolved_ids = resolved_ids or set()
    lines = ["---", "", "kanban-plugin: board", "", "---", ""]
    for column, status in BOARD_COLUMNS:
        lines.append(f"## {column}")
        lines.append("")
        for t in tickets:
            if t.get("status") == status:
                done = "x" if status in ("done", "rejected") else " "
                note = " — **metrics resolved, ready to close**" if t["id"] in resolved_ids else ""
                lines.append(f"- [{done}] [[{t['id']}|{t['title']}]]{note}")
        lines.append("")
    lines += ["%% kanban:settings", "```", '{"kanban-plugin":"board"}', "```", "%%", ""]
    path = tickets_dir(root, cfg) / "board.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    write_doc(path, "\n".join(lines), root)


def tickets_main(argv: list[str]) -> int:
    """`repo-scan tickets [list|approve|start|reject|done] [id]`"""
    import argparse

    from .config import load_config

    parser = argparse.ArgumentParser(
        prog="repo-scan tickets",
        description="Review scan-generated tickets from the terminal",
    )
    parser.add_argument("action", nargs="?", default="list",
                        choices=["list", "approve", "start", "reject", "done"])
    parser.add_argument("ticket_id", nargs="?", help="e.g. tkt-0001")
    parser.add_argument("--repo", default=".", help="Repo root (default: cwd)")
    args = parser.parse_args(argv)

    root = Path(args.repo).resolve()
    cfg = load_config(root)
    status_for = {"approve": "approved", "start": "in-progress",
                  "reject": "rejected", "done": "done"}

    if args.action == "list":
        tickets = load_tickets(root, cfg)
        if not tickets:
            print("no tickets — run repo-scan to propose some")
            return 0
        order = {s: i for i, (_, s) in enumerate(BOARD_COLUMNS)}
        prio = {"high": 0, "medium": 1, "low": 2}
        tickets.sort(key=lambda t: (order.get(t.get("status"), 9),
                                    prio.get(t.get("priority", "medium"), 1), t["id"]))
        for t in tickets:
            title = t["title"] if len(t["title"]) <= 70 else t["title"][:69] + "…"
            print(f"{t['id']:<10} {t.get('status', '?'):<12} "
                  f"{t.get('priority', '?'):<7} {t.get('origin', '?'):<6} {title}")
        return 0

    if not args.ticket_id:
        parser.error(f"'{args.action}' requires a ticket id")
    try:
        ticket = set_ticket_status(root, cfg, args.ticket_id, status_for[args.action])
    except (KeyError, ValueError) as e:
        ok_or_err = str(e).strip("'")
        print(f"error: {ok_or_err}")
        return 1
    ok(f"{ticket['id']} -> {status_for[args.action]}  ({ticket['title']})")
    return 0
