"""Ticket engine: auto-proposal, fingerprint dedup, rejection suppression, board."""

from pathlib import Path

import repo_scan
from repo_scan.config import DEFAULT_CONFIG
from repo_scan.tickets import (
    generate_tickets,
    load_tickets,
    next_ticket_num,
    parse_ticket,
    propose_from_scan,
    write_board,
    write_ticket,
)


def _signals(**overrides) -> dict:
    base = {
        "line_counts": {"big.py": {"lines": 700, "bytes": 20000}},
        "ranking": [],
        "churn": [{"file": "hot.py", "commits": 12}],
        "complexity": [{"file": "hot.py", "name": "f", "rank": "D", "complexity": 25, "lineno": 1}],
        "tested": set(),
        "behavior": {"coupling": [], "ownership": [], "age_days": {}},
        "seams": [],
    }
    base.update(overrides)
    return base


def test_propose_covers_signal_types():
    seams = [{"a": "a.py", "b": "b.py", "shared": 5, "degree": 80}]
    proposals = propose_from_scan(DEFAULT_CONFIG, **_signals(seams=seams))
    fps = {p["fingerprint"] for p in proposals}
    assert "refactor:hot.py" in fps
    assert "seam:a.py+b.py" in fps
    assert "size:big.py" in fps
    refactor = next(p for p in proposals if p["fingerprint"] == "refactor:hot.py")
    assert refactor["priority"] == "high"  # untested
    assert "untested" in refactor["title"]


def test_silo_proposals_require_multiple_repo_authors():
    own_single = [{"file": "a.py", "commits": 9, "authors": 1,
                   "top_author": "alice", "top_share": 1.0}]
    p = propose_from_scan(DEFAULT_CONFIG, **_signals(
        behavior={"coupling": [], "ownership": own_single, "age_days": {}}))
    assert not any(x["fingerprint"].startswith("silo:") for x in p)

    own_multi = own_single + [{"file": "b.py", "commits": 3, "authors": 1,
                               "top_author": "bob", "top_share": 1.0}]
    p = propose_from_scan(DEFAULT_CONFIG, **_signals(
        behavior={"coupling": [], "ownership": own_multi, "age_days": {}}))
    assert any(x["fingerprint"] == "silo:a.py" for x in p)


def test_generate_dedup_and_cap(tmp_repo: Path):
    cfg = dict(DEFAULT_CONFIG, tickets_max_new_per_scan=2)
    seams = [{"a": "a.py", "b": "b.py", "shared": 5, "degree": 80}]
    created, _ = generate_tickets(tmp_repo, cfg, _signals(seams=seams))
    assert created == 2  # capped (3 proposals available)
    created, _ = generate_tickets(tmp_repo, cfg, _signals(seams=seams))
    assert created == 1  # third one now
    created, _ = generate_tickets(tmp_repo, cfg, _signals(seams=seams))
    assert created == 0  # everything known


def test_rejected_fingerprint_never_reproposed(tmp_repo: Path):
    cfg = dict(DEFAULT_CONFIG)
    generate_tickets(tmp_repo, cfg, _signals())
    ticket = next(t for t in load_tickets(tmp_repo, cfg)
                  if t["fingerprint"] == "refactor:hot.py")
    text = ticket["path"].read_text().replace('status: "proposed"', 'status: "rejected"')
    ticket["path"].write_text(text)
    created, _ = generate_tickets(tmp_repo, cfg, _signals(line_counts={}))
    assert created == 0
    files = list((tmp_repo / "docs" / "tickets").glob("tkt-*.md"))
    assert len(files) == 2  # refactor (rejected) + size, nothing recreated


def test_human_tickets_loaded_and_on_board(tmp_repo: Path):
    cfg = dict(DEFAULT_CONFIG)
    tdir = tmp_repo / "docs" / "tickets"
    tdir.mkdir(parents=True)
    (tdir / "dark-mode.md").write_text(
        '---\nid: "dark-mode"\ntitle: "Add dark mode"\nstatus: "approved"\n'
        'origin: "human"\npriority: "high"\n---\n\n# Add dark mode\n')
    tickets = load_tickets(tmp_repo, cfg)
    assert any(t["origin"] == "human" for t in tickets)
    write_board(tmp_repo, cfg, tickets)
    board = (tdir / "board.md").read_text()
    assert "kanban-plugin: board" in board
    assert "## Approved" in board
    assert "[[dark-mode|Add dark mode]]" in board


def test_ids_increment_and_roundtrip(tmp_repo: Path):
    cfg = dict(DEFAULT_CONFIG)
    write_ticket(tmp_repo, cfg, {"id": "tkt-0001", "title": "T: a, b", "fingerprint": "x:y",
                                 "why": "because", "criteria": ["done"]})
    parsed = parse_ticket(tmp_repo / "docs" / "tickets" / "tkt-0001.md")
    assert parsed["status"] == "proposed"
    assert parsed["fingerprint"] == "x:y"
    assert parsed["title"] == "T: a, b"  # colon/comma survive quoting
    assert next_ticket_num([parsed]) == 2


def test_scan_proposes_tickets_end_to_end(tmp_repo_with_imports: Path):
    big = tmp_repo_with_imports / "huge.py"
    big.write_text("\n".join(f"x{i} = {i}" for i in range(700)))
    repo_scan.scan(tmp_repo_with_imports, quiet=True)
    tdir = tmp_repo_with_imports / "docs" / "tickets"
    tickets = list(tdir.glob("tkt-*.md"))
    assert tickets, "scan should propose at least the size ticket"
    board = (tdir / "board.md").read_text()
    assert "## Proposed" in board
    # second scan: no duplicates
    before = len(tickets)
    repo_scan.scan(tmp_repo_with_imports, quiet=True)
    assert len(list(tdir.glob("tkt-*.md"))) == before
