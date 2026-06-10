# Health report
_Generated 2026-06-10 15:07 UTC_  |  _Branch: main_  |  _Last commit: 8f5b278 radar: implement tkt-0013 — Refactor repo_scan/hub/daemon.py (CC 38, 11 commits, unteste (#9)_

## Where the code lives

```mermaid
pie title Lines of code by directory
    "repo_scan" : 6651
    "tests" : 3708
    "(root)" : 16
```

## File sizes

| File | Lines | Size | Status |
|------|-------|------|--------|
| `repo_scan/hub/prs.py` | 526 | 23.2 KB | *large* |
| `repo_scan/tickets.py` | 508 | 24.3 KB | *large* |
| `repo_scan/radar/pipeline.py` | 498 | 22.8 KB | *large* |
| `repo_scan/writers.py` | 485 | 21.5 KB | *large* |
| `repo_scan/hub/ui.py` | 467 | 23.9 KB | *large* |
| `repo_scan/radar/act.py` | 445 | 22.3 KB | *large* |
| `repo_scan/hub/daemon.py` | 395 | 18.2 KB | *large* |
| `tests/test_daemon.py` | 386 | 19.6 KB | *large* |
| `tests/test_hub.py` | 299 | 16.2 KB | ok |
| `repo_scan/hub/server.py` | 281 | 13.4 KB | ok |
| `repo_scan/radar/llm.py` | 249 | 11.1 KB | ok |
| `repo_scan/scanner.py` | 222 | 9.9 KB | ok |
| `repo_scan/hub/tui.py` | 218 | 10.4 KB | ok |
| `tests/test_prs.py` | 218 | 10.0 KB | ok |
| `repo_scan/hub/state.py` | 190 | 8.4 KB | ok |
| `repo_scan/radar/sources.py` | 189 | 7.8 KB | ok |
| `tests/test_act.py` | 178 | 9.8 KB | ok |
| `tests/test_languages.py` | 174 | 7.8 KB | ok |
| `repo_scan/graphs.py` | 172 | 7.4 KB | ok |
| `repo_scan/radar/fetchers.py` | 170 | 7.6 KB | ok |
| `tests/test_scanner_snapshots.py` | 165 | 8.3 KB | ok |
| `tests/test_radar_pipeline.py` | 162 | 8.5 KB | ok |
| `repo_scan/handoff.py` | 156 | 5.2 KB | ok |
| `tests/test_tickets.py` | 151 | 7.3 KB | ok |
| `tests/test_intent_governance.py` | 151 | 8.1 KB | ok |
| `repo_scan/radar/research.py` | 136 | 5.4 KB | ok |
| `tests/test_report_pipeline.py` | 128 | 4.6 KB | ok |
| `tests/test_llm_routing.py` | 124 | 5.8 KB | ok |
| `tests/test_phase_a.py` | 123 | 6.8 KB | ok |
| `repo_scan/radar/gates.py` | 120 | 5.9 KB | ok |
| `repo_scan/radar/cli.py` | 110 | 5.7 KB | ok |
| `tests/test_hub_ui.py` | 109 | 5.1 KB | ok |
| `tests/test_sources.py` | 108 | 5.2 KB | ok |
| `repo_scan/ranking.py` | 106 | 4.8 KB | ok |
| `tests/test_writers_snapshots.py` | 104 | 5.6 KB | ok |
| `tests/test_tickets_workflow.py` | 102 | 5.4 KB | ok |
| `repo_scan/behavior.py` | 102 | 4.4 KB | ok |
| `tests/test_tui.py` | 100 | 5.3 KB | ok |
| `repo_scan/languages.py` | 100 | 3.6 KB | ok |
| `repo_scan/trends.py` | 99 | 4.4 KB | ok |

## Complexity hotspots

| File | Function | Rank | Score | Line |
|------|----------|------|-------|------|
| `repo_scan/radar/act.py` | `cmd_act` | F | 52 | 251 |
| `repo_scan/hub/prs.py` | `remediate_pr` | E | 34 | 459 |
| `repo_scan/radar/llm.py` | `complete` | D | 28 | 158 |
| `repo_scan/hub/tui.py` | `frame_lines` | D | 25 | 92 |
| `repo_scan/hub/prs.py` | `_agent_remediate_pr` | D | 25 | 333 |
| `repo_scan/tickets.py` | `propose_from_scan` | C | 19 | 235 |
| `repo_scan/ranking.py` | `rank_files` | C | 19 | 69 |
| `repo_scan/tickets.py` | `derive_card` | C | 18 | 100 |
| `repo_scan/hub/server.py` | `build_state` | C | 18 | 42 |
| `repo_scan/graphs.py` | `get_python_dep_edges` | C | 17 | 112 |
| `repo_scan/hub/prs.py` | `_failed_ci_details` | C | 16 | 204 |
| `repo_scan/ranking.py` | `_pagerank` | C | 15 | 36 |
| `repo_scan/tickets.py` | `generate_tickets` | C | 14 | 464 |
| `repo_scan/tickets.py` | `tickets_main` | C | 14 | 513 |
| `repo_scan/identity.py` | `detect_entry_points` | C | 14 | 17 |
| `tests/test_trends.py` | `test_scan_writes_trend_and_delta_on_second_run` | C | 14 | 59 |
| `tests/test_act.py` | `test_act_happy_path_commits_on_branch` | C | 14 | 81 |
| `repo_scan/digest.py` | `write_digest` | C | 13 | 10 |
| `repo_scan/graphs.py` | `edges_to_mermaid` | C | 13 | 13 |
| `repo_scan/radar/gates.py` | `gate` | C | 13 | 88 |

## Git churn (most changed files)

```mermaid
xychart-beta
    title "Commits touching each file"
    x-axis ["decisions.md", "2026-06-10-loop.md", "README.md", "board.md", "index.md", "tags.md", "dependency-graph.…", "index.md", "calls.md", "dependencies.md"]
    y-axis "Commits" 0 --> 35
    bar [35, 26, 22, 18, 15, 15, 14, 14, 14, 14]
```

| File | Commits |
|------|---------|
| `docs/research/decisions.md` | 35 |
| `docs/changelog/2026-06-10-loop.md` | 26 |
| `README.md` | 22 |
| `docs/tickets/board.md` | 18 |
| `docs/research/index.md` | 15 |
| `docs/research/tags.md` | 15 |
| `docs/architecture/dependency-graph.md` | 14 |
| `docs/index.md` | 14 |
| `docs/reports/calls.md` | 14 |
| `docs/reports/dependencies.md` | 14 |
| `docs/reports/health.md` | 14 |
| `docs/scan.json` | 13 |
| `repo_scan/config.py` | 13 |
| `repo_scan/hub/daemon.py` | 12 |
| `repo_scan/scanner.py` | 12 |

## Knowledge map (bus factor)

_Top-author share near 100% on an active file = knowledge silo._

| File | Commits | Authors | Top author share | Age (days) | Flag |
|------|---------|---------|------------------|------------|------|
| `repo_scan/config.py` | 13 | 1 | 100% | 0 | silo |
| `repo_scan/radar/llm.py` | 8 | 1 | 100% | 0 | silo |
| `repo_scan/writers.py` | 8 | 1 | 100% | 0 | silo |
| `pyproject.toml` | 7 | 1 | 100% | 0 | silo |
| `repo_scan/radar/act.py` | 6 | 1 | 100% | 0 | silo |
| `repo_scan/radar/gates.py` | 5 | 1 | 100% | 0 | silo |
| `repo_scan/radar/cli.py` | 5 | 1 | 100% | 0 | silo |
| `tests/test_llm_routing.py` | 3 | 1 | 100% | 0 | — |
| `repo_scan/hub/prs.py` | 3 | 1 | 100% | 0 | — |
| `tests/test_prs.py` | 3 | 1 | 100% | 0 | — |
| `repo_scan/hub/state.py` | 3 | 1 | 100% | 0 | — |
| `repo_scan/radar/research.py` | 3 | 1 | 100% | 0 | — |
| `tests/test_hub_ui.py` | 2 | 1 | 100% | 0 | — |
| `tests/test_radar_gates.py` | 2 | 1 | 100% | 0 | — |
| `repo_scan/hub/notify.py` | 2 | 1 | 100% | 0 | — |
