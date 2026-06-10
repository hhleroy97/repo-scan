"""Gate drawer enrichment for hub /api/state."""

from pathlib import Path

from repo_scan.config import DEFAULT_CONFIG
from repo_scan.hub.gate_drawer import enrich_gate
from repo_scan.hub.server import build_state
from repo_scan.radar.gates import write_pending
from repo_scan.tickets import write_ticket


def test_enrich_gate_drawer_spec_excerpt_and_criteria(tmp_repo):
    cfg = DEFAULT_CONFIG
    specs = tmp_repo / "docs" / "specs"
    specs.mkdir(parents=True, exist_ok=True)
    spec_body = "\n".join(f"line {i}" for i in range(50))
    (specs / "demo-spec.md").write_text(
        '---\ntype: "spec"\n'
        'analysis: "[[2026-01-01-demo-analysis]]"\n'
        'drafted_at: "2020-01-01 00:00 UTC"\n---\n\n' + spec_body)
    analysis = tmp_repo / "docs" / "research" / "analysis"
    analysis.mkdir(parents=True, exist_ok=True)
    (analysis / "2026-01-01-demo-analysis.md").write_text("# Analysis\nok")

    write_ticket(tmp_repo, cfg, {
        "id": "tkt-0042", "title": "Demo", "fingerprint": "x:42",
        "why": "w", "criteria": ["exports csv", "handles utf-8"],
    })

    gate = {
        "gate": "post_audit",
        "summary": "audit pass — [[demo-spec]] for tkt-0042",
        "problem": "act tkt-0042 — demo-spec",
        "detail": {"doc": "specs/demo-spec.md", "audit_verdict": "pass"},
    }
    tickets = [{"id": "tkt-0042", "criteria": ["exports csv", "handles utf-8"],
                "criteria_checked": [False, False]}]
    enriched = enrich_gate(tmp_repo, cfg, gate, tickets)
    dr = enriched["drawer"]
    assert dr["ticket_id"] == "tkt-0042"
    assert len(dr["criteria"]) == 2
    assert dr["analysis_doc"] == "research/analysis/2026-01-01-demo-analysis.md"
    assert "line 0" in dr["excerpt"] and "line 38" in dr["excerpt"]
    assert "---" not in dr["excerpt"][:10]
    assert dr.get("stale_warning")


def test_build_state_includes_gate_drawer(tmp_repo):
    cfg = DEFAULT_CONFIG
    write_ticket(tmp_repo, cfg, {
        "id": "tkt-0007", "title": "T", "fingerprint": "x:7",
        "why": "w", "criteria": ["done"],
    })
    specs = tmp_repo / "docs" / "specs"
    specs.mkdir(parents=True, exist_ok=True)
    (specs / "t-spec.md").write_text('---\ntype: spec\n---\n\n## Goal\nShip it.\n')
    write_pending(tmp_repo, cfg, "pre_implement", {
        "problem": "act tkt-0007 — t-spec",
        "summary": "implement for tkt-0007",
        "detail": {"doc": "specs/t-spec.md"},
    })
    state = build_state(tmp_repo, cfg)
    assert state["gates"][0]["drawer"]["ticket_id"] == "tkt-0007"
    assert "Ship it" in state["gates"][0]["drawer"]["excerpt"]
