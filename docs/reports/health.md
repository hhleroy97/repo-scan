# Health report
_Generated 2026-06-10 03:06 UTC_  |  _Branch: main_  |  _Last commit: b1788a1 feat: .repo-scan.local.json for machine-private config (ntfy topic stays out of git)_

## Where the code lives

```mermaid
pie title Lines of code by directory
    "repo_scan" : 4087
    "tests" : 1597
    "(root)" : 30
```

## File sizes

| File | Lines | Size | Status |
|------|-------|------|--------|
| `repo_scan/writers.py` | 485 | 21.5 KB | *large* |
| `repo_scan/radar/pipeline.py` | 380 | 16.5 KB | *large* |
| `repo_scan/tickets.py` | 303 | 14.5 KB | *large* |
| `tests/test_hub.py` | 258 | 14.3 KB | ok |
| `repo_scan/hub/ui.py` | 255 | 12.3 KB | ok |
| `repo_scan/hub/server.py` | 200 | 9.3 KB | ok |
| `repo_scan/radar/fetchers.py` | 170 | 7.6 KB | ok |
| `repo_scan/radar/sources.py` | 166 | 6.7 KB | ok |
| `repo_scan/handoff.py` | 156 | 5.2 KB | ok |
| `repo_scan/scanner.py` | 151 | 7.2 KB | ok |
| `tests/test_radar_ingest.py` | 141 | 6.0 KB | ok |
| `repo_scan/hub/state.py` | 141 | 6.1 KB | ok |
| `repo_scan/graphs.py` | 140 | 6.0 KB | ok |
| `repo_scan/radar/research.py` | 136 | 5.3 KB | ok |
| `repo_scan/hub/daemon.py` | 124 | 6.0 KB | ok |
| `tests/test_phase_a.py` | 123 | 6.8 KB | ok |
| `tests/test_radar_pipeline.py` | 114 | 6.0 KB | ok |
| `repo_scan/ranking.py` | 106 | 4.8 KB | ok |
| `tests/test_writers_snapshots.py` | 104 | 5.6 KB | ok |
| `repo_scan/behavior.py` | 102 | 4.4 KB | ok |
| `tests/test_tickets.py` | 101 | 4.9 KB | ok |
| `repo_scan/radar/gates.py` | 100 | 4.8 KB | ok |
| `repo_scan/trends.py` | 99 | 4.4 KB | ok |
| `tests/test_radar_llm.py` | 95 | 4.6 KB | ok |
| `repo_scan/radar/cli.py` | 94 | 4.7 KB | ok |
| `repo_scan/radar/llm.py` | 93 | 3.8 KB | ok |
| `repo_scan/complexity.py` | 91 | 3.7 KB | ok |
| `tests/test_visuals.py` | 89 | 4.4 KB | ok |
| `tests/test_radar_full.py` | 83 | 4.0 KB | ok |
| `repo_scan/identity.py` | 81 | 3.7 KB | ok |
| `tests/test_scan.py` | 80 | 3.8 KB | ok |
| `tests/test_tickets_workflow.py` | 80 | 4.1 KB | ok |
| `repo_scan/utils.py` | 80 | 3.9 KB | ok |
| `tests/test_behavior.py` | 72 | 3.7 KB | ok |
| `repo_scan/cli.py` | 67 | 2.9 KB | ok |
| `repo_scan/languages.py` | 66 | 2.8 KB | ok |
| `repo_scan/__init__.py` | 64 | 1.5 KB | ok |
| `tests/test_trends.py` | 61 | 2.8 KB | ok |
| `tests/test_portability.py` | 55 | 2.7 KB | ok |
| `repo_scan/config.py` | 55 | 2.3 KB | ok |

## Complexity hotspots

| File | Function | Rank | Score | Line |
|------|----------|------|-------|------|
| `repo_scan/scanner.py` | `scan` | D | 28 | 46 |
| `repo_scan/tickets.py` | `propose_from_scan` | C | 19 | 109 |
| `repo_scan/graphs.py` | `get_python_dep_edges` | C | 19 | 81 |
| `repo_scan/ranking.py` | `rank_files` | C | 19 | 69 |
| `tests/test_radar_pipeline.py` | `test_loop_happy_path_auto_gates` | C | 19 | 54 |
| `repo_scan/languages.py` | `get_line_counts` | C | 18 | 39 |
| `repo_scan/hub/server.py` | `build_state` | C | 18 | 38 |
| `repo_scan/radar/pipeline.py` | `cmd_loop` | C | 17 | 228 |
| `repo_scan/ranking.py` | `_pagerank` | C | 15 | 36 |
| `repo_scan/hub/daemon.py` | `daemon_tick` | C | 15 | 86 |
| `repo_scan/tickets.py` | `generate_tickets` | C | 14 | 256 |
| `repo_scan/identity.py` | `detect_entry_points` | C | 14 | 17 |
| `repo_scan/radar/sources.py` | `rebuild_research_index` | C | 14 | 153 |
| `tests/test_trends.py` | `test_scan_writes_trend_and_delta_on_second_run` | C | 14 | 59 |
| `repo_scan/digest.py` | `write_digest` | C | 13 | 10 |
| `repo_scan/graphs.py` | `edges_to_mermaid` | C | 13 | 13 |
| `repo_scan/radar/gates.py` | `gate` | C | 13 | 63 |
| `repo_scan/graphs.py` | `get_ts_dep_edges` | C | 12 | 53 |
| `repo_scan/graphs.py` | `get_c_call_graph_mermaid` | C | 12 | 134 |
| `repo_scan/behavior.py` | `analyze_history` | C | 12 | 42 |

## Git churn (most changed files)

```mermaid
xychart-beta
    title "Commits touching each file"
    x-axis ["README.md", "dependency-graph.…", "index.md", "calls.md", "dependencies.md", "health.md", "scan.json", "scanner.py", "candidates.md", "writers.py"]
    y-axis "Commits" 0 --> 12
    bar [12, 12, 12, 12, 12, 12, 11, 10, 9, 8]
```

| File | Commits |
|------|---------|
| `README.md` | 12 |
| `docs/architecture/dependency-graph.md` | 12 |
| `docs/index.md` | 12 |
| `docs/reports/calls.md` | 12 |
| `docs/reports/dependencies.md` | 12 |
| `docs/reports/health.md` | 12 |
| `docs/scan.json` | 11 |
| `repo_scan/scanner.py` | 10 |
| `docs/research/candidates.md` | 9 |
| `repo_scan/writers.py` | 8 |
| `pyproject.toml` | 7 |
| `setup.py` | 7 |
| `repo_scan/config.py` | 6 |
| `docs/digest.md` | 6 |
| `repo_scan/radar/pipeline.py` | 5 |

## Knowledge map (bus factor)

_Top-author share near 100% on an active file = knowledge silo._

| File | Commits | Authors | Top author share | Age (days) | Flag |
|------|---------|---------|------------------|------------|------|
| `README.md` | 12 | 1 | 100% | 0 | silo |
| `repo_scan/scanner.py` | 10 | 1 | 100% | 0 | silo |
| `repo_scan/writers.py` | 8 | 1 | 100% | 0 | silo |
| `pyproject.toml` | 7 | 1 | 100% | 0 | silo |
| `setup.py` | 7 | 1 | 100% | 0 | silo |
| `repo_scan/config.py` | 6 | 1 | 100% | 0 | silo |
| `repo_scan/radar/pipeline.py` | 5 | 1 | 100% | 0 | silo |
| `tests/test_radar_pipeline.py` | 4 | 1 | 100% | 0 | — |
| `repo_scan/radar/cli.py` | 3 | 1 | 100% | 0 | — |
| `repo_scan/radar/llm.py` | 3 | 1 | 100% | 0 | — |
| `repo_scan/graphs.py` | 3 | 1 | 100% | 0 | — |
| `repo_scan/languages.py` | 3 | 1 | 100% | 0 | — |
| `repo_scan/radar/sources.py` | 3 | 1 | 100% | 0 | — |
| `tests/test_hub.py` | 2 | 1 | 100% | 0 | — |
| `repo_scan/hub/daemon.py` | 2 | 1 | 100% | 0 | — |
