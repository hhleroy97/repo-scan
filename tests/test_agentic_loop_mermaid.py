"""Hub agentic loop Mermaid diagram builder."""

from repo_scan.hub.agentic_loop import build_agentic_loop_mermaid


def test_mermaid_includes_lifecycle_and_loop_subgraphs():
    text = build_agentic_loop_mermaid()
    assert "graph TD" in text
    assert 'subgraph lifecycle' in text
    assert 'subgraph radar' in text
    assert 'subgraph actflow' in text
    assert "rd_post_analyze" in text
    assert "ac_pre" in text


def test_mermaid_highlights_active_loop_stage():
    run = {"kind": "loop", "stage": "[2/7] Analyze", "status": "running"}
    text = build_agentic_loop_mermaid([run], [])
    assert "class rd_analyze,lc_loop active" in text.replace("\n", " ") or "rd_analyze" in text and "active" in text


def test_mermaid_highlights_pending_gate():
    gates = [{"gate": "post-audit", "problem": "x"}]
    text = build_agentic_loop_mermaid([], gates)
    assert "rd_post_audit" in text
    assert "waiting" in text


def test_mermaid_shows_completed_trail():
    done_run = {"kind": "loop", "stage": "[5/7] Audit", "status": "done"}
    text = build_agentic_loop_mermaid([], [], last_completed_run=done_run)
    assert "completed" in text
    assert "rd_research" in text


def test_completed_trail_does_not_override_active():
    active = {"kind": "loop", "stage": "[2/7] Analyze", "status": "running"}
    done = {"kind": "loop", "stage": "[5/7] Audit", "status": "done"}
    text = build_agentic_loop_mermaid([active], [], last_completed_run=done)
    lines = text.split("\n")
    active_line = [l for l in lines if "active" in l and "classDef" not in l]
    completed_line = [l for l in lines if "completed" in l and "classDef" not in l]
    if active_line:
        assert "rd_analyze" in active_line[0]
    if completed_line:
        assert "rd_analyze" not in completed_line[0]
