"""Visual layer: Mermaid charts, callouts, PageRank-tinted dep graphs."""

import json
from pathlib import Path

import repo_scan
from repo_scan.graphs import edges_to_mermaid
from repo_scan.utils import strip_emoji
from repo_scan.writers import (
    callout,
    churn_complexity_quadrant,
    mermaid_bar,
    mermaid_pie,
    mermaid_quadrant,
)


def test_strip_emoji():
    assert strip_emoji("\U0001F4E6 Repomix packs your repo") == "Repomix packs your repo"
    assert strip_emoji("plain text") == "plain text"
    assert strip_emoji("star \u2B50 and check \u2705 ok") == "star and check ok"


def test_health_status_column_is_plain_text(tmp_repo_with_imports):
    big = tmp_repo_with_imports / "big.py"
    big.write_text("\n".join(f"x{i} = {i}" for i in range(700)))
    repo_scan.scan(tmp_repo_with_imports, quiet=True)
    health = (tmp_repo_with_imports / "docs" / "reports" / "health.md").read_text()
    assert "**critical**" in health
    assert not any(ord(ch) > 0x2000 and ord(ch) not in (0x2014, 0x2026) for ch in health), \
        "generated health.md should contain no emoji/pictographs"


def test_callout_format():
    lines = callout("warning", "3 critical files", ["- [ ] split a.py"])
    assert lines[0] == "> [!warning] 3 critical files"
    assert lines[1] == "> - [ ] split a.py"


def test_mermaid_pie_and_bar():
    pie = mermaid_pie("Lines", [("repo_scan", 2000), ("tests", 800)])
    assert "pie title Lines" in pie[1]
    assert '"repo_scan" : 2000' in "\n".join(pie)
    assert mermaid_pie("Empty", []) == []

    bar = mermaid_bar("Scores", "Score", ["a/very_long_module_name_here.py", "b.py"],
                      [62.1, 30.0], y_max=100)
    text = "\n".join(bar)
    assert "xychart-beta" in text
    assert "bar [62.1, 30]" in text
    assert 'y-axis "Score" 0 --> 100' in text
    assert "very_long_module_…" in text  # label truncated, basename only
    assert mermaid_bar("Empty", "Y", [], []) == []


def test_mermaid_quadrant_clamps_and_dedupes():
    chart = mermaid_quadrant("T", "lo --> hi", "lo --> hi",
                             ("q1", "q2", "q3", "q4"),
                             [("x/a.py", 0.0, 1.5), ("y/a.py", 0.5, 0.5)])
    text = "\n".join(chart)
    assert "quadrantChart" in text
    assert "a.py: [0.02, 0.98]" in text     # clamped into visible range
    assert "a.py·: [0.50, 0.50]" in text    # duplicate basename deduped


def test_churn_complexity_quadrant_requires_both_signals():
    rows = [{"file": "a.py", "commits": 5, "complexity": 0}]
    assert churn_complexity_quadrant(rows) == []  # no complexity axis
    rows = [{"file": "a.py", "commits": 5, "complexity": 10},
            {"file": "b.py", "commits": 1, "complexity": 2}]
    text = "\n".join(churn_complexity_quadrant(rows))
    assert "RADAR candidates" in text
    assert "a.py: [0.98, 0.98]" in text


def test_edges_to_mermaid_pagerank_tiers():
    edges = [("app", "hub"), ("lib", "hub"), ("app", "lib")]
    scores = {"hub": 0.5, "lib": 0.2, "app": 0.05}
    text = edges_to_mermaid(edges, scores)
    assert "classDef hot" in text
    assert "class hub hot" in text
    assert "class lib warm" in text
    assert "class app cold" in text


def test_edges_to_mermaid_no_scores_no_classdefs():
    text = edges_to_mermaid([("a", "b")])
    assert "classDef" not in text


def test_index_has_callout_and_charts(tmp_repo_with_imports: Path):
    repo_scan.scan(tmp_repo_with_imports, quiet=True)
    index = (tmp_repo_with_imports / "docs" / "index.md").read_text()
    assert "> [!" in index                  # health verdict callout
    assert "xychart-beta" in index          # score bar chart


def test_health_has_pie_and_warning_callout(tmp_repo_with_imports: Path):
    big = tmp_repo_with_imports / "big.py"
    big.write_text("\n".join(f"x{i} = {i}" for i in range(700)))
    repo_scan.scan(tmp_repo_with_imports, quiet=True)
    health = (tmp_repo_with_imports / "docs" / "reports" / "health.md").read_text()
    assert "pie title Lines of code by directory" in health
    assert "> [!warning]" in health
    assert "Split `big.py`" in health
    index = (tmp_repo_with_imports / "docs" / "index.md").read_text()
    assert "> [!warning]" in index


def test_dep_report_has_color_legend(tmp_repo_with_imports: Path):
    repo_scan.scan(tmp_repo_with_imports, quiet=True)
    deps = (tmp_repo_with_imports / "docs" / "reports" / "dependencies.md").read_text()
    assert "Node color = PageRank tier" in deps
    assert "classDef hot" in deps
