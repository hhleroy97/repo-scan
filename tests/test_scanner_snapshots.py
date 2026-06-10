"""E2E characterization for repo_scan.scanner (tkt-0002 Phase 1).

Writer artifacts are compared to golden output from test_writers_snapshots
constants (same stubbed inputs). Orchestration-only artifacts use syrupy.
"""

import json
from pathlib import Path

import pytest

import repo_scan
import repo_scan.scanner as scanner
import repo_scan.writers as writers
from repo_scan.utils import ensure_dirs
from tests.conftest import PREV_SUMMARY_FOR_DELTA, _git, freeze_writers_metadata
from tests.test_writers_snapshots import (
    BEHAVIOR,
    CFG,
    CHURN,
    COMPLEXITY,
    COUPLING,
    C_MERMAID,
    LANGUAGES,
    LINE_COUNTS,
    PY_MERMAID,
    RANKING,
    SEAMS,
    TREE,
    TS_MERMAID,
)

PY_EDGES = [("pkg.mod", "pkg.util")]
TS_EDGES = [("src/a.ts", "src/b.ts")]

WRITER_ARTIFACTS = {
    "docs/index.md",
    "docs/scan.json",
    "docs/reports/health.md",
    "docs/reports/coupling.md",
    "docs/reports/dependencies.md",
    "docs/reports/calls.md",
    "docs/architecture/dependency-graph.md",
}


def _build_writers_golden(repo: Path, cfg: dict) -> dict[str, str]:
    """Canonical writer output for the shared fixture constants."""
    from tests.test_writers_snapshots import DELTA

    ranking = [dict(r) for r in RANKING]
    writers.write_health_report(repo, cfg, LINE_COUNTS, CHURN, COMPLEXITY, behavior=BEHAVIOR)
    writers.write_coupling_report(repo, cfg, COUPLING, SEAMS)
    writers.write_dep_report(repo, cfg, TS_MERMAID, PY_MERMAID)
    writers.write_call_report(repo, cfg, C_MERMAID)
    writers.write_index(repo, cfg, LINE_COUNTS, LANGUAGES, ranking, TREE, delta=DELTA)
    writers.write_scan_json(repo, cfg, LINE_COUNTS, LANGUAGES, CHURN, COMPLEXITY, ranking,
                            py_edges=PY_EDGES, ts_edges=TS_EDGES, behavior=BEHAVIOR)
    return {rel: (repo / rel).read_text() for rel in WRITER_ARTIFACTS}


def _capture_writers_golden(repo: Path, cfg: dict) -> dict[str, str]:
    """Write golden artifacts to repo and return their contents."""
    golden = _build_writers_golden(repo, cfg)
    return golden


def _stub_scanner_pipeline(monkeypatch, *, cfg: dict | None = None,
                           prev_summary: dict | None = PREV_SUMMARY_FOR_DELTA) -> dict:
    """Return cfg used for scan after patching scanner upstream helpers."""
    scan_cfg = dict(CFG if cfg is None else cfg)

    monkeypatch.setattr(scanner, "detect_languages",
                        lambda root, c: {
                            "py": [root / p for p in LANGUAGES["py"]],
                            "ts": [],
                            "c": [],
                        })
    monkeypatch.setattr(scanner, "get_line_counts", lambda root, c: LINE_COUNTS)
    monkeypatch.setattr(scanner, "get_git_churn", lambda root, c: CHURN)
    monkeypatch.setattr(scanner, "analyze_history", lambda root, c, files: BEHAVIOR)
    monkeypatch.setattr(scanner, "get_complexity", lambda root, py, c: COMPLEXITY)
    monkeypatch.setattr(scanner, "get_ts_dep_edges", lambda root, ts: (list(TS_EDGES), ""))
    monkeypatch.setattr(scanner, "get_python_dep_edges", lambda root, py, c: list(PY_EDGES))
    monkeypatch.setattr(scanner, "get_c_call_graph_mermaid", lambda root, c: C_MERMAID)
    monkeypatch.setattr(scanner, "rank_files", lambda *a, **k: [dict(r) for r in RANKING])
    monkeypatch.setattr(scanner, "get_directory_tree", lambda root, c: TREE)
    monkeypatch.setattr(scanner, "find_tested_files", lambda files: {"src/app.py"})
    monkeypatch.setattr(scanner, "is_test_file", lambda f: f.startswith("tests/"))
    monkeypatch.setattr(scanner, "hidden_seams", lambda coupling, edges: SEAMS)
    monkeypatch.setattr(scanner, "load_previous_summary", lambda root, c: prev_summary)

    def _edges_to_mermaid(edges, scores=None):
        if edges == PY_EDGES:
            return PY_MERMAID
        if edges == TS_EDGES:
            return TS_MERMAID
        from repo_scan.graphs import edges_to_mermaid
        return edges_to_mermaid(edges, scores)

    monkeypatch.setattr(scanner, "edges_to_mermaid", _edges_to_mermaid)
    return scan_cfg


@pytest.fixture
def fixture_repo(tmp_path: Path, monkeypatch) -> Path:
    """Multi-file git tree matching writers snapshot constants."""
    repo = tmp_path / "fixed"
    repo.mkdir()
    (repo / "README.md").write_text("# Fixed\n\nA deterministic fixture repo for writer snapshots.\n")
    (repo / "pyproject.toml").write_text(
        "[project]\nname = \"fixed\"\n\n[project.scripts]\nfixed = \"fixed:main\"\n")
    (repo / "src").mkdir()
    (repo / "src" / "app.py").write_text("def main():\n    pass\n")
    (repo / "src" / "util.py").write_text("def helper():\n    pass\n")
    (repo / "src" / "ok.py").write_text("x = 1\n")
    (repo / "tests").mkdir()
    (repo / "tests" / "test_app.py").write_text("def test_app():\n    pass\n")
    _git(["init", "-q"], repo)
    _git(["config", "user.email", "alice@example.com"], repo)
    _git(["config", "user.name", "Alice"], repo)
    _git(["add", "."], repo)
    _git(["commit", "-qm", "init"], repo)

    ensure_dirs(repo, CFG)
    freeze_writers_metadata(monkeypatch)
    monkeypatch.setattr(writers, "ok", lambda *a, **k: None)
    for mod in (scanner, writers):
        monkeypatch.setattr(mod, "ok", lambda *a, **k: None)
    for name in ("step", "info", "warn", "header"):
        monkeypatch.setattr(scanner, name, lambda *a, **k: None)
    return repo


def _assert_writer_parity(repo: Path, expected: dict[str, str]) -> None:
    for rel in WRITER_ARTIFACTS:
        assert (repo / rel).read_text() == expected[rel], rel


@pytest.mark.parametrize("scan_kwargs", [
    pytest.param({"quiet": True, "include_handoff": False}, id="baseline"),
    pytest.param({"quiet": True, "include_handoff": True}, id="handoff"),
])
def test_scan_writer_artifacts_match_golden(fixture_repo: Path, monkeypatch, scan_kwargs):
    cfg = _stub_scanner_pipeline(monkeypatch, cfg={**CFG, "radar_enabled": False, "tickets_enabled": False})
    (fixture_repo / ".repo-scan.json").write_text(json.dumps(cfg))
    expected = _capture_writers_golden(fixture_repo, cfg)
    repo_scan.scan(fixture_repo, **scan_kwargs)
    _assert_writer_parity(fixture_repo, expected)
    if scan_kwargs["include_handoff"]:
        assert (fixture_repo / "docs" / "HANDOFF.md").exists()


def test_scan_trend_first_run_snapshot(fixture_repo: Path, monkeypatch, snapshot):
    _stub_scanner_pipeline(monkeypatch, prev_summary=None)
    cfg = {**CFG, "tickets_enabled": False, "radar_enabled": False}
    (fixture_repo / ".repo-scan.json").write_text(json.dumps(cfg))
    repo_scan.scan(fixture_repo, quiet=True)
    trend = (fixture_repo / "docs" / "reports" / "trend.md").read_text()
    assert trend == snapshot


def test_scan_radar_writes_candidates(fixture_repo: Path, monkeypatch):
    _stub_scanner_pipeline(monkeypatch)
    cfg = {**CFG, "radar_enabled": True, "tickets_enabled": False}
    (fixture_repo / ".repo-scan.json").write_text(json.dumps(cfg))
    writers.write_candidates(fixture_repo, cfg, CHURN, COMPLEXITY, tested={"src/app.py"})
    expected = (fixture_repo / "docs" / "research" / "candidates.md").read_text()
    repo_scan.scan(fixture_repo, quiet=True)
    assert (fixture_repo / "docs" / "research" / "candidates.md").read_text() == expected


def test_scan_tickets_snapshot(fixture_repo: Path, monkeypatch, snapshot):
    _stub_scanner_pipeline(monkeypatch)
    cfg = {**CFG, "radar_enabled": False, "tickets_enabled": True, "tickets_max_new_per_scan": 3}
    (fixture_repo / ".repo-scan.json").write_text(json.dumps(cfg))
    monkeypatch.setattr("repo_scan.tickets.now_date", lambda: "2026-01-01")
    repo_scan.scan(fixture_repo, quiet=True)
    board = (fixture_repo / "docs" / "tickets" / "board.md").read_text()
    assert board == snapshot


def test_scan_json_schema_guard(fixture_repo: Path, monkeypatch):
    _stub_scanner_pipeline(monkeypatch)
    cfg = {**CFG, "tickets_enabled": False, "radar_enabled": False}
    (fixture_repo / ".repo-scan.json").write_text(json.dumps(cfg))
    repo_scan.scan(fixture_repo, quiet=True)
    payload = json.loads((fixture_repo / "docs" / "scan.json").read_text())
    assert payload["schema_version"] == 1
    assert set(payload) == {
        "schema_version", "generated_at", "repo", "languages", "files", "churn",
        "complexity", "ranking", "dependency_edges", "behavior", "config",
    }
    assert payload["repo"]["name"] == "fixed"
    assert payload["ranking"][0]["file"] == "src/app.py"
