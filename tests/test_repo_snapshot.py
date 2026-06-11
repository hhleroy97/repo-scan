"""repo_snapshot() — ranked map for RADAR LLM prompts."""

import json

from repo_scan.config import DEFAULT_CONFIG
from repo_scan.radar.pipeline import run_analyze
from repo_scan.radar.research import (repo_context_snippet, repo_snapshot,
                                      repo_snapshot_digest)
from repo_scan.tickets import write_ticket


def _write_scan(repo, ranking=None, **extra):
    docs = repo / "docs"
    docs.mkdir(exist_ok=True)
    payload = {
        "schema_version": 1,
        "generated_at": "2026-06-10 12:00 UTC",
        "repo": {"name": repo.name, "branch": "main"},
        "languages": {"py": 3},
        "ranking": ranking or [
            {"file": "app.py", "lines": 120, "complexity": 9,
             "tested": True, "commits": 4, "score": 30},
            {"file": "lib.py", "lines": 80, "complexity": 3,
             "tested": False, "commits": 0, "score": 10},
        ],
        "churn": [{"file": "app.py", "commits": 4}],
        "behavior": {"coupling": [{"a": "app.py", "b": "lib.py",
                                   "shared": 3, "degree": 55}]},
        **extra,
    }
    (docs / "scan.json").write_text(json.dumps(payload))


def test_snapshot_includes_ranking_and_tickets(tmp_repo):
    cfg = DEFAULT_CONFIG.copy()
    _write_scan(tmp_repo)
    write_ticket(tmp_repo, cfg, {
        "id": "tkt-0001", "title": "Refactor app.py", "status": "proposed",
        "fingerprint": "refactor:app.py", "why": "hot", "criteria": ["tests pass"],
    })
    snap = repo_snapshot(tmp_repo, cfg)
    assert "Repo snapshot" in snap
    assert "app.py" in snap and "rank #1" in snap
    assert "tkt-0001" in snap and "Refactor app.py" in snap


def test_snapshot_digest_stable_for_same_scan(tmp_repo):
    cfg = DEFAULT_CONFIG.copy()
    _write_scan(tmp_repo)
    d1 = repo_snapshot_digest(tmp_repo, cfg)
    d2 = repo_snapshot_digest(tmp_repo, cfg)
    assert d1 == d2 and len(d1) == 16


def test_snapshot_degrades_without_scan_json(tmp_repo):
    cfg = DEFAULT_CONFIG.copy()
    text = repo_context_snippet(tmp_repo, cfg)
    assert "no scan.json" in text


def test_analyze_prompt_receives_snapshot(tmp_repo, monkeypatch):
    cfg = DEFAULT_CONFIG.copy()
    _write_scan(tmp_repo)
    captured = {}

    def fake_complete_json(prompt, *args, **kwargs):
        captured["prompt"] = prompt
        return {"findings": ["f"], "recommendation": "r",
                "confidence": "high", "risks": []}

    monkeypatch.setattr("repo_scan.radar.pipeline.complete_json", fake_complete_json)
    run_analyze(tmp_repo, cfg, "how to test?", [])
    assert "Repo snapshot" in captured["prompt"]
    assert "app.py" in captured["prompt"]
