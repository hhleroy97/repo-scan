"""B2: LLM CLI backend, JSON extraction, summarize, radar research (offline)."""

import json
import sys
from pathlib import Path

import pytest

from repo_scan.config import load_config
from repo_scan.radar.llm import LLMError, complete, complete_json, extract_json, summarize_source
from repo_scan.radar.research import cmd_research, repo_context_snippet, run_research
from repo_scan.radar.sources import Source

FAKE_LLM = f"{sys.executable} {Path(__file__).parent / 'fake_llm.py'}"


@pytest.fixture
def llm_cfg(tmp_repo):
    cfg = load_config(tmp_repo)
    cfg["llm_cli"] = [FAKE_LLM]
    return cfg


def test_complete_uses_configured_cli(llm_cfg, monkeypatch):
    monkeypatch.setenv("RADAR_FAKE_RESPONSE", "hello from fake")
    assert complete("prompt", llm_cfg) == "hello from fake"


def test_complete_strips_embedded_null_bytes(llm_cfg, monkeypatch):
    """NUL in prompt must not crash subprocess.Popen (POSIX argv restriction)."""
    monkeypatch.setenv("RADAR_FAKE_RESPONSE", "ok")
    assert complete("before\x00after", llm_cfg) == "ok"


def test_complete_raises_when_no_backend(tmp_repo):
    cfg = load_config(tmp_repo)
    cfg["llm_cli"] = ["definitely-not-a-real-cli-xyz"]
    with pytest.raises(LLMError, match="no LLM CLI"):
        complete("prompt", cfg)


def test_complete_raises_on_nonzero_exit(llm_cfg, monkeypatch):
    monkeypatch.delenv("RADAR_FAKE_RESPONSE", raising=False)
    monkeypatch.delenv("RADAR_FAKE_RESPONSES_DIR", raising=False)
    with pytest.raises(LLMError, match="exited 1"):
        complete("prompt", llm_cfg)


def test_extract_json_variants():
    assert extract_json('{"a": 1}') == {"a": 1}
    assert extract_json('prose before {"a": 1} prose after') == {"a": 1}
    assert extract_json('```json\n{"a": 1}\n```') == {"a": 1}
    with pytest.raises(LLMError):
        extract_json("no json here")


def test_complete_json(llm_cfg, monkeypatch):
    monkeypatch.setenv("RADAR_FAKE_RESPONSE", 'Sure! ```json\n{"x": 2}\n```')
    assert complete_json("prompt", llm_cfg) == {"x": 2}


def test_summarize_source(llm_cfg, monkeypatch):
    monkeypatch.setenv("RADAR_FAKE_RESPONSE", json.dumps({
        "summary": "A paper about agent loops.",
        "key_claims": ["loops work", "gates matter"],
        "tags": ["agents", "paper"],
        "relevance": "applies to radar",
    }))
    src = Source(id="arxiv-1", type="arxiv", url="u", title="T", tags=["paper"])
    src = summarize_source(src, "content", llm_cfg)
    assert src.summary == "A paper about agent loops."
    assert src.key_claims == ["loops work", "gates matter"]
    assert src.tags == ["agents", "paper"]
    assert src.relevance == "applies to radar"


def test_repo_context_snippet_without_scan(tmp_repo):
    cfg = load_config(tmp_repo)
    assert "no scan.json" in repo_context_snippet(tmp_repo, cfg)


def test_run_research_ingests_proposed_file(tmp_repo, llm_cfg, monkeypatch):
    note = tmp_repo / "design-note.md"
    note.write_text("# Design\nUse file-backed gates.\n")
    monkeypatch.setenv("RADAR_FAKE_RESPONSE", json.dumps({
        "sources": [{"ref": f"file:{note}", "why": "local design note"}],
        "notes": "use the local note",
    }))

    result = run_research(tmp_repo, llm_cfg, "how should gates work?", max_sources=2)
    assert len(result["ingested"]) == 1
    assert result["ingested"][0]["id"] == "file-design-note"
    assert result["failed"] == []

    source_file = tmp_repo / "docs" / "research" / "sources" / "file-design-note.md"
    assert source_file.exists()
    # summarize_source got the same fake response (no key_claims key) — summary survives
    assert "relevance: " in source_file.read_text()
    index = (tmp_repo / "docs" / "research" / "index.md").read_text()
    assert "file-design-note" in index


def test_run_research_records_failures(tmp_repo, llm_cfg, monkeypatch):
    monkeypatch.setenv("RADAR_FAKE_RESPONSE", json.dumps({
        "sources": [{"ref": "file:/nonexistent/nope.md", "why": "bad"}],
        "notes": "",
    }))
    result = run_research(tmp_repo, llm_cfg, "q", max_sources=1)
    assert result["ingested"] == []
    assert len(result["failed"]) == 1


def test_cmd_research_writes_run_log(tmp_repo, llm_cfg, monkeypatch):
    note = tmp_repo / "n.md"
    note.write_text("# N\ncontent here\n")
    monkeypatch.setenv("RADAR_FAKE_RESPONSE", json.dumps({
        "sources": [{"ref": f"file:{note}", "why": "w"}],
        "notes": "strategy",
    }))
    rc = cmd_research(tmp_repo, llm_cfg, "what about gates?", max_sources=1)
    assert rc == 0
    runs = list((tmp_repo / "docs" / "research" / "runs").glob("*.md"))
    assert len(runs) == 1
    log = runs[0].read_text()
    assert "what about gates?" in log
    assert "file-n" in log


def test_cmd_research_fails_without_backend(tmp_repo):
    cfg = load_config(tmp_repo)
    cfg["llm_cli"] = ["definitely-not-a-real-cli-xyz"]
    assert cmd_research(tmp_repo, cfg, "q") == 1
