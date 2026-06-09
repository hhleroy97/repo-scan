# Health report
_Generated 2026-06-09 22:43 UTC_  |  _Branch: main_  |  _Last commit: 727b427 feat: phase A — robust initial digest (ranking, scan.json, tree, digest, AGENTS.md, madge fix)_

## File sizes

| File | Lines | Size | Status |
|------|-------|------|--------|
| `docs/scan.json` | 310 | 5.6 KB | 🟡 large |
| `repo_scan/writers.py` | 272 | 10.7 KB | ✅ |
| `repo_scan/handoff.py` | 156 | 5.2 KB | ✅ |
| `repo_scan/graphs.py` | 111 | 4.4 KB | ✅ |
| `repo_scan/scanner.py` | 99 | 4.5 KB | ✅ |
| `repo_scan/identity.py` | 81 | 3.7 KB | ✅ |
| `tests/test_scan.py` | 80 | 3.8 KB | ✅ |
| `tests/test_phase_a.py` | 78 | 4.0 KB | ✅ |
| `repo_scan/utils.py` | 67 | 3.2 KB | ✅ |
| `repo_scan/__init__.py` | 64 | 1.4 KB | ✅ |
| `repo_scan/cli.py` | 64 | 2.6 KB | ✅ |
| `repo_scan/languages.py` | 61 | 2.3 KB | ✅ |
| `repo_scan/ranking.py` | 52 | 2.4 KB | ✅ |
| `repo_scan/digest.py` | 46 | 2.3 KB | ✅ |
| `repo_scan/config.py` | 42 | 1.6 KB | ✅ |
| `repo_scan/hooks.py` | 37 | 1.2 KB | ✅ |
| `repo_scan/complexity.py` | 29 | 1.1 KB | ✅ |
| `tests/conftest.py` | 28 | 1.1 KB | ✅ |
| `repo_scan/churn.py` | 14 | 0.6 KB | ✅ |
| `pyproject.toml` | 13 | 0.3 KB | ✅ |
| `setup.py` | 12 | 0.2 KB | ✅ |
| `docs/reports/calls.md` | 0 | 0.2 KB | ✅ |
| `docs/reports/health.md` | 0 | 2.1 KB | ✅ |
| `docs/RADAR_CONTEXT.md` | 0 | 6.5 KB | ✅ |
| `docs/changelog/2026-06-09-phase-a.md` | 0 | 2.2 KB | ✅ |
| `docs/index.md` | 0 | 2.6 KB | ✅ |
| `docs/digest.md` | 0 | 2.6 KB | ✅ |
| `docs/reports/dependencies.md` | 0 | 0.3 KB | ✅ |
| `docs/architecture/dependency-graph.md` | 0 | 0.3 KB | ✅ |
| `README.md` | 0 | 3.1 KB | ✅ |

## Complexity hotspots

| File | Function | Rank | Score | Line |
|------|----------|------|-------|------|
| `repo_scan/graphs.py` | `get_python_dep_edges` | C | 19 | 46 |
| `repo_scan/writers.py` | `write_index` | C | 19 | 113 |
| `repo_scan/languages.py` | `get_line_counts` | C | 16 | 31 |
| `repo_scan/scanner.py` | `scan` | C | 16 | 25 |
| `repo_scan/ranking.py` | `rank_files` | C | 16 | 15 |
| `repo_scan/identity.py` | `detect_entry_points` | C | 14 | 17 |
| `repo_scan/digest.py` | `write_digest` | C | 13 | 10 |
| `repo_scan/graphs.py` | `get_c_call_graph_mermaid` | C | 12 | 99 |
| `repo_scan/writers.py` | `write_health_report` | C | 12 | 10 |
| `repo_scan/graphs.py` | `get_ts_dep_edges` | C | 11 | 24 |

## Git churn (most changed files)

| File | Commits |
|------|---------|
| `pyproject.toml` | 3 |
| `setup.py` | 3 |
| `README.md` | 2 |
| `docs/architecture/dependency-graph.md` | 2 |
| `docs/index.md` | 2 |
| `docs/reports/calls.md` | 2 |
| `docs/reports/dependencies.md` | 2 |
| `docs/reports/health.md` | 2 |
| `repo_scan.py` | 2 |
| `.gitignore` | 2 |
| `HANDOFF.md` | 2 |
| `docs/changelog/2026-06-09-phase-a.md` | 1 |
| `docs/digest.md` | 1 |
| `docs/scan.json` | 1 |
| `tests/conftest.py` | 1 |
