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
    """Controls → canvas → context panels: no collapsibles between controls and canvas."""
    start = DASHBOARD_HTML.index("function rGraph()")
    end = DASHBOARD_HTML.index("function setGraphLayer(", start)
    src = DASHBOARD_HTML[start:end]
    stack_idx = src.index("rGraphControlsStack()")
    canvas_idx = src.index("rGraphCanvas()")
    ctx_idx = src.index("rGraphContextPanels()")
    assert stack_idx < canvas_idx < ctx_idx
    between_stack_canvas = src[stack_idx:canvas_idx]
    assert "rGraphPipeline" not in between_stack_canvas
    assert "rDashUntracked" not in between_stack_canvas


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


def test_graph_context_panels_below_canvas():
    """Context panels (loop, untracked, tools) render after the canvas."""
    rgraph_start = DASHBOARD_HTML.index("function rGraph()")
    rgraph_end = DASHBOARD_HTML.index("function setGraphLayer(", rgraph_start)
    rgraph_src = DASHBOARD_HTML[rgraph_start:rgraph_end]
    assert rgraph_src.index("rGraphControlsStack()") < rgraph_src.index(
        "rGraphCanvas()"
    )
    assert rgraph_src.index("rGraphCanvas()") < rgraph_src.index(
        "rGraphContextPanels()"
    )
    ctx_start = DASHBOARD_HTML.index("function rGraphContextPanels()")
    ctx_end = DASHBOARD_HTML.index("function rGraph()", ctx_start)
    ctx_src = DASHBOARD_HTML[ctx_start:ctx_end]
    assert "rGraphPipeline()" in ctx_src
    assert "rDashUntracked()" in ctx_src
    assert "rDashProvenanceTools()" in ctx_src


def test_provenance_tools_panel_rendered():
    """Provenance tools panel includes lint, auto-link, and audit actions."""
    start = DASHBOARD_HTML.index("function rDashProvenanceTools()")
    end = DASHBOARD_HTML.index("async function runProvenanceLint(", start)
    src = DASHBOARD_HTML[start:end]
    assert "Provenance tools" in src
    assert "Lint vault links" in src
    assert "Auto-link orphans" in src
    assert "radar audit-provenance" in src
    assert "API_PROVENANCE_LINT" in DASHBOARD_HTML
    assert "API_PROVENANCE_AUTOLINK" in DASHBOARD_HTML


def test_graph_guide_rendered():
    """Graph guide explains signals, edges, layers, and interaction."""
    start = DASHBOARD_HTML.index("function rGraphGuide()")
    end = DASHBOARD_HTML.index("function rGraphDashboard()", start)
    src = DASHBOARD_HTML[start:end]
    assert "How to read this graph" in src
    assert "Evidence" in src
    assert "Linked" in src
    assert "Cited" in src
    assert "Closed loop" in src
    assert "Layer filters" in src
    assert "provenance chain" in src


def test_additional_views_all_nine():
    """All 9 additional view functions exist and are composed together."""
    view_fns = [
        "rViewDirCoverage", "rViewProvenanceFlow", "rViewGovernanceRisk",
        "rViewCitationDensity", "rViewStaleQueue", "rViewCompletenessRadar",
        "rViewOrphanCluster", "rViewChangeImpact", "rViewProvenanceTimeline",
    ]
    for fn in view_fns:
        assert f"function {fn}()" in DASHBOARD_HTML, f"missing {fn}"
    composite = DASHBOARD_HTML[
        DASHBOARD_HTML.index("function rGraphAdditionalViews()"):
        DASHBOARD_HTML.index("function rGraphAdditionalViews()") + 500
    ]
    for fn in view_fns:
        assert fn in composite, f"{fn} not in rGraphAdditionalViews"


def test_additional_views_in_context_panels():
    """Additional views are rendered inside context panels."""
    ctx_start = DASHBOARD_HTML.index("function rGraphContextPanels()")
    ctx_end = DASHBOARD_HTML.index("function rGraph()", ctx_start)
    ctx_src = DASHBOARD_HTML[ctx_start:ctx_end]
    assert "rGraphAdditionalViews()" in ctx_src


def test_view_dir_coverage_content():
    """Directory coverage view shows tracked/total language."""
    start = DASHBOARD_HTML.index("function rViewDirCoverage()")
    end = DASHBOARD_HTML.index("function rViewProvenanceFlow()", start)
    src = DASHBOARD_HTML[start:end]
    assert "Coverage by directory" in src
    assert "dir_coverage" in src


def test_view_completeness_radar_content():
    """Radar chart renders SVG with 4 signal axes."""
    start = DASHBOARD_HTML.index("function rViewCompletenessRadar()")
    end = DASHBOARD_HTML.index("function setOrphanView(", start)
    src = DASHBOARD_HTML[start:end]
    assert "signal_matrix" in src
    assert "<svg" in src
    assert "polygon" in src


def test_view_change_impact_api():
    """Change impact view references the provenance impact API."""
    assert "API_PROVENANCE_IMPACT" in DASHBOARD_HTML
    start = DASHBOARD_HTML.index("function rViewChangeImpact()")
    end = DASHBOARD_HTML.index("async function loadChangeImpact(", start)
    src = DASHBOARD_HTML[start:end]
    assert "Change impact" in src


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
    "a19dc83cb66214bb6d863cbeca4ef78e2a4e8256356322cde45270d428101280"
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


def test_force_tuning_controls():
    """Force tuning panel has sliders, edge toggles, freeze, and reset."""
    assert "gf-tuning" in DASHBOARD_HTML
    assert "Force tuning" in DASHBOARD_HTML
    for param in ("gfRepulsion", "gfSpring", "gfGravity", "gfDamping", "gfIterations"):
        assert param in DASHBOARD_HTML, f"{param} missing"
    assert "gfNodeScale" in DASHBOARD_HTML
    assert "gfLabelThreshold" in DASHBOARD_HTML
    assert "function gfSet(" in DASHBOARD_HTML
    assert "function gfToggleEdge(" in DASHBOARD_HTML
    assert "function gfToggleFrozen()" in DASHBOARD_HTML
    assert "function gfResetDefaults()" in DASHBOARD_HTML
    assert "gf-slider" in DASHBOARD_HTML
    assert "gfShowEdges" in DASHBOARD_HTML
    assert "Freeze" in DASHBOARD_HTML


def test_force_tuning_css():
    css_start = DASHBOARD_HTML.index("<style>")
    css_end = DASHBOARD_HTML.index("</style>", css_start)
    css = DASHBOARD_HTML[css_start:css_end]
    for cls in (".gf-tuning", ".gf-summary", ".gf-grid", ".gf-row",
                ".gf-slider", ".gf-val", ".gf-edge-row", ".gf-check"):
        assert cls in css, f"{cls} missing from CSS"


def test_dashboard_contract_marker_placement():
    assert "/* __HUB_CONTRACT__ */" not in DASHBOARD_HTML
    block = js_contract_block()
    render_idx = DASHBOARD_HTML.index("function render(")
    filter_idx = DASHBOARD_HTML.index("function filterOpenTickets")
    block_idx = DASHBOARD_HTML.index(block)
    assert render_idx < block_idx < filter_idx
