"""Unit tests for scanner helpers (tkt-0002 Phase 1)."""

from pathlib import Path

import pytest

import repo_scan.writers as writers
from repo_scan.config import DEFAULT_CONFIG
from repo_scan.scanner import collect_digest_inputs, ranking_node_scores, run_digest
from tests.conftest import freeze_writers_metadata
from tests.test_writers_snapshots import COMPLEXITY, LINE_COUNTS, RANKING, TREE


def test_ranking_node_scores_maps_python_modules():
    scores = ranking_node_scores(RANKING)
    assert scores["src/app.py"] == pytest.approx(0.41)
    assert scores["src.app"] == pytest.approx(0.41)
    assert scores["src/util.py"] == pytest.approx(0.18)
    assert scores["src.util"] == pytest.approx(0.18)


def test_collect_digest_inputs_keys_match_run_digest_inputs(monkeypatch, tmp_path: Path):
    repo = tmp_path / "digest-repo"
    repo.mkdir()
    (repo / "main.py").write_text("x = 1\n")

    import repo_scan.scanner as scanner

    stub = {
        "line_counts": LINE_COUNTS,
        "languages": {"py": ["src/a.py"], "ts": [], "c": []},
        "churn": [],
        "complexity": COMPLEXITY,
        "ranking": RANKING,
        "tree": TREE,
    }
    monkeypatch.setattr(scanner, "detect_languages", lambda root, cfg: stub["languages"])
    monkeypatch.setattr(scanner, "get_line_counts", lambda root, cfg: stub["line_counts"])
    monkeypatch.setattr(scanner, "get_git_churn", lambda root, cfg: stub["churn"])
    monkeypatch.setattr(scanner, "get_complexity", lambda root, py, cfg: stub["complexity"])
    monkeypatch.setattr(scanner, "get_python_dep_edges", lambda root, py, cfg: [])
    monkeypatch.setattr(scanner, "get_ts_dep_edges", lambda root, ts: ([], "no TS/JS files"))
    monkeypatch.setattr(scanner, "rank_files", lambda *a, **k: list(RANKING))
    monkeypatch.setattr(scanner, "get_directory_tree", lambda root, cfg: stub["tree"])

    collected = collect_digest_inputs(repo, dict(DEFAULT_CONFIG))
    assert set(collected) == set(stub)
    for key in stub:
        assert collected[key] == stub[key]


def test_run_digest_writes_expected_path(monkeypatch, tmp_path: Path, snapshot):
    repo = tmp_path / "fixed"
    repo.mkdir()
    (repo / "README.md").write_text("# Fixed\n")
    freeze_writers_metadata(monkeypatch)
    monkeypatch.setattr(writers, "ok", lambda *a, **k: None)

    import repo_scan.scanner as scanner

    monkeypatch.setattr(scanner, "collect_digest_inputs", lambda root, cfg: {
        "line_counts": LINE_COUNTS,
        "languages": {"py": ["src/app.py"], "ts": [], "c": []},
        "churn": [],
        "complexity": COMPLEXITY,
        "ranking": RANKING,
        "tree": TREE,
    })
    import repo_scan.digest as digest

    monkeypatch.setattr("repo_scan.identity.readme_summary", lambda root, max_chars=280: "Fixture readme.")
    monkeypatch.setattr(digest, "now_iso", lambda: "2026-01-01 00:00 UTC")
    monkeypatch.setattr(digest, "git_branch", lambda root: "main")
    monkeypatch.setattr(digest, "git_last_commit", lambda root: "abc1234 fixed commit")
    monkeypatch.setattr(digest, "git_remote_url", lambda root: "https://example.com/repo.git")

    path = run_digest(repo)
    assert path == repo / "docs" / "digest.md"
    assert path.read_text() == snapshot
