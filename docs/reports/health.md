# Health report
_Generated 2026-06-10 00:09 UTC_  |  _Branch: main_  |  _Last commit: c7c69a2 feat: PageRank centrality in file ranking — first RADAR-loop-driven change (spec approved at Gate 2)_

## Where the code lives

```mermaid
pie title Lines of code by directory
    "repo_scan" : 2440
    "tests" : 812
    "(root)" : 27
```

## File sizes

| File | Lines | Size | Status |
|------|-------|------|--------|
| `repo_scan/writers.py` | 393 | 16.2 KB | 🟡 large |
| `repo_scan/radar/pipeline.py` | 292 | 12.4 KB | ✅ |
| `repo_scan/radar/fetchers.py` | 170 | 7.6 KB | ✅ |
| `repo_scan/radar/sources.py` | 166 | 6.7 KB | ✅ |
| `repo_scan/handoff.py` | 156 | 5.2 KB | ✅ |
| `tests/test_radar_ingest.py` | 141 | 6.0 KB | ✅ |
| `repo_scan/graphs.py` | 137 | 5.6 KB | ✅ |
| `repo_scan/radar/research.py` | 136 | 5.3 KB | ✅ |
| `tests/test_phase_a.py` | 123 | 6.8 KB | ✅ |
| `repo_scan/scanner.py` | 118 | 5.4 KB | ✅ |
| `tests/test_radar_pipeline.py` | 113 | 5.9 KB | ✅ |
| `repo_scan/ranking.py` | 106 | 4.8 KB | ✅ |
| `tests/test_radar_llm.py` | 95 | 4.6 KB | ✅ |
| `repo_scan/radar/llm.py` | 91 | 3.6 KB | ✅ |
| `repo_scan/radar/gates.py` | 85 | 3.9 KB | ✅ |
| `tests/test_radar_full.py` | 83 | 4.0 KB | ✅ |
| `repo_scan/identity.py` | 81 | 3.7 KB | ✅ |
| `repo_scan/radar/cli.py` | 80 | 3.8 KB | ✅ |
| `tests/test_scan.py` | 80 | 3.8 KB | ✅ |
| `tests/test_visuals.py` | 76 | 3.6 KB | ✅ |
| `repo_scan/utils.py` | 67 | 3.2 KB | ✅ |
| `repo_scan/__init__.py` | 64 | 1.4 KB | ✅ |
| `repo_scan/cli.py` | 64 | 2.6 KB | ✅ |
| `repo_scan/languages.py` | 61 | 2.4 KB | ✅ |
| `tests/test_radar_gates.py` | 46 | 2.4 KB | ✅ |
| `repo_scan/digest.py` | 46 | 2.3 KB | ✅ |
| `repo_scan/config.py` | 42 | 1.6 KB | ✅ |
| `repo_scan/hooks.py` | 37 | 1.2 KB | ✅ |
| `repo_scan/complexity.py` | 29 | 1.1 KB | ✅ |
| `tests/conftest.py` | 28 | 1.1 KB | ✅ |
| `tests/fake_llm.py` | 27 | 0.9 KB | ✅ |
| `repo_scan/churn.py` | 14 | 0.6 KB | ✅ |
| `pyproject.toml` | 14 | 0.4 KB | ✅ |
| `setup.py` | 13 | 0.3 KB | ✅ |
| `repo_scan/radar/__init__.py` | 5 | 0.2 KB | ✅ |
| `README.md` | 0 | 5.8 KB | ✅ |

## Complexity hotspots

| File | Function | Rank | Score | Line |
|------|----------|------|-------|------|
| `repo_scan/writers.py` | `write_index` | D | 23 | 231 |
| `repo_scan/scanner.py` | `scan` | C | 20 | 41 |
| `repo_scan/writers.py` | `write_health_report` | C | 20 | 104 |
| `repo_scan/graphs.py` | `get_python_dep_edges` | C | 19 | 75 |
| `repo_scan/ranking.py` | `rank_files` | C | 19 | 69 |
| `tests/test_radar_pipeline.py` | `test_loop_happy_path_auto_gates` | C | 19 | 54 |
| `repo_scan/languages.py` | `get_line_counts` | C | 16 | 31 |
| `repo_scan/ranking.py` | `_pagerank` | C | 15 | 36 |
| `repo_scan/identity.py` | `detect_entry_points` | C | 14 | 17 |
| `repo_scan/radar/sources.py` | `rebuild_research_index` | C | 14 | 153 |
| `repo_scan/digest.py` | `write_digest` | C | 13 | 10 |
| `repo_scan/graphs.py` | `edges_to_mermaid` | C | 13 | 13 |
| `repo_scan/graphs.py` | `get_c_call_graph_mermaid` | C | 12 | 128 |
| `repo_scan/graphs.py` | `get_ts_dep_edges` | C | 11 | 53 |
| `repo_scan/radar/pipeline.py` | `write_analysis` | C | 11 | 96 |

## Git churn (most changed files)

```mermaid
xychart-beta
    title "Commits touching each file"
    x-axis ["dependency-graph.…", "index.md", "calls.md", "dependencies.md", "health.md", "README.md", "scan.json", "pyproject.toml", "setup.py", "digest.md"]
    y-axis "Commits" 0 --> 6
    bar [6, 6, 6, 6, 6, 5, 5, 5, 5, 3]
```

| File | Commits |
|------|---------|
| `docs/architecture/dependency-graph.md` | 6 |
| `docs/index.md` | 6 |
| `docs/reports/calls.md` | 6 |
| `docs/reports/dependencies.md` | 6 |
| `docs/reports/health.md` | 6 |
| `README.md` | 5 |
| `docs/scan.json` | 5 |
| `pyproject.toml` | 5 |
| `setup.py` | 5 |
| `docs/digest.md` | 3 |
| `docs/research/candidates.md` | 3 |
| `docs/research/index.md` | 3 |
| `docs/research/tags.md` | 3 |
| `repo_scan.py` | 3 |
| `repo_scan/digest.py` | 2 |
