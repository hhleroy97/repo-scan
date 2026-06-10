"""C3: ticket review CLI, approved-ticket radar queue, metrics-resolved flags."""

from pathlib import Path

import pytest

import repo_scan.radar.pipeline as pipeline
from repo_scan.config import DEFAULT_CONFIG, load_config
from repo_scan.tickets import (
    generate_tickets,
    load_tickets,
    pick_approved_ticket,
    set_ticket_status,
    tickets_main,
    write_ticket,
)

from tests.test_tickets import _signals


def _make_ticket(root: Path, num: int, priority: str = "medium", **kw):
    ticket = {"id": f"tkt-{num:04d}", "title": f"Ticket {num}", "priority": priority,
              "fingerprint": kw.pop("fingerprint", f"x:{num}"),
              "why": "because reasons", "criteria": ["done"], **kw}
    write_ticket(root, DEFAULT_CONFIG, ticket)
    return ticket


def test_set_ticket_status_roundtrip_and_board(tmp_repo: Path):
    _make_ticket(tmp_repo, 1)
    t = set_ticket_status(tmp_repo, DEFAULT_CONFIG, "tkt-0001", "approved")
    assert t["status"] == "approved"
    assert load_tickets(tmp_repo, DEFAULT_CONFIG)[0]["status"] == "approved"
    board = (tmp_repo / "docs" / "tickets" / "board.md").read_text()
    assert "## Approved" in board and "[[tkt-0001|Ticket 1]]" in board

    with pytest.raises(ValueError):
        set_ticket_status(tmp_repo, DEFAULT_CONFIG, "tkt-0001", "bogus")
    with pytest.raises(KeyError):
        set_ticket_status(tmp_repo, DEFAULT_CONFIG, "tkt-9999", "done")


def test_pick_approved_skips_placeholder_criteria(tmp_repo: Path):
    write_ticket(tmp_repo, DEFAULT_CONFIG, {
        "id": "tkt-0001", "title": "Bad", "fingerprint": "x:1",
        "why": "w", "criteria": ["define acceptance criteria before approving"],
    })
    path = tmp_repo / "docs" / "tickets" / "tkt-0001.md"
    path.write_text(path.read_text().replace('status: "proposed"', 'status: "approved"'))
    _make_ticket(tmp_repo, 2, priority="low")
    set_ticket_status(tmp_repo, DEFAULT_CONFIG, "tkt-0002", "approved")
    picked = pick_approved_ticket(tmp_repo, DEFAULT_CONFIG)
    assert picked["id"] == "tkt-0002"


def test_tickets_cli_approve_rejected_without_criteria(tmp_repo: Path):
    write_ticket(tmp_repo, DEFAULT_CONFIG, {
        "id": "tkt-0001", "title": "T", "fingerprint": "x:1",
        "why": "w", "criteria": ["define done"],
    })
    assert tickets_main(["approve", "tkt-0001", "--repo", str(tmp_repo)]) == 1
    assert load_tickets(tmp_repo, DEFAULT_CONFIG)[0]["status"] == "proposed"


def test_tickets_cli_new_approve_requires_criteria(tmp_repo: Path, capsys):
    assert tickets_main(["new", "Ship it", "--approve", "--repo", str(tmp_repo)]) == 1
    assert "criterion" in capsys.readouterr().out.lower()
    assert not list((tmp_repo / "docs" / "tickets").glob("tkt-*.md"))


def test_pick_approved_ticket_priority_order(tmp_repo: Path):
    _make_ticket(tmp_repo, 1, priority="low")
    _make_ticket(tmp_repo, 2, priority="high")
    _make_ticket(tmp_repo, 3, priority="high")
    assert pick_approved_ticket(tmp_repo, DEFAULT_CONFIG) is None  # nothing approved
    for tid in ("tkt-0001", "tkt-0003", "tkt-0002"):
        set_ticket_status(tmp_repo, DEFAULT_CONFIG, tid, "approved")
    picked = pick_approved_ticket(tmp_repo, DEFAULT_CONFIG)
    assert picked["id"] == "tkt-0002"  # high priority, lowest id


def test_tickets_cli_list_and_approve(tmp_repo: Path, capsys):
    _make_ticket(tmp_repo, 1)
    assert tickets_main(["list", "--repo", str(tmp_repo)]) == 0
    out = capsys.readouterr().out
    assert "tkt-0001" in out and "proposed" in out

    assert tickets_main(["approve", "tkt-0001", "--repo", str(tmp_repo)]) == 0
    assert load_tickets(tmp_repo, DEFAULT_CONFIG)[0]["status"] == "approved"

    assert tickets_main(["done", "tkt-9999", "--repo", str(tmp_repo)]) == 1


def test_metrics_resolved_flagged_on_board(tmp_repo: Path):
    cfg = dict(DEFAULT_CONFIG)
    generate_tickets(tmp_repo, cfg, _signals())  # refactor:hot.py + size:big.py
    set_ticket_status(tmp_repo, cfg, "tkt-0001", "in-progress")
    # next scan: hot.py is fixed (no churn x complexity), big.py still large
    _, resolved = generate_tickets(tmp_repo, cfg, _signals(churn=[], complexity=[]))
    assert [t["fingerprint"] for t in resolved] == ["refactor:hot.py"]
    board = (tmp_repo / "docs" / "tickets" / "board.md").read_text()
    assert "metrics resolved, ready to close" in board


def test_radar_full_consumes_approved_ticket(tmp_repo: Path, monkeypatch):
    cfg = load_config(tmp_repo)
    cfg["radar_enabled"] = True
    _make_ticket(tmp_repo, 1, priority="high")
    set_ticket_status(tmp_repo, DEFAULT_CONFIG, "tkt-0001", "approved")

    seen = {}

    def fake_loop(root, cfg, problem, approve=None, gates_override=None):
        seen["problem"] = problem
        return 0

    monkeypatch.setattr(pipeline, "cmd_loop", fake_loop)
    assert pipeline.cmd_full(tmp_repo, cfg) == 0
    assert "Ticket 1" in seen["problem"]
    assert "because reasons" in seen["problem"]

    ticket = load_tickets(tmp_repo, DEFAULT_CONFIG)[0]
    assert ticket["status"] == "in-progress"
    assert "radar spec approved" in ticket["path"].read_text()


def test_radar_full_stopped_loop_keeps_ticket_approved(tmp_repo: Path, monkeypatch):
    cfg = load_config(tmp_repo)
    cfg["radar_enabled"] = True
    _make_ticket(tmp_repo, 1)
    set_ticket_status(tmp_repo, DEFAULT_CONFIG, "tkt-0001", "approved")
    monkeypatch.setattr(pipeline, "cmd_loop", lambda *a, **k: 2)
    assert pipeline.cmd_full(tmp_repo, cfg) == 2
    assert load_tickets(tmp_repo, DEFAULT_CONFIG)[0]["status"] == "approved"
