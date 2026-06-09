# Health report
_Generated 2026-06-09 22:39 UTC_  |  _Branch: main_  |  _Last commit: 1e69bb8 chore: baseline docs/ scan output, RADAR context, ignore .obsidian_

## File sizes

| File | Lines | Size | Status |
|------|-------|------|--------|
| `repo_scan.py` | 1131 | 48.6 KB | 🔴 critical |
| `docs/scan.json` | 306 | 5.5 KB | 🟡 large |
| `tests/test_scan.py` | 80 | 3.8 KB | ✅ |
| `tests/test_phase_a.py` | 78 | 4.0 KB | ✅ |
| `tests/conftest.py` | 28 | 1.1 KB | ✅ |
| `pyproject.toml` | 13 | 0.3 KB | ✅ |
| `setup.py` | 12 | 0.2 KB | ✅ |
| `docs/reports/health.md` | 0 | 2.0 KB | ✅ |
| `docs/changelog/2026-06-09-phase-a.md` | 0 | 2.2 KB | ✅ |
| `docs/RADAR_CONTEXT.md` | 0 | 6.5 KB | ✅ |
| `docs/reports/calls.md` | 0 | 0.2 KB | ✅ |
| `docs/index.md` | 0 | 2.6 KB | ✅ |
| `docs/digest.md` | 0 | 3.0 KB | ✅ |
| `docs/reports/dependencies.md` | 0 | 0.3 KB | ✅ |
| `docs/architecture/dependency-graph.md` | 0 | 0.3 KB | ✅ |
| `README.md` | 0 | 3.1 KB | ✅ |

## Complexity hotspots

| File | Function | Rank | Score | Line |
|------|----------|------|-------|------|
| `repo_scan.py` | `get_python_dep_edges` | C | 19 | 500 |
| `repo_scan.py` | `write_index` | C | 19 | 688 |
| `repo_scan.py` | `rank_files` | C | 16 | 315 |
| `repo_scan.py` | `get_line_counts` | C | 16 | 368 |
| `repo_scan.py` | `scan` | C | 16 | 1243 |
| `repo_scan.py` | `detect_entry_points` | C | 14 | 213 |
| `repo_scan.py` | `write_digest` | C | 13 | 850 |
| `repo_scan.py` | `get_c_call_graph_mermaid` | C | 12 | 553 |
| `repo_scan.py` | `write_health_report` | C | 12 | 585 |
| `repo_scan.py` | `get_ts_dep_edges` | C | 11 | 478 |

## Git churn (most changed files)

| File | Commits |
|------|---------|
| `.gitignore` | 2 |
| `HANDOFF.md` | 2 |
| `pyproject.toml` | 2 |
| `setup.py` | 2 |
| `docs/RADAR_CONTEXT.md` | 1 |
| `docs/architecture/dependency-graph.md` | 1 |
| `docs/index.md` | 1 |
| `docs/reports/calls.md` | 1 |
| `docs/reports/dependencies.md` | 1 |
| `docs/reports/health.md` | 1 |
| `README.md` | 1 |
| `repo_scan.py` | 1 |
| `repo_scan_README.md` | 1 |

## Action items

- [ ] Split `repo_scan.py` (1131 lines)
