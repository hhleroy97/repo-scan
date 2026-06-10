"""Hub dashboard UI: open-ticket helpers embedded in DASHBOARD_HTML."""

import json
import re

import pytest

from repo_scan.hub.contract import TICKET_BADGE_CLS, TICKET_STATUS_ORDER, js_contract_block
from repo_scan.hub.ui import DASHBOARD_HTML
from repo_scan.tickets import OPEN_STATUSES as TICKETS_OPEN_STATUSES


def _parse_open_statuses_from_block(block: str) -> set[str]:
    m = re.search(r"OPEN_TICKET_STATUSES=new Set\((\[.*?\])\)", block)
    assert m, "OPEN_TICKET_STATUSES Set missing from contract block"
    return set(json.loads(m.group(1)))


def _parse_status_order_from_block(block: str) -> dict[str, int]:
    m = re.search(r"TICKET_STATUS_ORDER=(\{[^}]+\})", block)
    assert m, "TICKET_STATUS_ORDER missing from contract block"
    return json.loads(m.group(1))


@pytest.fixture
def contract_block() -> str:
    return js_contract_block()


@pytest.fixture
def open_statuses(contract_block) -> set[str]:
    return _parse_open_statuses_from_block(contract_block)


@pytest.fixture
def status_order(contract_block) -> dict[str, int]:
    return _parse_status_order_from_block(contract_block)


@pytest.fixture
def all_status_tickets() -> list[dict]:
    return [
        {"id": "tkt-0001", "status": "proposed", "title": "P", "priority": "high", "kind": "feature"},
        {"id": "tkt-0002", "status": "approved", "title": "A", "priority": "medium", "kind": "fix"},
        {"id": "tkt-0003", "status": "in-progress", "title": "I", "priority": "low", "kind": "feature"},
        {"id": "tkt-0004", "status": "done", "title": "D", "priority": "medium", "kind": "feature"},
        {"id": "tkt-0005", "status": "rejected", "title": "R", "priority": "low", "kind": "fix"},
    ]


def test_open_tickets_helpers_defined_in_source(contract_block):
    for name in (
        "OPEN_TICKET_STATUSES",
        "TICKET_STATUS_ORDER",
        "TICKET_BADGE_CLS",
        "filterOpenTickets",
        "sortTickets",
        "rOpenTickets",
    ):
        assert name in DASHBOARD_HTML, f"{name} missing from dashboard source"
    assert contract_block in DASHBOARD_HTML


def test_open_ticket_statuses_match_python_contract(open_statuses):
    assert open_statuses == TICKETS_OPEN_STATUSES


def test_open_tickets_filter_includes_only_non_terminal(
    open_statuses, all_status_tickets,
):
    filtered = [t for t in all_status_tickets if t.get("status") in open_statuses]
    assert {t["status"] for t in filtered} == {"proposed", "approved", "in-progress"}
    assert {t["id"] for t in filtered} == {"tkt-0001", "tkt-0002", "tkt-0003"}


def test_open_tickets_sort_follows_workflow_order(open_statuses, status_order):
    tickets = [
        {"id": "tkt-0003", "status": "in-progress", "title": "I"},
        {"id": "tkt-0001", "status": "proposed", "title": "P"},
        {"id": "tkt-0002", "status": "approved", "title": "A"},
    ]
    filtered = [t for t in tickets if t.get("status") in open_statuses]
    ordered = sorted(filtered, key=lambda t: status_order.get(t.get("status", ""), 9))
    assert [t["status"] for t in ordered] == ["proposed", "approved", "in-progress"]
    assert status_order == TICKET_STATUS_ORDER


def test_rnow_open_tickets_renders_rows_for_fixture():
    """Row template includes status badge, PM outcome, priority, id, criteria count."""
    start = DASHBOARD_HTML.index("function rOpenTickets()")
    end = DASHBOARD_HTML.index("function rNow()", start)
    src = DASHBOARD_HTML[start:end]
    assert "TICKET_BADGE_CLS[t.status]" in src
    assert "ticketHeadline(t)" in src and "t.priority" in src
    assert "t.id" in src and "criteria_count" in src
    assert "Open tickets" in src
    assert "setTab('tickets')" in src


def test_open_tickets_section_omitted_when_empty():
    """rOpenTickets returns early when the filtered list is empty."""
    assert re.search(
        r"function rOpenTickets\(\)\{[^}]*if\(!open\.length\)return ''",
        DASHBOARD_HTML,
        re.DOTALL,
    ), "rOpenTickets must omit markup when no open tickets"


def test_rnow_places_open_tickets_after_gates_or_stats():
    start = DASHBOARD_HTML.index("function rNow()")
    end = DASHBOARD_HTML.index("function tok", start)
    src = DASHBOARD_HTML[start:end]
    assert "h+=rOpenTickets();" in src
    assert "if(S.gates.length){" in src
    assert "if(!S.gates.length)h+=rOpenTickets()" in src
    gates_idx = src.index("if(S.gates.length){")
    open_after_gates = src.index("h+=rOpenTickets();", gates_idx)
    stats_idx = src.index('<div class="grid">')
    open_no_gates = src.index("if(!S.gates.length)h+=rOpenTickets()")
    assert open_after_gates < stats_idx
    assert stats_idx < open_no_gates


def test_rtickets_uses_shared_sort_helpers():
    assert "sortTickets(S.tickets)" in DASHBOARD_HTML
    assert "TICKET_BADGE_CLS[t.status]" in DASHBOARD_HTML


def test_ticket_cards_render_card_outcome_and_criteria_count():
    for needle in (
        "function ticketCard(",
        "ticketHeadline",
        "criteria_count",
        "toggleTicket",
        "saveCriteria",
        "Define acceptance criteria before approving",
        "View ticket",
    ):
        assert needle in DASHBOARD_HTML, f"{needle} missing from dashboard"


def test_badge_cls_injected_from_contract(contract_block):
    assert json.dumps(TICKET_BADGE_CLS, separators=(",", ":")) in contract_block
    assert "TICKET_BADGE_CLS" in DASHBOARD_HTML
