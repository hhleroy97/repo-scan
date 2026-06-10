"""B3: gate modes, pending state, decision trail."""

import json
from pathlib import Path

from repo_scan.config import load_config
from repo_scan.radar.gates import clear_pending, gate, gate_mode, write_pending


def _cfg(tmp_repo: Path, gates: dict | None = None) -> dict:
    cfg = load_config(tmp_repo)
    if gates is not None:
        cfg["gates"] = gates
    return cfg


def test_gate_mode_defaults_and_validation(tmp_repo):
    cfg = _cfg(tmp_repo)
    assert gate_mode("post_analyze", cfg) == "prompt"
    cfg["gates"] = {"post_analyze": "auto", "post_audit": "bogus"}
    assert gate_mode("post_analyze", cfg) == "auto"
    assert gate_mode("post_audit", cfg) == "prompt"  # invalid value falls back


def test_gate_auto_passes_and_records(tmp_repo):
    cfg = _cfg(tmp_repo, {"post_analyze": "auto"})
    assert gate("post_analyze", {"summary": "do the thing"}, cfg, tmp_repo) is True
    decisions = (tmp_repo / "docs" / "research" / "decisions.md").read_text()
    assert "| post_analyze | auto |" in decisions
    assert "do the thing" in decisions


def test_gate_deny_stops(tmp_repo):
    cfg = _cfg(tmp_repo, {"post_audit": "deny"})
    assert gate("post_audit", {"summary": "s"}, cfg, tmp_repo) is False
    decisions = (tmp_repo / "docs" / "research" / "decisions.md").read_text()
    assert "denied (config)" in decisions


def test_gate_prompt_noninteractive_pauses_with_pending_file(tmp_repo):
    cfg = _cfg(tmp_repo)  # prompt mode; pytest stdin is not a tty
    assert gate("post_analyze", {"summary": "needs a human"}, cfg, tmp_repo) is False
    # pending files are keyed by (gate, problem) so parallel runs don't clobber
    pending = next((tmp_repo / "docs" / "research" / "pending").glob("post_analyze*.json"))
    data = json.loads(pending.read_text())
    assert data["gate"] == "post_analyze"
    assert data["payload"]["summary"] == "needs a human"


def test_gate_preapproved_consumes_pending(tmp_repo):
    cfg = _cfg(tmp_repo)
    write_pending(tmp_repo, cfg, "post_analyze", {"summary": "s"})
    assert gate("post_analyze", {"summary": "s"}, cfg, tmp_repo,
                approved={"post_analyze"}) is True
    assert not list((tmp_repo / "docs" / "research" / "pending").glob("post_analyze*.json"))
    decisions = (tmp_repo / "docs" / "research" / "decisions.md").read_text()
    assert "approved (--approve)" in decisions


def test_clear_pending_missing_is_noop(tmp_repo):
    cfg = _cfg(tmp_repo)
    clear_pending(tmp_repo, cfg, "post_audit")  # must not raise
