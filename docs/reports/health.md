# Health report
_Generated 2026-06-11 15:13 UTC_  |  _Branch: main_  |  _Last commit: db06a3f docs: documentation pass — vault citations, frontmatter, provenance lint_

> [!note] Vault provenance: 107/146 docs fully traced (73%)
> Untracked ranked code: 3
> Stale docs: 0

## Vault health

| Metric | Value |
|--------|-------|
| Coverage | 73% (107/146) |
| Untracked code (ranked) | 3 |
| Stale docs | 0 |
| Orphan analysiss | 19 |
| Orphan sources | 13 |
| Orphan specs | 1 |
| Orphan tickets | 6 |

## Where the code lives

```mermaid
pie title Lines of code by directory
    "repo_scan" : 13823
    "tests" : 5861
    "(root)" : 74
```

## File sizes

| File | Lines | Size | Status |
|------|-------|------|--------|
| `repo_scan/hub/static/mermaid.min.js` | 2028 | 3258.6 KB | **critical** |
| `repo_scan/writers.py` | 553 | 24.6 KB | *large* |
| `repo_scan/radar/act.py` | 541 | 26.7 KB | *large* |
| `repo_scan/hub/prs.py` | 533 | 23.6 KB | *large* |
| `repo_scan/radar/pipeline.py` | 524 | 24.0 KB | *large* |
| `repo_scan/hub/graph.py` | 480 | 19.3 KB | *large* |
| `tests/test_hub_ui.py` | 410 | 19.4 KB | *large* |
| `repo_scan/hub/telemetry.py` | 407 | 17.0 KB | *large* |
| `repo_scan/hub/server.py` | 405 | 19.1 KB | *large* |
| `tests/test_hub.py` | 389 | 20.2 KB | *large* |
| `repo_scan/hub/daemon.py` | 379 | 17.3 KB | *large* |
| `tests/test_daemon.py` | 337 | 17.1 KB | *large* |
| `repo_scan/provenance.py` | 334 | 13.4 KB | *large* |
| `tests/test_hub_graph.py` | 311 | 13.3 KB | *large* |
| `repo_scan/graphs.py` | 294 | 13.0 KB | ok |
| `repo_scan/hub/ui/_graph_dashboard.py` | 293 | 15.5 KB | ok |
| `repo_scan/radar/llm.py` | 274 | 12.1 KB | ok |
| `repo_scan/radar/research.py` | 272 | 11.7 KB | ok |
| `repo_scan/hub/ui/_css.py` | 266 | 16.6 KB | ok |
| `repo_scan/scanner.py` | 248 | 11.4 KB | ok |
| `tests/test_prs.py` | 238 | 10.9 KB | ok |
| `repo_scan/hub/tui.py` | 233 | 11.1 KB | ok |
| `tests/test_tickets.py` | 230 | 10.8 KB | ok |
| `repo_scan/hub/state.py` | 212 | 9.4 KB | ok |
| `repo_scan/hub/ui/_prs_gates.py` | 209 | 9.7 KB | ok |
| `repo_scan/hub/ui/_graph_views2.py` | 184 | 9.0 KB | ok |
| `repo_scan/hub/ui/_graph.py` | 175 | 8.9 KB | ok |
| `tests/test_languages.py` | 174 | 7.8 KB | ok |
| `tests/test_scanner_snapshots.py` | 170 | 8.5 KB | ok |
| `repo_scan/radar/fetchers.py` | 170 | 7.6 KB | ok |
| `repo_scan/hub/ui/_activity.py` | 170 | 6.9 KB | ok |
| `repo_scan/hub/ui/_runtime.py` | 169 | 5.6 KB | ok |
| `tests/test_radar_pipeline.py` | 168 | 8.7 KB | ok |
| `repo_scan/radar/gates.py` | 167 | 7.8 KB | ok |
| `tests/test_act.py` | 165 | 9.2 KB | ok |
| `repo_scan/radar/sources.py` | 163 | 6.8 KB | ok |
| `tests/test_report_pipeline.py` | 162 | 5.8 KB | ok |
| `repo_scan/handoff.py` | 160 | 5.3 KB | ok |
| `repo_scan/hub/ui/_graph_sim.py` | 154 | 6.2 KB | ok |
| `repo_scan/trends.py` | 153 | 6.8 KB | ok |

## Complexity hotspots

| File | Function | Rank | Score | Line |
|------|----------|------|-------|------|
| `repo_scan/radar/act.py` | `cmd_act` | F | 54 | 336 |
| `repo_scan/radar/llm.py` | `complete` | E | 38 | 168 |
| `repo_scan/hub/prs.py` | `remediate_pr` | E | 33 | 472 |
| `repo_scan/provenance_audit.py` | `audit` | D | 30 | 55 |
| `repo_scan/hub/tui.py` | `frame_lines` | D | 29 | 92 |
| `repo_scan/hub/server.py` | `build_state` | D | 29 | 68 |
| `repo_scan/provenance.py` | `vault_coverage` | D | 27 | 227 |
| `repo_scan/hub/prs.py` | `_agent_remediate_pr` | D | 25 | 346 |
| `repo_scan/provenance.py` | `score_node` | D | 22 | 110 |
| `repo_scan/provenance.py` | `autolink_orphan_analyses` | C | 20 | 296 |
| `repo_scan/ranking.py` | `rank_files` | C | 19 | 76 |
| `repo_scan/tickets/propose.py` | `propose_from_scan` | C | 19 | 4 |
| `repo_scan/radar/research.py` | `repo_snapshot` | C | 18 | 71 |
| `repo_scan/radar/research.py` | `_snapshot_delta_lines` | C | 18 | 151 |
| `repo_scan/tickets/parse.py` | `derive_card` | C | 18 | 65 |
| `repo_scan/graphs.py` | `get_python_dep_edges` | C | 17 | 248 |
| `repo_scan/hub/gate_drawer.py` | `enrich_gate` | C | 16 | 71 |
| `repo_scan/hub/graph.py` | `_code_layer` | C | 16 | 85 |
| `repo_scan/hub/prs.py` | `_failed_ci_details` | C | 16 | 217 |
| `repo_scan/tickets/generation.py` | `generate_tickets` | C | 16 | 14 |

## Git churn (most changed files)

```mermaid
xychart-beta
    title "Commits touching each file"
    x-axis ["decisions.md", "2026-06-10-loop.md", "board.md", "README.md", "dependency-graph.…", "index.md", "calls.md", "dependencies.md", "health.md", "scan.json"]
    y-axis "Commits" 0 --> 64
    bar [64, 49, 34, 30, 22, 22, 22, 22, 22, 21]
```

| File | Commits |
|------|---------|
| `docs/research/decisions.md` | 64 |
| `docs/changelog/2026-06-10-loop.md` | 49 |
| `docs/tickets/board.md` | 34 |
| `README.md` | 30 |
| `docs/architecture/dependency-graph.md` | 22 |
| `docs/index.md` | 22 |
| `docs/reports/calls.md` | 22 |
| `docs/reports/dependencies.md` | 22 |
| `docs/reports/health.md` | 22 |
| `docs/scan.json` | 21 |
| `docs/research/index.md` | 21 |
| `docs/research/tags.md` | 21 |
| `docs/changelog/2026-06-10-act.md` | 19 |
| `docs/research/candidates.md` | 19 |
| `repo_scan/config.py` | 19 |

## Knowledge map (bus factor)

_Top-author share near 100% on an active file = knowledge silo._

| File | Commits | Authors | Top author share | Age (days) | Flag |
|------|---------|---------|------------------|------------|------|
| `repo_scan/radar/act.py` | 10 | 1 | 100% | 0 | silo |
| `repo_scan/radar/llm.py` | 10 | 1 | 100% | 0 | silo |
| `pyproject.toml` | 9 | 1 | 100% | 0 | silo |
| `repo_scan/radar/research.py` | 8 | 1 | 100% | 0 | silo |
| `repo_scan/hub/state.py` | 6 | 1 | 100% | 0 | silo |
| `repo_scan/hub/prs.py` | 5 | 1 | 100% | 0 | silo |
| `repo_scan/provenance.py` | 5 | 1 | 100% | 0 | silo |
| `repo_scan/hub/graph.py` | 4 | 1 | 100% | 0 | — |
| `tests/test_prs.py` | 4 | 1 | 100% | 0 | — |
| `repo_scan/provenance_lint.py` | 3 | 1 | 100% | 0 | — |
| `repo_scan/__init__.py` | 3 | 1 | 100% | 0 | — |
| `repo_scan/digest.py` | 3 | 1 | 100% | 0 | — |
| `repo_scan/hub/agentic_loop.py` | 3 | 1 | 100% | 0 | — |
| `repo_scan/ranking.py` | 3 | 1 | 100% | 0 | — |
| `repo_scan/radar/fetchers.py` | 3 | 1 | 100% | 0 | — |

## Action items

> [!warning] 1 file(s) over the 600-line critical threshold
> - [ ] Split `repo_scan/hub/static/mermaid.min.js` (2028 lines)
