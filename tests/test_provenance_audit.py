"""Tests for provenance_audit — coverage audit with regression detection."""

import json
from pathlib import Path

from repo_scan.provenance_audit import audit


def _make_repo(tmp_path: Path, coverage_pct: float = 0.3,
               healthy: int = 5, docs: int = 20) -> Path:
    root = tmp_path
    dd = root / "docs"
    dd.mkdir()
    scan = {
        "files": {"repo_scan/foo.py": {"lines": 50}},
        "ranking": [{"file": "repo_scan/foo.py", "pagerank": 0.5}],
        "behavior": {"coupling": [], "age_days": {}},
        "citations": [],
        "vault_health": {
            "coverage_pct": coverage_pct,
            "healthy": healthy,
            "docs": docs,
            "score_histogram": {"0": 0, "1": 5, "2": 10, "3": healthy},
            "orphans_by_kind": {},
            "untracked_code_count": 0,
            "stale_docs_count": 0,
            "knowledge_debt": 20.0,
            "thin_citations": [],
        },
    }
    (dd / "scan.json").write_text(json.dumps(scan))
    (dd / "tickets").mkdir()
    return root


def test_audit_runs_without_error(tmp_path):
    root = _make_repo(tmp_path)
    rc = audit(root, {"docs_dir": "docs"})
    assert rc == 0


def test_audit_regression_detected(tmp_path, capsys):
    root = _make_repo(tmp_path, coverage_pct=0.5, healthy=10)
    rc = audit(root, {"docs_dir": "docs"}, fail_on_regression=True)
    out = capsys.readouterr().out
    # Current live coverage is 0 (no real docs), baseline is 0.5
    assert rc == 1
    assert "regression" in out.lower()


def test_audit_no_regression_when_equal(tmp_path):
    root = _make_repo(tmp_path, coverage_pct=0.0, healthy=0)
    rc = audit(root, {"docs_dir": "docs"}, fail_on_regression=True)
    assert rc == 0
