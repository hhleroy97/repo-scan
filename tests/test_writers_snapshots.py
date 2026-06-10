"""Characterization snapshots for every writer artifact (tkt-0001 Phase 1).

Golden files pin the exact markdown/JSON each write_* produces from fixed
inputs, with volatile metadata (timestamps, git) stubbed. Any refactor of
writers.py must keep these snapshots byte-identical. Update intentionally
with `pytest --snapshot-update`.
"""

import json
from pathlib import Path

import pytest

import repo_scan.writers as writers
from repo_scan.config import DEFAULT_CONFIG
from repo_scan.utils import ensure_dirs

CFG = dict(DEFAULT_CONFIG)

LINE_COUNTS = {
    "src/app.py": {"lines": 700, "bytes": 21000},
    "src/util.py": {"lines": 350, "bytes": 10500},
    "src/ok.py": {"lines": 50, "bytes": 1500},
    "tests/test_app.py": {"lines": 80, "bytes": 2400},
}
LANGUAGES = {"py": ["src/app.py", "src/util.py", "src/ok.py", "tests/test_app.py"],
             "ts": [], "c": []}
CHURN = [{"file": "src/app.py", "commits": 12}, {"file": "src/util.py", "commits": 4}]
COMPLEXITY = [
    {"file": "src/app.py", "name": "main", "rank": "D", "complexity": 24, "lineno": 10},
    {"file": "src/util.py", "name": "helper", "rank": "C", "complexity": 12, "lineno": 5},
]
RANKING = [
    {"file": "src/app.py", "score": 80.0, "pagerank": 0.41, "imported_by": 2,
     "commits": 12, "complexity": 24, "lines": 700, "tested": True},
    {"file": "src/util.py", "score": 40.5, "pagerank": 0.18, "imported_by": 1,
     "commits": 4, "complexity": 12, "lines": 350, "tested": False},
]
BEHAVIOR = {
    "coupling": [{"a": "src/app.py", "b": "src/util.py", "shared": 4, "degree": 67}],
    "ownership": [
        {"file": "src/app.py", "commits": 12, "authors": 1,
         "top_author": "alice@example.com", "top_share": 1.0},
        {"file": "src/util.py", "commits": 4, "authors": 2,
         "top_author": "bob@example.com", "top_share": 0.75},
    ],
    "age_days": {"src/app.py": 3, "src/util.py": 200},
}
COUPLING = BEHAVIOR["coupling"]
SEAMS = [{"a": "src/app.py", "b": "src/util.py", "shared": 4, "degree": 67}]
DELTA = {"since": "2025-12-31 00:00 UTC", "lines": 120, "files": 1,
         "hotspot_functions": 1, "critical_files": 0,
         "cc_movers": [("src/app.py", 6)]}
TREE = "src/\n  app.py\n  util.py\n  ok.py\ntests/\n  test_app.py"
TS_MERMAID = 'graph TD\n  src_a["a"] --> src_b["b"]'
PY_MERMAID = 'graph TD\n  pkg_mod["mod"] --> pkg_util["util"]'
C_MERMAID = 'graph TD\n  main --> helper'


@pytest.fixture
def fixture_repo(tmp_path: Path, monkeypatch) -> Path:
    """Deterministic repo + frozen time/git so artifacts are byte-stable."""
    repo = tmp_path / "fixed"
    repo.mkdir()
    (repo / "README.md").write_text("# Fixed\n\nA deterministic fixture repo for writer snapshots.\n")
    (repo / "pyproject.toml").write_text(
        "[project]\nname = \"fixed\"\n\n[project.scripts]\nfixed = \"fixed:main\"\n")
    ensure_dirs(repo, CFG)
    monkeypatch.setattr(writers, "now_iso", lambda: "2026-01-01 00:00 UTC")
    monkeypatch.setattr(writers, "git_branch", lambda root: "main")
    monkeypatch.setattr(writers, "git_last_commit", lambda root: "abc1234 fixed commit")
    monkeypatch.setattr(writers, "git_remote_url", lambda root: "https://example.com/repo.git")
    monkeypatch.setattr(writers, "ok", lambda *a, **k: None)
    return repo


def test_health_report_snapshot(fixture_repo: Path, snapshot):
    writers.write_health_report(fixture_repo, CFG, LINE_COUNTS, CHURN, COMPLEXITY,
                                behavior=BEHAVIOR)
    assert (fixture_repo / "docs" / "reports" / "health.md").read_text() == snapshot


def test_index_snapshot(fixture_repo: Path, snapshot):
    writers.write_index(fixture_repo, CFG, LINE_COUNTS, LANGUAGES, RANKING, TREE,
                        delta=DELTA)
    assert (fixture_repo / "docs" / "index.md").read_text() == snapshot


def test_coupling_report_snapshot(fixture_repo: Path, snapshot):
    writers.write_coupling_report(fixture_repo, CFG, COUPLING, SEAMS,
                                  py_edges=[("pkg.mod", "pkg.util")],
                                  ts_edges=[], line_counts=LINE_COUNTS)
    assert (fixture_repo / "docs" / "reports" / "coupling.md").read_text() == snapshot


def test_dep_report_snapshot(fixture_repo: Path, snapshot):
    writers.write_dep_report(fixture_repo, CFG, TS_MERMAID, PY_MERMAID)
    assert (fixture_repo / "docs" / "reports" / "dependencies.md").read_text() == snapshot
    assert (fixture_repo / "docs" / "architecture" / "dependency-graph.md").read_text() \
        == (fixture_repo / "docs" / "reports" / "dependencies.md").read_text()


def test_call_report_snapshot(fixture_repo: Path, snapshot):
    writers.write_call_report(fixture_repo, CFG, C_MERMAID)
    assert (fixture_repo / "docs" / "reports" / "calls.md").read_text() == snapshot


def test_candidates_snapshot(fixture_repo: Path, snapshot):
    writers.write_candidates(fixture_repo, CFG, CHURN, COMPLEXITY,
                             tested={"src/app.py"})
    assert (fixture_repo / "docs" / "research" / "candidates.md").read_text() == snapshot


def test_scan_json_snapshot(fixture_repo: Path, snapshot):
    writers.write_scan_json(fixture_repo, CFG, LINE_COUNTS, LANGUAGES, CHURN,
                            COMPLEXITY, RANKING,
                            py_edges=[("pkg.mod", "pkg.util")],
                            ts_edges=[("src/a.ts", "src/b.ts")],
                            behavior=BEHAVIOR)
    raw = (fixture_repo / "docs" / "scan.json").read_text()
    payload = json.loads(raw)
    # schema guard separate from the golden file, per audit feedback:
    # intentional schema bumps must be explicit, not hidden in snapshot churn
    assert payload["schema_version"] == 1
    assert set(payload) == {
        "schema_version", "generated_at", "repo", "languages", "files", "churn",
        "complexity", "ranking", "dependency_edges", "behavior", "config",
        "citations", "vault_health",
    }
    assert raw == snapshot
