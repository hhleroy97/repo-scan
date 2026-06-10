"""Report pipeline contract: explicit scanner→writers seam via report_pipeline."""

import ast
import subprocess
from pathlib import Path

import pytest

from repo_scan.behavior import analyze_history
from repo_scan.config import DEFAULT_CONFIG
from repo_scan.report_pipeline import ReportPayload, write_scan_reports
from tests.test_scanner_snapshots import PY_EDGES, TS_EDGES
from tests.test_writers_snapshots import (
    BEHAVIOR,
    CHURN,
    COMPLEXITY,
    DELTA,
    LANGUAGES,
    LINE_COUNTS,
    RANKING,
    SEAMS,
    TREE,
)


def _commit(repo: Path, files: dict[str, str], msg: str = "c"):
    for name, content in files.items():
        path = repo / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)
    subprocess.run(["git", "add", "."], cwd=repo, check=True, capture_output=True)
    subprocess.run(
        ["git", "-c", "user.name=t", "-c", "user.email=t@t.com", "commit", "-qm", msg],
        cwd=repo, check=True, capture_output=True,
    )


def test_scanner_imports_report_pipeline_not_writers():
    """Scanner delegates report writes through report_pipeline, not writers.write_*."""
    scanner_path = Path(__file__).resolve().parents[1] / "repo_scan" / "scanner.py"
    tree = ast.parse(scanner_path.read_text())
    import_froms = {
        node.module
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom) and node.module
    }
    writer_fns = {
        alias.name
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom) and node.module == "writers"
        for alias in node.names
    }
    assert "report_pipeline" in import_froms
    assert writer_fns == {"write_candidates"}


def test_write_scan_reports_call_order(monkeypatch, tmp_path: Path):
    """write_scan_reports sequences writers then append_trend_log."""
    calls: list[str] = []

    def _track(name):
        def _fn(*args, **kwargs):
            calls.append(name)
        return _fn

    import repo_scan.report_pipeline as pipeline

    monkeypatch.setattr(pipeline, "write_health_report", _track("health"))
    monkeypatch.setattr(pipeline, "write_coupling_report", _track("coupling"))
    monkeypatch.setattr(pipeline, "write_dep_report", _track("dep"))
    monkeypatch.setattr(pipeline, "write_call_report", _track("call"))
    monkeypatch.setattr(pipeline, "write_index", _track("index"))
    monkeypatch.setattr(pipeline, "write_scan_json", _track("scan_json"))
    monkeypatch.setattr(pipeline, "append_trend_log", _track("trend"))

    payload = ReportPayload(
        line_counts=LINE_COUNTS,
        languages=LANGUAGES,
        churn=CHURN,
        complexity=COMPLEXITY,
        ranking=list(RANKING),
        tree=TREE,
        behavior=BEHAVIOR,
        seams=SEAMS,
        ts_mermaid=None,
        py_mermaid=None,
        ts_reason="no TS/JS files",
        c_mermaid=None,
        py_edges=PY_EDGES,
        ts_edges=TS_EDGES,
        curr_summary={"files": 4},
        delta=DELTA,
    )
    write_scan_reports(tmp_path, dict(DEFAULT_CONFIG), payload)
    assert calls == [
        "health", "coupling", "dep", "call", "index", "scan_json", "trend",
    ]


def test_scanner_writers_degree_below_threshold(tmp_path: Path):
    """After decoupling history, scanner↔writers coupling drops below 50%."""
    repo = tmp_path / "coupling-repo"
    repo.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=repo, check=True, capture_output=True)
    pkg = "repo_scan"
    scanner = f"{pkg}/scanner.py"
    writers = f"{pkg}/writers.py"
    pipeline = f"{pkg}/report_pipeline.py"

    for i in range(5):
        _commit(
            repo,
            {
                scanner: f"# pair {i}\n",
                writers: f"# pair {i}\n",
            },
            f"pair {i}",
        )
    for i in range(3):
        _commit(repo, {writers: f"# writers solo {i}\n"}, f"writers {i}")
    for i in range(6):
        _commit(repo, {scanner: f"# scanner solo {i}\n"}, f"scanner {i}")
    for i in range(2):
        _commit(
            repo,
            {
                scanner: f"# decouple {i}\n",
                pipeline: f"# pipeline {i}\n",
            },
            f"decouple {i}",
        )

    tracked = {scanner, writers, pipeline}
    result = analyze_history(repo, DEFAULT_CONFIG, tracked)
    pair_keys = {frozenset((c["a"], c["b"])) for c in result["coupling"]}
    seam_pair = frozenset((scanner, writers))
    if seam_pair in pair_keys:
        degree = next(
            c["degree"]
            for c in result["coupling"]
            if frozenset((c["a"], c["b"])) == seam_pair
        )
        assert degree < DEFAULT_CONFIG["coupling_min_degree"]
    else:
        assert seam_pair not in pair_keys


def test_cli_gates_degree_below_threshold(tmp_path: Path):
    """After decoupling history, cli↔gates coupling drops below 50%."""
    repo = tmp_path / "cli-gates-repo"
    repo.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=repo, check=True, capture_output=True)
    pkg = "repo_scan/radar"
    cli = f"{pkg}/cli.py"
    gates = f"{pkg}/gates.py"

    for i in range(4):
        _commit(
            repo,
            {
                cli: f"# pair {i}\n",
                gates: f"# pair {i}\n",
            },
            f"pair {i}",
        )
    for i in range(3):
        _commit(repo, {gates: f"# gates solo {i}\n"}, f"gates {i}")
    for i in range(6):
        _commit(repo, {cli: f"# cli solo {i}\n"}, f"cli {i}")

    tracked = {cli, gates}
    result = analyze_history(repo, DEFAULT_CONFIG, tracked)
    pair_keys = {frozenset((c["a"], c["b"])) for c in result["coupling"]}
    seam_pair = frozenset((cli, gates))
    if seam_pair in pair_keys:
        degree = next(
            c["degree"]
            for c in result["coupling"]
            if frozenset((c["a"], c["b"])) == seam_pair
        )
        assert degree < DEFAULT_CONFIG["coupling_min_degree"]
    else:
        assert seam_pair not in pair_keys
