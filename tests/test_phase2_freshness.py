"""Phase 2 — act context bundle, merge record stage, auto-close resolved."""

import json

from repo_scan.config import DEFAULT_CONFIG
from repo_scan.hub.prs import _note_merged
from repo_scan.radar.act import build_act_context
from repo_scan.tickets import (auto_close_resolved_proposed, generate_tickets,
                               load_tickets, write_ticket)


def test_build_act_context_includes_snapshot_and_criteria(tmp_repo):
    cfg = DEFAULT_CONFIG.copy()
    docs = tmp_repo / "docs"
    docs.mkdir(exist_ok=True)
    (docs / "scan.json").write_text(json.dumps({
        "schema_version": 1,
        "generated_at": "2026-06-10 12:00 UTC",
        "repo": {"name": "repo", "branch": "main"},
        "languages": {"py": 1},
        "ranking": [{"file": "main.py", "lines": 2, "complexity": 0,
                     "tested": False, "commits": 0, "score": 1}],
        "files": {"main.py": {"lines": 2}},
        "complexity": [],
    }))
    ticket = {
        "id": "tkt-0099", "title": "T", "criteria": ["exports csv"],
        "fingerprint": "feature:x",
    }
    ctx = build_act_context(tmp_repo, cfg, ticket, "## Goal\nDo thing\n", tmp_repo, "radar/tkt-0099")
    assert "Acceptance criteria" in ctx
    assert "exports csv" in ctx
    assert "Repo snapshot" in ctx
    assert "Do thing" in ctx


def test_auto_close_resolved_proposed(tmp_repo):
    cfg = DEFAULT_CONFIG.copy()
    write_ticket(tmp_repo, cfg, {
        "id": "tkt-0001", "title": "Refactor gone.py", "status": "proposed",
        "fingerprint": "refactor:gone.py", "why": "was hot", "criteria": ["split file"],
    })
    resolved = [{"id": "tkt-0001", "status": "proposed", "fingerprint": "refactor:gone.py"}]
    closed = auto_close_resolved_proposed(tmp_repo, cfg, resolved)
    assert closed == ["tkt-0001"]
    t = load_tickets(tmp_repo, cfg)[0]
    assert t["status"] == "done"


def test_generate_tickets_auto_closes_proposed_resolved(tmp_repo, monkeypatch):
    cfg = DEFAULT_CONFIG.copy()
    write_ticket(tmp_repo, cfg, {
        "id": "tkt-0001", "title": "Refactor stale.py", "status": "proposed",
        "fingerprint": "refactor:stale.py", "why": "cc", "criteria": ["tests pass"],
    })
    signals = {
        "line_counts": {"main.py": {"lines": 2}},
        "ranking": [], "churn": [], "complexity": [],
        "tested": set(), "behavior": {}, "seams": [],
    }
    created, resolved = generate_tickets(tmp_repo, cfg, signals)
    assert created == 0
    assert any(t["id"] == "tkt-0001" for t in resolved)
    t = load_tickets(tmp_repo, cfg)[0]
    assert t["status"] == "done"


def test_note_merged_calls_record_verification(tmp_repo, monkeypatch):
    cfg = DEFAULT_CONFIG.copy()
    called = {}

    def fake_record(root, cfg, ticket_id, pr_number):
        called["ticket_id"] = ticket_id
        called["pr"] = pr_number

    monkeypatch.setattr("repo_scan.tickets.record_merge_verification", fake_record)
    from repo_scan.hub import prs as prs_mod
    with prs_mod._CACHE_LOCK:
        prs_mod._CACHE["prs"] = [{"number": 42, "ticket": "tkt-0042"}]
    write_ticket(tmp_repo, cfg, {
        "id": "tkt-0042", "title": "T", "status": "in-progress",
        "fingerprint": "feature:x", "why": "w", "criteria": ["done"],
    })
    _note_merged(tmp_repo, cfg, 42)
    assert called == {"ticket_id": "tkt-0042", "pr": 42}
