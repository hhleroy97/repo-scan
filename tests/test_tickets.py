"""Ticket engine: auto-proposal, fingerprint dedup, rejection suppression, board."""

from pathlib import Path

import pytest

import repo_scan
from repo_scan.config import DEFAULT_CONFIG
from repo_scan.tickets import (
    criteria_ready,
    generate_tickets,
    load_tickets,
    next_ticket_num,
    parse_ticket,
    propose_from_scan,
    set_ticket_status,
    ticket_evidence_diagrams,
    write_board,
    write_ticket,
)


def _signals(**overrides) -> dict:
    base = {
        "line_counts": {"big.py": {"lines": 700, "bytes": 20000},
                        "hot.py": {"lines": 100, "bytes": 3000},
                        "a.py": {"lines": 50, "bytes": 1500},
                        "b.py": {"lines": 50, "bytes": 1500}},
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


def test_criteria_ready_rejects_placeholders():
    assert not criteria_ready(["define done"])
    assert not criteria_ready(["  Define Acceptance Criteria Before Approving  "])
    assert criteria_ready(["define done", "tests pass"])
    assert criteria_ready(["Complexity of every function below rank C"])


def test_derive_card_from_refactor_ticket(tmp_repo: Path):
    cfg = dict(DEFAULT_CONFIG)
    ticket = {
        "id": "tkt-0099",
        "title": "Refactor repo_scan/graphs.py (CC 56, 3 commits)",
        "fingerprint": "refactor:repo_scan/graphs.py",
        "why": "`repo_scan/graphs.py` is both high-churn (3 commits) and "
               "high-complexity (total CC 56).",
        "criteria": ["Complexity of every function below rank C"],
    }
    write_ticket(tmp_repo, cfg, ticket)
    path = tmp_repo / "docs" / "tickets" / "tkt-0099.md"
    parsed = parse_ticket(path)
    assert parsed["title"] == ticket["title"]
    outcome = parsed["card"]["outcome"]
    assert "repo_scan" not in outcome and "CC" not in outcome
    assert outcome == "Reduce risk in graphs.py"


def test_parse_ticket_card_section_overrides(tmp_repo: Path):
    cfg = dict(DEFAULT_CONFIG)
    tdir = tmp_repo / "docs" / "tickets"
    tdir.mkdir(parents=True)
    (tdir / "tkt-0100.md").write_text(
        '---\nid: "tkt-0100"\ntitle: "Technical title"\nstatus: "proposed"\n'
        'fingerprint: "feature:x"\n---\n\n# Technical title\n\n## Why\n\nBecause.\n\n'
        "## Card\n\n"
        "Outcome: Ship the friendly outcome\n"
        "Story: As a PM I can triage quickly\n"
        "Title: PM headline\n\n"
        "## Acceptance criteria\n\n- [ ] real criterion\n")
    parsed = parse_ticket(tdir / "tkt-0100.md")
    assert parsed["card"]["outcome"] == "Ship the friendly outcome"
    assert parsed["card"]["story"] == "As a PM I can triage quickly"
    assert parsed["card"]["title"] == "PM headline"
    assert parsed["title"] == "Technical title"


def test_approve_blocked_without_valid_criteria(tmp_repo: Path):
    cfg = dict(DEFAULT_CONFIG)
    write_ticket(tmp_repo, cfg, {
        "id": "tkt-0001", "title": "T", "fingerprint": "x:1",
        "why": "w", "criteria": ["define acceptance criteria before approving"],
    })
    with pytest.raises(ValueError, match="acceptance criteria"):
        set_ticket_status(tmp_repo, cfg, "tkt-0001", "approved")


def test_write_ticket_evidence_diagrams(tmp_repo: Path):
    cfg = dict(DEFAULT_CONFIG)
    signals = _signals(
        seams=[{"a": "a.py", "b": "b.py", "shared": 5, "degree": 80}],
        behavior={"coupling": [{"a": "hot.py", "b": "a.py", "shared": 4, "degree": 70}],
                  "ownership": [], "age_days": {}},
        py_edges=[],
        ts_edges=[],
        line_counts={"hot.py": {"lines": 100}, "a.py": {"lines": 50},
                     "b.py": {"lines": 50}, "big.py": {"lines": 700}},
    )
    write_ticket(tmp_repo, cfg, {
        "id": "tkt-0001",
        "title": "Refactor hot.py",
        "fingerprint": "refactor:hot.py",
        "why": "hot",
        "criteria": ["done"],
    }, signals=signals)
    text = (tmp_repo / "docs" / "tickets" / "tkt-0001.md").read_text()
    assert "## Evidence" in text
    assert "```mermaid" in text
    assert "graph TD" in text
    assert "class hot_py focal" in text

    disabled = dict(cfg, ticket_diagrams_enabled=False)
    write_ticket(tmp_repo, disabled, {
        "id": "tkt-0002",
        "title": "Seam",
        "fingerprint": "seam:a.py+b.py",
        "why": "seam",
        "criteria": ["done"],
    }, signals=signals)
    no_ev = (tmp_repo / "docs" / "tickets" / "tkt-0002.md").read_text()
    assert "## Evidence" not in no_ev


def test_size_ticket_evidence_callout_only(tmp_repo: Path):
    cfg = dict(DEFAULT_CONFIG)
    signals = _signals(line_counts={"big.py": {"lines": 700}})
    write_ticket(tmp_repo, cfg, {
        "id": "tkt-0003",
        "title": "Split big.py",
        "fingerprint": "size:big.py",
        "why": "big",
        "criteria": ["done"],
    }, signals=signals)
    text = (tmp_repo / "docs" / "tickets" / "tkt-0003.md").read_text()
    assert "## Evidence" in text
    assert "[[reports/health#file-sizes]]" in text
    assert "```mermaid" not in text


def test_evidence_no_quadrant_chart(tmp_repo: Path):
    cfg = dict(DEFAULT_CONFIG)
    signals = _signals()
    for fp in ("refactor:hot.py", "seam:a.py+b.py"):
        tid = "tkt-0101" if fp.startswith("refactor") else "tkt-0102"
        write_ticket(tmp_repo, cfg, {
            "id": tid,
            "title": fp,
            "fingerprint": fp,
            "why": "w",
            "criteria": ["done"],
        }, signals={**signals, "seams": [{"a": "a.py", "b": "b.py", "shared": 5, "degree": 80}],
                    "behavior": {"coupling": [{"a": "a.py", "b": "b.py", "shared": 5, "degree": 80},
                                              {"a": "hot.py", "b": "a.py", "shared": 4, "degree": 70}],
                                 "ownership": [], "age_days": {}}})
    for tid in ("tkt-0101", "tkt-0102"):
        body = (tmp_repo / "docs" / "tickets" / f"{tid}.md").read_text()
        evidence = body.split("## Evidence", 1)[1].split("## Notes", 1)[0]
        assert "quadrantChart" not in evidence
        assert "xychart-beta" not in evidence


def test_ticket_evidence_diagrams_unit():
    signals = _signals(
        behavior={"coupling": [{"a": "hot.py", "b": "n.py", "shared": 4, "degree": 60}],
                  "ownership": [], "age_days": {}},
    )
    lines = ticket_evidence_diagrams("refactor:hot.py", signals, DEFAULT_CONFIG)
    assert any("graph TD" in l for l in lines)
    assert ticket_evidence_diagrams("stale:x.py", signals, DEFAULT_CONFIG) == []


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
