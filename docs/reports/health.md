# Health report
_Generated 2026-06-09 22:54 UTC_  |  _Branch: main_  |  _Last commit: 6a140a5 feat: phase B3 — file-backed gates and full radar loop pipeline_

## File sizes

| File | Lines | Size | Status |
|------|-------|------|--------|
| `docs/scan.json` | 454 | 8.4 KB | 🟡 large |
| `repo_scan/writers.py` | 272 | 10.7 KB | ✅ |
| `repo_scan/radar/pipeline.py` | 248 | 10.5 KB | ✅ |
| `repo_scan/radar/fetchers.py` | 167 | 7.5 KB | ✅ |
| `repo_scan/handoff.py` | 156 | 5.2 KB | ✅ |
| `repo_scan/radar/sources.py` | 132 | 5.1 KB | ✅ |
| `repo_scan/radar/research.py` | 129 | 5.1 KB | ✅ |
| `tests/test_radar_ingest.py` | 114 | 4.8 KB | ✅ |
| `repo_scan/graphs.py` | 111 | 4.4 KB | ✅ |
| `repo_scan/scanner.py` | 103 | 4.8 KB | ✅ |
| `tests/test_radar_pipeline.py` | 102 | 5.2 KB | ✅ |
| `tests/test_radar_llm.py` | 95 | 4.6 KB | ✅ |
| `repo_scan/radar/llm.py` | 90 | 3.4 KB | ✅ |
| `repo_scan/radar/gates.py` | 85 | 3.9 KB | ✅ |
| `tests/test_radar_full.py` | 83 | 4.0 KB | ✅ |
| `repo_scan/identity.py` | 81 | 3.7 KB | ✅ |
| `tests/test_scan.py` | 80 | 3.8 KB | ✅ |
| `repo_scan/radar/cli.py` | 80 | 3.8 KB | ✅ |
| `tests/test_phase_a.py` | 78 | 4.0 KB | ✅ |
| `repo_scan/utils.py` | 67 | 3.2 KB | ✅ |
| `repo_scan/__init__.py` | 64 | 1.4 KB | ✅ |
| `repo_scan/cli.py` | 64 | 2.6 KB | ✅ |
| `repo_scan/languages.py` | 61 | 2.3 KB | ✅ |
| `repo_scan/ranking.py` | 52 | 2.4 KB | ✅ |
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
| `docs/research/tags.md` | 0 | 0.7 KB | ✅ |
| `docs/research/index.md` | 0 | 0.5 KB | ✅ |
| `docs/reports/calls.md` | 0 | 0.2 KB | ✅ |
| `docs/RADAR_CONTEXT.md` | 0 | 6.5 KB | ✅ |
| `docs/changelog/2026-06-09-phase-b3-loop.md` | 0 | 2.2 KB | ✅ |

## Complexity hotspots

| File | Function | Rank | Score | Line |
|------|----------|------|-------|------|
| `repo_scan/scanner.py` | `scan` | C | 20 | 25 |
| `repo_scan/graphs.py` | `get_python_dep_edges` | C | 19 | 46 |
| `repo_scan/writers.py` | `write_index` | C | 19 | 113 |
| `repo_scan/languages.py` | `get_line_counts` | C | 16 | 31 |
| `repo_scan/ranking.py` | `rank_files` | C | 16 | 15 |
| `repo_scan/identity.py` | `detect_entry_points` | C | 14 | 17 |
| `repo_scan/digest.py` | `write_digest` | C | 13 | 10 |
| `repo_scan/radar/sources.py` | `rebuild_research_index` | C | 13 | 112 |
| `repo_scan/graphs.py` | `get_c_call_graph_mermaid` | C | 12 | 99 |
| `repo_scan/writers.py` | `write_health_report` | C | 12 | 10 |
| `tests/test_radar_pipeline.py` | `test_loop_happy_path_auto_gates` | C | 12 | 54 |
| `repo_scan/graphs.py` | `get_ts_dep_edges` | C | 11 | 24 |

## Git churn (most changed files)

| File | Commits |
|------|---------|
| `pyproject.toml` | 5 |
| `setup.py` | 5 |
| `docs/architecture/dependency-graph.md` | 3 |
| `docs/index.md` | 3 |
| `docs/reports/calls.md` | 3 |
| `docs/reports/dependencies.md` | 3 |
| `docs/reports/health.md` | 3 |
| `repo_scan.py` | 3 |
| `repo_scan/radar/cli.py` | 2 |
| `docs/scan.json` | 2 |
| `README.md` | 2 |
| `.gitignore` | 2 |
| `HANDOFF.md` | 2 |
| `docs/changelog/2026-06-09-phase-b3-loop.md` | 1 |
| `repo_scan/radar/gates.py` | 1 |
