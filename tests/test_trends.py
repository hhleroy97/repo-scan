"""Scan-over-scan deltas: the verify half of the reflexion loop."""

from pathlib import Path

import repo_scan
from repo_scan.config import DEFAULT_CONFIG
from repo_scan.trends import (
    compute_delta,
    load_previous_summary,
    summarize_metrics,
    trend_callout,
)


def _counts(**files):
    return {name: {"lines": lines, "bytes": lines * 30} for name, lines in files.items()}


def _cc(file, score):
    return {"file": file, "name": "fn", "rank": "C", "complexity": score, "lineno": 1}


def test_summarize_metrics():
    s = summarize_metrics(_counts(a=100, b=700), [_cc("a", 12), _cc("a", 5)], DEFAULT_CONFIG)
    assert s["files"] == 2
    assert s["lines"] == 800
    assert s["hotspot_functions"] == 2
    assert s["critical_files"] == 1
    assert s["cc_by_file"] == {"a": 17}


def test_summarize_metrics_includes_vault_health():
    s = summarize_metrics(_counts(a=10), [], DEFAULT_CONFIG, vault_health={
        "coverage_pct": 0.75,
        "untracked_code_count": 3,
    })
    assert s["vault_coverage_pct"] == 0.75
    assert s["untracked_code_count"] == 3


def test_compute_delta_vault_metrics():
    base = {"lines": 0, "files": 0, "hotspot_functions": 0,
            "critical_files": 0, "cc_by_file": {}}
    prev = {**base, "vault_coverage_pct": 0.5, "untracked_code_count": 10}
    curr = {**base, "vault_coverage_pct": 0.75, "untracked_code_count": 7}
    delta = compute_delta(prev, curr)
    assert delta["vault_coverage_pct"] == 0.25
    assert delta["untracked_code_count"] == -3


def test_compute_delta_and_movers():
    prev = summarize_metrics(_counts(a=100), [_cc("a", 12)], DEFAULT_CONFIG)
    prev["generated_at"] = "yesterday"
    curr = summarize_metrics(_counts(a=150, b=50), [_cc("a", 20), _cc("b", 11)], DEFAULT_CONFIG)
    delta = compute_delta(prev, curr)
    assert delta["lines"] == 100
    assert delta["files"] == 1
    assert delta["hotspot_functions"] == 1
    assert ("b", 11) in delta["cc_movers"]
    assert ("a", 8) in delta["cc_movers"]
    assert compute_delta(None, curr) is None


def test_trend_callout_kinds():
    assert trend_callout(None) == []
    base = {"since": "t", "lines": 0, "files": 0, "hotspot_functions": 0,
            "critical_files": 0, "cc_movers": []}
    assert "[!tip] No metric changes" in trend_callout(base)[0]
    worse = dict(base, hotspot_functions=2, cc_movers=[("a.py", 9)])
    text = "\n".join(trend_callout(worse))
    assert "[!warning]" in text
    assert "hotspot functions +2" in text
    assert "`a.py` complexity +9" in text
    better = dict(base, lines=-50, hotspot_functions=-1)
    assert "[!note]" in trend_callout(better)[0]


def test_scan_writes_trend_and_delta_on_second_run(tmp_repo_with_imports: Path):
    repo_scan.scan(tmp_repo_with_imports, quiet=True)
    trend = tmp_repo_with_imports / "docs" / "reports" / "trend.md"
    assert trend.exists()
    first_rows = [l for l in trend.read_text().splitlines() if l.startswith("| 20")]
    assert len(first_rows) == 1
    assert "| — |" in first_rows[0]  # no delta on the first scan

    prev = load_previous_summary(tmp_repo_with_imports, DEFAULT_CONFIG)
    assert prev is not None and prev["files"] > 0

    (tmp_repo_with_imports / "extra.py").write_text("\n".join(f"v{i} = {i}" for i in range(50)))
    repo_scan.scan(tmp_repo_with_imports, quiet=True)
    rows = [l for l in trend.read_text().splitlines() if l.startswith("| 20")]
    assert len(rows) == 2
    assert "+50" in rows[1]

    index = (tmp_repo_with_imports / "docs" / "index.md").read_text()
    assert "Since last scan" in index
    assert "lines +50" in index
