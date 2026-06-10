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


OPEN_STATUSES = {"proposed", "approved", "in-progress"}

PLACEHOLDER_CRITERIA = frozenset({
    "define done",
    "define acceptance criteria before approving",
})


def _normalize_criterion(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip().lower())


def criteria_ready(criteria: list[str]) -> bool:
    """True when at least one criterion is not a known placeholder string."""
    if not criteria:
        return False
    return any(_normalize_criterion(c) not in PLACEHOLDER_CRITERIA
               for c in criteria if c.strip())


def _strip_technical(text: str) -> str:
    """Remove backtick paths, CC parentheticals, and line-count suffixes."""

    def _backtick(m: re.Match) -> str:
        inner = m.group(1)
        return Path(inner).name if "/" in inner or "\\" in inner else inner

    text = re.sub(r"`([^`]+)`", _backtick, text)
    text = re.sub(r"\(CC\s+\d+[^)]*\)", "", text, flags=re.I)
    text = re.sub(r"\(\d+\s+lines\)", "", text, flags=re.I)
    return re.sub(r"\s+", " ", text).strip()


def _first_sentence(text: str, limit: int = 120) -> str:
    if not text:
        return ""
    sent = re.split(r"(?<=[.!?])\s+", text.strip(), maxsplit=1)[0]
    return _strip_technical(sent)[:limit]


def _parse_card_section(text: str) -> dict[str, str]:
    m = re.search(r"^## Card\n+(.+?)(?:\n##|\Z)", text, re.S | re.M)
    if not m:
        return {}
    card: dict[str, str] = {}
    for line in m.group(1).splitlines():
        for key in ("Outcome", "Story", "Title"):
            prefix = f"{key}:"
            if line.startswith(prefix):
                card[key.lower()] = line[len(prefix):].strip()
    return card


def _criteria_summary(criteria: list[str]) -> str:
    real = [c.strip() for c in criteria
            if c.strip() and _normalize_criterion(c) not in PLACEHOLDER_CRITERIA]
    return " · ".join(real[:2])


def derive_card(meta: dict, text: str) -> dict:
    """Build a PM-facing card from ticket ground truth.

    Base layer: heuristics from fingerprint kind (``refactor`` → reduce risk in
    basename, ``size`` → break up oversized basename, ``seam`` → make coupling
    explicit), else the first sentence of ``Why`` (≤120 chars). Technical
    paths and ``(CC N, …)`` / ``(N lines)`` parentheticals are stripped from
    display copy. Higher layers override: ``## Card`` fields, then frontmatter
    ``card_outcome`` / ``card_story`` / ``card_title``.
    """
    title = meta.get("title", "")
    why = meta.get("why", "")
    fingerprint = str(meta.get("fingerprint", ""))
    kind = fingerprint.split(":", 1)[0] if fingerprint else ""
    if not kind and meta.get("tags"):
        kind = str(meta["tags"][0])
    path_part = fingerprint.split(":", 1)[1] if ":" in fingerprint else ""
    basename = Path(path_part).name if path_part else ""

    if kind == "refactor":
        outcome = f"Reduce risk in {basename}" if basename else "Reduce risk in this area"
    elif kind == "size":
        outcome = f"Break up oversized {basename}" if basename else "Break up oversized file"
    elif kind == "seam":
        outcome = "Make coupling explicit"
    else:
        outcome = _first_sentence(why) or _strip_technical(title)

    card = {
        "title": title,
        "outcome": outcome,
        "story": "",
        "why_line": _first_sentence(why) or _strip_technical(why.splitlines()[0] if why else ""),
        "criteria_summary": _criteria_summary(meta.get("criteria", [])),
    }

    for key, val in _parse_card_section(text).items():
        if val:
            card[key] = val

    for fm_key, card_key in (("card_outcome", "outcome"), ("card_story", "story"),
                             ("card_title", "title")):
        if meta.get(fm_key):
            card[card_key] = str(meta[fm_key])

    return card


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
    checks = re.findall(r"^- \[([ x])\] (.+)$", text, re.M)
    meta["criteria"] = [c[1] for c in checks]
    meta["criteria_checked"] = [c[0] == "x" for c in checks]
    meta["criteria_ready"] = criteria_ready(meta["criteria"])
    meta["criteria_count"] = len(meta["criteria"])
    meta["card"] = derive_card(meta, text)
    meta["criteria_summary"] = meta["card"]["criteria_summary"]
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


def new_ticket(root: Path, cfg: dict, title: str, *, why: str = "",
               priority: str = "medium", criteria: list[str] | None = None,
               kind: str = "feature", source: str = "intent",
               status: str = "proposed") -> dict:
    """Intent intake: a human idea becomes a first-class ticket.

    Same lifecycle as scan-proposed tickets, so the loop (research -> spec ->
    act -> PR) picks it up identically. Fingerprinted by kind+title slug so
    re-submitting the same idea dedups instead of duplicating.
    """
    from .radar.sources import slugify
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
                        choices=["list", "new", "approve", "start", "reject", "done"])
    parser.add_argument("ticket_id", nargs="?",
                        help="ticket id (or the title, for `new`)")
    parser.add_argument("--repo", default=".", help="Repo root (default: cwd)")
    parser.add_argument("--why", default="", help="(new) rationale for the ticket")
    parser.add_argument("--priority", default="medium",
                        choices=["high", "medium", "low"], help="(new) priority")
    parser.add_argument("--criterion", action="append", default=[],
                        metavar="TEXT", help="(new) acceptance criterion; repeatable")
    parser.add_argument("--kind", default="feature",
                        help="(new) ticket kind: feature, refactor, chore... (default feature)")
    parser.add_argument("--approve", action="store_true",
                        help="(new) create directly as approved")
    args = parser.parse_args(argv)

    root = Path(args.repo).resolve()
    cfg = load_config(root)
    status_for = {"approve": "approved", "start": "in-progress",
                  "reject": "rejected", "done": "done"}

    if args.action == "new":
        if not args.ticket_id:
            parser.error("`new` requires a title: repo-scan tickets new \"...\"")
        if args.approve and not args.criterion:
            print("error: --approve requires at least one --criterion")
            return 1
        ticket = new_ticket(root, cfg, args.ticket_id, why=args.why,
                            priority=args.priority, criteria=args.criterion,
                            kind=args.kind,
                            status="approved" if args.approve else "proposed")
        ok(f"{ticket['id']} ({ticket['status']}): {ticket['title']}")
        if not args.criterion:
            print("  tip: acceptance criteria drive the spec and the tests —"
                  " add them with --criterion before approving")
        return 0

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
