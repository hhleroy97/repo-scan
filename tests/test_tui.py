"""radar top: the pure (curses-free) parts of the TUI."""

from pathlib import Path

from repo_scan.config import DEFAULT_CONFIG
from repo_scan.hub.state import peek_decision
from repo_scan.hub.tui import (S_SEL, actionable_items, apply_decision,
                               detail_lines, frame_lines)
from repo_scan.tickets import load_tickets, write_ticket

STATE = {
    "version": "0.4.0",
    "repo": {"name": "demo", "branch": "main"},
    "now": "2026-06-10 03:00 UTC",
    "scan": {"files": 10, "lines": 1234, "hotspots": 2, "critical": 1},
    "gates": [{"gate": "post_audit", "problem": "Fix the thing",
               "summary": "audit revise: needs work",
               "detail": {"audit_verdict": "revise",
                          "issues": ["issue one"], "doc": "specs/x.md"}}],
    "tickets": [
        {"id": "tkt-0001", "status": "proposed", "title": "Refactor A", "priority": "high"},
        {"id": "tkt-0002", "status": "approved", "title": "Refactor B", "priority": "low"},
        {"id": "tkt-0003", "status": "done", "title": "Old", "priority": "low"},
    ],
    "runs": [{"status": "waiting-on-gate", "gate": "post_audit",
              "problem": "Fix the thing", "kind": "loop"}],
    "activity": [{"when": "2026-06-10", "gate": "post_audit",
                  "decision": "approved", "summary": "ok"}],
    "usage": {
        "total": {"calls": 5, "input_tokens": 150000, "output_tokens": 2500,
                  "cache_read_tokens": 0, "duration_ms": 9000, "estimated": False},
        "today": {"calls": 2, "input_tokens": 60000, "output_tokens": 800,
                  "cache_read_tokens": 0, "duration_ms": 3000, "estimated": False},
        "by_model": {"composer-2.5": {"calls": 3, "input_tokens": 90000,
                                      "output_tokens": 1500},
                     "default": {"calls": 2, "input_tokens": 60000,
                                 "output_tokens": 1000}},
        "by_role": {"act": {"calls": 3, "input_tokens": 90000, "output_tokens": 1500}},
        "recent": [],
    },
}


def test_actionable_items_gates_first_done_excluded():
    items = actionable_items(STATE)
    assert [i["kind"] for i in items] == ["gate", "ticket", "ticket"]
    assert items[0]["gate"] == "post_audit"
    assert {i.get("id") for i in items[1:]} == {"tkt-0001", "tkt-0002"}


def test_frame_lines_renders_all_panels():
    text = "\n".join(t for _, t in frame_lines(STATE, sel=0))
    for needle in ("demo hub", "GATES (1)", "post_audit", "RUNS (1)",
                   "TICKETS (2 actionable)", "LLM USAGE", "composer-2.5",
                   "150.0k in", "RECENT DECISIONS", "a approve"):
        assert needle in text, needle


def test_frame_lines_selection_marker_moves():
    rows0 = frame_lines(STATE, sel=0)
    rows1 = frame_lines(STATE, sel=1)
    sel0 = [t for s, t in rows0 if s == S_SEL]
    sel1 = [t for s, t in rows1 if s == S_SEL]
    assert len(sel0) == len(sel1) == 1
    assert "post_audit" in sel0[0]
    assert "tkt-0001" in sel1[0]


def test_frame_lines_empty_state():
    text = "\n".join(t for _, t in frame_lines(
        {"repo": {}, "gates": [], "tickets": [], "runs": [], "usage": {}}, 0))
    assert "none waiting" in text and "no LLM calls" in text


def test_detail_lines_for_gate():
    item = actionable_items(STATE)[0]
    text = "\n".join(detail_lines(item))
    assert "audit: revise" in text
    assert "issue one" in text
    assert "specs/x.md" in text


def test_apply_decision_gate_writes_inbox(tmp_repo: Path):
    cfg = DEFAULT_CONFIG
    item = actionable_items(STATE)[0]
    msg = apply_decision(tmp_repo, cfg, item, "approve")
    assert "approve" in msg
    d = peek_decision(tmp_repo, cfg, "post_audit", "Fix the thing")
    assert d and d["decision"] == "approve" and d["source"] == "tui"


def test_apply_decision_ticket_lifecycle(tmp_repo: Path):
    cfg = DEFAULT_CONFIG
    write_ticket(tmp_repo, cfg, {"id": "tkt-0001", "title": "Refactor A",
                                 "priority": "high", "fingerprint": "x:1",
                                 "why": "w", "criteria": ["c"]})
    item = {"kind": "ticket", "id": "tkt-0001", "status": "proposed"}
    assert apply_decision(tmp_repo, cfg, item, "approve") == "tkt-0001: approved"
    item["status"] = "approved"
    assert apply_decision(tmp_repo, cfg, item, "approve") == "tkt-0001: in-progress"
    assert load_tickets(tmp_repo, cfg)[0]["status"] == "in-progress"
