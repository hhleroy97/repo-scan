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


def generate_tickets(root: Path, cfg: dict, signals: dict) -> int:
    """Dedup proposals against every existing fingerprint (any status,
    including rejected) and write the top N new tickets. Returns count."""
    existing = load_tickets(root, cfg)
    known = {t.get("fingerprint") for t in existing if t.get("fingerprint")}
    proposals = [p for p in propose_from_scan(cfg, **signals)
                 if p["fingerprint"] not in known]
    cap = cfg.get("tickets_max_new_per_scan", 5)
    num = next_ticket_num(existing)
    created = 0
    for p in proposals[:cap]:
        p["id"] = f"tkt-{num + created:04d}"
        write_ticket(root, cfg, p)
        created += 1
    if created or existing:
        write_board(root, cfg, load_tickets(root, cfg))
    return created


def write_board(root: Path, cfg: dict, tickets: list[dict]):
    """Obsidian Kanban-plugin board — review tickets by dragging cards."""
    lines = ["---", "", "kanban-plugin: board", "", "---", ""]
    for column, status in BOARD_COLUMNS:
        lines.append(f"## {column}")
        lines.append("")
        for t in tickets:
            if t.get("status") == status:
                done = "x" if status in ("done", "rejected") else " "
                lines.append(f"- [{done}] [[{t['id']}|{t['title']}]]")
        lines.append("")
    lines += ["%% kanban:settings", "```", '{"kanban-plugin":"board"}', "```", "%%", ""]
    path = tickets_dir(root, cfg) / "board.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    write_doc(path, "\n".join(lines), root)
