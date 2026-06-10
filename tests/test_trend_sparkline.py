from pathlib import Path

from repo_scan.trends import load_trend_sparkline


def test_sparkline_parses_trend_rows(tmp_repo):
    trend = tmp_repo / "docs" / "reports" / "trend.md"
    trend.parent.mkdir(parents=True, exist_ok=True)
    trend.write_text(
        "# Scan trend\n\n"
        "| When | Files | Lines | Hotspot fns | Critical | Δ lines | Δ hotspots | Vault % | Δ vault |\n"
        "|------|-------|-------|-------------|----------|---------|------------|---------|--------|\n"
        "| 2026-06-10 10:00 UTC | 40 | 10000 | 5 | 2 | — | — | 60% | — |\n"
        "| 2026-06-10 12:00 UTC | 42 | 10500 | 6 | 2 | +500 | +1 | 65% | +5% |\n"
    )
    rows = load_trend_sparkline(tmp_repo, {"docs_dir": "docs"}, limit=10)
    assert len(rows) == 2
    assert rows[0]["files"] == 40
    assert rows[1]["vault_pct"] == 0.65
