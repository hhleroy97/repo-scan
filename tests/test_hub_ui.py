"""Hub dashboard UI: open-ticket helpers embedded in DASHBOARD_HTML."""

import hashlib
import json
import re
from pathlib import Path

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


def test_rnow_layout_metrics_then_live_then_actions():
    start = DASHBOARD_HTML.index("function rNow()")
    end = DASHBOARD_HTML.index("function tok", start)
    src = DASHBOARD_HTML[start:end]
    stats_idx = src.index('<div class="grid">')
    live_idx = src.index("h+=rLiveRuns();")
    actions_idx = src.index("h+=rNowPRsAndGates();")
    assert stats_idx < live_idx < actions_idx
    assert "h+=rOpenTickets()" not in src
    assert "S.runs" not in src
    assert "gate(s) waiting" not in src
    assert "setTab('gates')" not in src


def test_rnow_prs_and_gates_combined_with_direct_approve():
    assert "function rNowPRsAndGates()" in DASHBOARD_HTML
    assert "PRs &amp; gates" in DASHBOARD_HTML
    start = DASHBOARD_HTML.index("function rNowPRsAndGates()")
    end = DASHBOARD_HTML.index("function rFeed()", start)
    src = DASHBOARD_HTML[start:end]
    assert "rGateCard(g,gi)" in src
    assert "rPRCard" in src
    assert "gateDecide(" in DASHBOARD_HTML
    assert "function rGateCard(" in DASHBOARD_HTML


def test_dashboard_has_telemetry_section():
    assert "function rTelemetry()" in DASHBOARD_HTML
    assert "Pipeline telemetry" in DASHBOARD_HTML
    assert "S.telemetry" in DASHBOARD_HTML


def test_dashboard_has_stage_burn_chart():
    assert "function rStageBurnChart()" in DASHBOARD_HTML
    assert "function buildStageChartClient(" in DASHBOARD_HTML
    assert "function setBurnView(" in DASHBOARD_HTML
    assert "function setBurnRun(" in DASHBOARD_HTML
    assert "burn-tabs" in DASHBOARD_HTML
    assert "Avg / run" in DASHBOARD_HTML
    assert "burn-chart" in DASHBOARD_HTML
    assert "pct_time" in DASHBOARD_HTML
    assert "pct_tokens" in DASHBOARD_HTML
    assert "views.runs" in DASHBOARD_HTML


def test_rlive_runs_omits_gate_navigation():
    start = DASHBOARD_HTML.index("function rLiveRuns()")
    end = DASHBOARD_HTML.index("function rNow()", start)
    src = DASHBOARD_HTML[start:end]
    assert "setTab('gates')" not in src
    assert "Gate:" not in src


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


def test_dashboard_has_knowledge_tab():
    assert 'data-tab="dashboard"' in DASHBOARD_HTML
    assert "Knowledge dashboard" in DASHBOARD_HTML
    assert "function rGraph()" in DASHBOARD_HTML
    assert "function mountGraph()" in DASHBOARD_HTML
    assert "API_GRAPH" in DASHBOARD_HTML
    assert "graph-wrap" in DASHBOARD_HTML


def test_dashboard_has_audit_panels():
    assert "function rGraphDashboard()" in DASHBOARD_HTML
    assert "Signal coverage" in DASHBOARD_HTML
    assert "function signalGlyphs(" in DASHBOARD_HTML
    assert "dash-matrix" in DASHBOARD_HTML
    assert "Score distribution" in DASHBOARD_HTML
    assert "Untracked code" in DASHBOARD_HTML
    assert "graphLayer==='coverage'" in DASHBOARD_HTML
    assert "scoreRingColor" in DASHBOARD_HTML
    assert "function graphEdgeStyle(" in DASHBOARD_HTML


def test_dashboard_has_mermaid_agentic_loop():
    assert "function rGraphPipeline()" in DASHBOARD_HTML
    assert "function renderAgenticLoopMermaid()" in DASHBOARD_HTML
    assert "agentic-loop-host" in DASHBOARD_HTML
    assert "agentic_loop_mermaid" in DASHBOARD_HTML
    assert "/static/mermaid.min.js" in DASHBOARD_HTML
    assert "mermaid-wrap" in DASHBOARD_HTML


def test_dashboard_has_chain_panel():
    assert "function openGraphChain(" in DASHBOARD_HTML
    assert "API_GRAPH_CHAIN" in DASHBOARD_HTML
    assert "graph-chain" in DASHBOARD_HTML
    assert "dash-sigs" in DASHBOARD_HTML


def test_dashboard_has_sparkline_and_delta():
    assert "function sparkSVG(" in DASHBOARD_HTML
    assert "function deltaTag(" in DASHBOARD_HTML
    assert "trend_sparkline" in DASHBOARD_HTML
    assert "vault_delta" in DASHBOARD_HTML


def test_dashboard_has_knowledge_debt_card():
    assert "knowledge debt" in DASHBOARD_HTML
    assert "knowledge_debt" in DASHBOARD_HTML


def test_dashboard_has_approved_unhealthy_badge():
    assert "approved_unhealthy" in DASHBOARD_HTML
    assert "approved unhealthy" in DASHBOARD_HTML


def test_dashboard_has_thin_links_section():
    assert "function rDashThinLinks()" in DASHBOARD_HTML
    assert "thin_citations" in DASHBOARD_HTML
    assert "Fragile code links" in DASHBOARD_HTML


def test_dashboard_has_trend_chart():
    assert "function rDashTrendChart()" in DASHBOARD_HTML
    assert "Scan trend" in DASHBOARD_HTML
    assert "viewBox" in DASHBOARD_HTML


def test_dashboard_matrix_cells_are_clickable():
    start = DASHBOARD_HTML.index("function rDashMatrix()")
    end = DASHBOARD_HTML.index("function rDashHistogram()", start)
    src = DASHBOARD_HTML[start:end]
    assert "onclick" in src
    assert "setGraphMissFilter" in src


def test_graph_controls_stack_contiguous():
    start = DASHBOARD_HTML.index("function rGraph()")
    end = DASHBOARD_HTML.index("function setGraphLayer(", start)
    src = DASHBOARD_HTML[start:end]
    ctx_idx = src.index("rGraphContextPanels()")
    stack_idx = src.index("rGraphControlsStack()")
    wrap_idx = src.index("graph-wrap")
    assert ctx_idx < stack_idx < wrap_idx
    between_ctx_stack = src[ctx_idx:stack_idx]
    between_stack_wrap = src[stack_idx:wrap_idx]
    assert "Provenance graph" not in between_ctx_stack
    assert "Provenance graph" not in between_stack_wrap
    assert '<div class="section"' not in between_stack_wrap


def test_graph_controls_stack_markup():
    start = DASHBOARD_HTML.index("function rGraphControlsStack()")
    end = DASHBOARD_HTML.index("function rGraph()", start)
    src = DASHBOARD_HTML[start:end]
    assert "graph-controls-stack" in src
    tabs_idx = src.index("graph-tabs")
    toolbar_idx = src.index("graph-toolbar")
    assert tabs_idx < toolbar_idx
    filters_idx = src.find("dash-filters")
    if filters_idx >= 0:
        assert filters_idx < tabs_idx


def test_graph_context_panels_above_controls():
    rgraph_start = DASHBOARD_HTML.index("function rGraph()")
    rgraph_end = DASHBOARD_HTML.index("function setGraphLayer(", rgraph_start)
    rgraph_src = DASHBOARD_HTML[rgraph_start:rgraph_end]
    assert rgraph_src.index("rGraphContextPanels()") < rgraph_src.index(
        "rGraphControlsStack()"
    )
    ctx_start = DASHBOARD_HTML.index("function rGraphContextPanels()")
    ctx_end = DASHBOARD_HTML.index("function rGraphControlsStack()", ctx_start)
    ctx_src = DASHBOARD_HTML[ctx_start:ctx_end]
    assert ctx_src.index("rGraphPipeline()") < ctx_src.index("rDashUntracked()")
    pipe_start = DASHBOARD_HTML.index("function rGraphPipeline()")
    pipe_end = DASHBOARD_HTML.index("function rGraphContextPanels()", pipe_start)
    untr_start = DASHBOARD_HTML.index("function rDashUntracked()")
    untr_end = DASHBOARD_HTML.index("function rDashThinLinks()", untr_start)
    assert "agentic-loop-host" in DASHBOARD_HTML[pipe_start:pipe_end]
    assert "Untracked code" in DASHBOARD_HTML[untr_start:untr_end]


def test_graph_controls_stack_css():
    css_start = DASHBOARD_HTML.index("<style>")
    css_end = DASHBOARD_HTML.index("</style>", css_start)
    css = DASHBOARD_HTML[css_start:css_end]
    assert ".graph-controls-stack" in css
    assert "flex-direction:column" in css
    assert ".graph-controls-stack .dash-filters" in css
    assert "margin-bottom:0" in css


def test_untracked_summary_opens_panel():
    start = DASHBOARD_HTML.index("function rDashSummary()")
    end = DASHBOARD_HTML.index("function rDashMatrix()", start)
    src = DASHBOARD_HTML[start:end]
    assert "openUntrackedPanel()" in src
    assert 'id="dash-untracked-panel"' in DASHBOARD_HTML


_DASHBOARD_HTML_SHA256 = (
    "085332bd7f3361f1699e2e799ed009d91368de02f3eb327bb2e06526af537070"
)
_UI_PACKAGE = Path(__file__).resolve().parents[1] / "repo_scan" / "hub" / "ui"
_UI_LINE_CAP = 300


def test_ui_package_modules_under_line_cap():
    for path in sorted(_UI_PACKAGE.glob("*.py")):
        lines = path.read_text().splitlines()
        assert len(lines) <= _UI_LINE_CAP, f"{path.name} has {len(lines)} lines"


def test_dashboard_html_byte_parity():
    digest = hashlib.sha256(DASHBOARD_HTML.encode()).hexdigest()
    assert digest == _DASHBOARD_HTML_SHA256


def test_dashboard_contract_marker_placement():
    assert "/* __HUB_CONTRACT__ */" not in DASHBOARD_HTML
    block = js_contract_block()
    render_idx = DASHBOARD_HTML.index("function render(")
    filter_idx = DASHBOARD_HTML.index("function filterOpenTickets")
    block_idx = DASHBOARD_HTML.index(block)
    assert render_idx < block_idx < filter_idx
