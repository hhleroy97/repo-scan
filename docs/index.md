# Repo index
_Last scan: 2026-06-10 09:06 UTC_

> Repo intelligence tool. Run it against any codebase — analyzes structure, generates dependency and call graphs as Mermaid diagrams, scores complexity, tracks git churn, writes everything to `docs/` committed to git and readable in Obsidian.

> [!note] No critical files; 7 file(s) above the 300-line watermark

> [!warning] Since last scan (2026-06-10 03:06 UTC)
> lines +3563, files +13, hotspot functions +9, critical files 0
> - `repo_scan/tickets.py` complexity +55
> - `repo_scan/radar/act.py` complexity +52
> - `repo_scan/radar/llm.py` complexity +40

## Overview

| Metric | Value |
|--------|-------|
| Source files | 65 |
| Total lines | 9,277 |
| Languages | PY: 65 |
| Large files (>300 lines) | 7 |
| Critical files (>600 lines) | 0 |
| Branch | main |
| Last commit | 6a23752 vault: loop artifacts — tkt-0006 |
| Remote | https://github.com/hhleroy97/repo-scan.git |
| Manifests | `pyproject.toml` |

## Entry points

- `repo-scan` → repo_scan:main (pyproject)
- `radar` → repo_scan.radar.cli:main (pyproject)

## Start here (ranked by importance)

_Composite of import-graph PageRank × git churn × complexity × size._
_"Imported by" counts direct dependents only; PageRank captures transitive importance._

| File | Score | PageRank | Imported by | Commits | CC | Lines | Tests |
|------|-------|----------|-------------|---------|----|-------|-------|
| `repo_scan/tickets.py` | 46.7 | 0.0331 | 8 | 0 | 88 | 508 | yes |
| `repo_scan/config.py` | 45.7 | 0.0732 | 20 | 13 | 0 | 61 | **no** |
| `repo_scan/radar/gates.py` | 41.1 | 0.0988 | 27 | 0 | 13 | 120 | yes |
| `repo_scan/radar/pipeline.py` | 39.5 | 0.0244 | 5 | 10 | 30 | 409 | yes |
| `repo_scan/hub/daemon.py` | 39.4 | 0.0183 | 6 | 11 | 38 | 327 | **no** |
| `README.md` | 30.0 | 0.0000 | 0 | 21 | 0 | 0 | **no** |
| `repo_scan/radar/act.py` | 29.6 | 0.0172 | 4 | 0 | 52 | 445 | yes |
| `repo_scan/hub/ui.py` | 28.0 | 0.0184 | 1 | 9 | 0 | 439 | yes |
| `repo_scan/graphs.py` | 25.3 | 0.0188 | 3 | 0 | 56 | 140 | **no** |
| `repo_scan/scanner.py` | 25.0 | 0.0143 | 1 | 11 | 0 | 217 | yes |
| `repo_scan/radar/llm.py` | 24.2 | 0.0225 | 4 | 0 | 40 | 248 | yes |
| `repo_scan/ranking.py` | 18.2 | 0.0184 | 1 | 0 | 34 | 106 | **no** |
| `repo_scan/hub/tui.py` | 16.9 | 0.0156 | 1 | 0 | 25 | 218 | yes |
| `tests/test_act.py` | 16.8 | 0.0129 | 0 | 0 | 25 | 260 | yes |
| `repo_scan/hub/server.py` | 16.1 | 0.0154 | 2 | 0 | 18 | 282 | **no** |

```mermaid
xychart-beta
    title "Importance score (top files)"
    x-axis ["tickets.py", "config.py", "gates.py", "pipeline.py", "daemon.py", "README.md", "act.py", "ui.py"]
    y-axis "Score" 0 --> 100
    bar [46.7, 45.7, 41.1, 39.5, 39.4, 30, 29.6, 28]
```

```mermaid
quadrantChart
    title Where to focus: churn vs complexity
    x-axis Low churn --> High churn
    y-axis Low complexity --> High complexity
    quadrant-1 RADAR candidates
    quadrant-2 Complex but stable
    quadrant-3 Quiet
    quadrant-4 Hot but simple
    tickets.py: [0.02, 0.98]
    config.py: [0.62, 0.02]
    gates.py: [0.02, 0.15]
    pipeline.py: [0.48, 0.34]
    daemon.py: [0.52, 0.43]
    README.md: [0.98, 0.02]
    act.py: [0.02, 0.59]
    ui.py: [0.43, 0.02]
    graphs.py: [0.02, 0.64]
    scanner.py: [0.52, 0.02]
    llm.py: [0.02, 0.45]
    ranking.py: [0.02, 0.39]
```

## Structure

```
repo-scan/
├── docs/
│   ├── architecture/
│   │   └── dependency-graph.md
│   ├── changelog/
│   │   ├── 2026-06-09-assessment-hardening.md
│   │   ├── 2026-06-09-loop.md
│   │   ├── 2026-06-09-no-emoji-docs.md
│   │   ├── 2026-06-09-obsidian-graph.md
│   │   ├── 2026-06-09-pagerank-ranking.md
│   │   ├── 2026-06-09-phase-a.md
│   │   ├── 2026-06-09-phase-a2-split.md
│   │   ├── 2026-06-09-phase-b1-ingest.md
│   │   ├── 2026-06-09-phase-b2-research.md
│   │   ├── 2026-06-09-phase-b3-loop.md
│   │   ├── 2026-06-09-phase-b4-autonomy.md
│   │   ├── 2026-06-09-portability-fixes.md
│   │   ├── 2026-06-09-visual-layer.md
│   │   ├── 2026-06-10-act-stage.md
│   │   ├── 2026-06-10-act.md
│   │   ├── 2026-06-10-agent-factory.md
│   │   ├── 2026-06-10-agent-feedback.md
│   │   ├── 2026-06-10-behavior-and-tickets.md
│   │   ├── 2026-06-10-intent-governance.md
│   │   ├── 2026-06-10-llm-liveness.md
│   │   ├── 2026-06-10-loop.md
│   │   ├── 2026-06-10-mobile-hub.md
│   │   ├── 2026-06-10-parallel-loops.md
│   │   ├── 2026-06-10-phase-c3-workflow.md
│   │   ├── 2026-06-10-pr-merge-ui.md
│   │   ├── 2026-06-10-tkt-0001-writers-refactor.md
│   │   └── 2026-06-10-vault-autocommit.md
│   ├── reports/
│   │   ├── calls.md
│   │   ├── coupling.md
│   │   ├── dependencies.md
│   │   ├── health.md
│   │   └── trend.md
│   ├── research/
│   │   ├── analysis/
│   │   ├── pending/
│   │   ├── runs/
│   │   ├── sources/
│   │   ├── candidates.md
│   │   ├── decisions.md
│   │   ├── index.md
│   │   └── tags.md
│   ├── specs/
│   │   ├── 2026-06-09-should-repo-scan-replace-its-heuristic-i-spec.md
│   │   ├── 2026-06-10-add-a-list-for-the-open-tickets-to-the-n-spec.md
│   │   ├── 2026-06-10-convert-tickets-to-most-human-friendly-t-spec.md
│   │   ├── 2026-06-10-hidden-seam-pyproject-toml-setup-py-100-spec.md
│   │   ├── 2026-06-10-refactor-repo-scan-graphs-py-cc-56-3-com-spec.md
│   │   ├── 2026-06-10-refactor-repo-scan-languages-py-cc-18-3-spec.md
│   │   ├── 2026-06-10-refactor-repo-scan-radar-sources-py-cc-1-spec.md
│   │   ├── 2026-06-10-refactor-repo-scan-scanner-py-cc-27-8-co-spec.md
│   │   ├── 2026-06-10-refactor-repo-scan-writers-py-cc-52-7-co-spec.md
│   │   └── 2026-06-10-refactor-tests-test-radar-pipeline-py-cc-spec.md
│   ├── tickets/
│   │   ├── board.md
│   │   ├── tkt-0001.md
│   │   ├── tkt-0002.md
│   │   ├── tkt-0003.md
│   │   ├── tkt-0004.md
│   │   ├── tkt-0005.md
│   │   ├── tkt-0006.md
│   │   ├── tkt-0007.md
│   │   ├── tkt-0008.md
│   │   ├── tkt-0009.md
│   │   ├── tkt-0010.md
│   │   ├── tkt-0011.md
│   │   └── tkt-0012.md
│   ├── digest.md
│   ├── index.md
│   ├── RADAR_CONTEXT.md
│   └── scan.json
├── repo_scan/
│   ├── hub/
│   │   ├── __init__.py
│   │   ├── daemon.py
│   │   ├── notify.py
│   │   ├── progress.py
│   │   ├── prs.py
│   │   ├── server.py
│   │   ├── state.py
│   │   ├── tui.py
│   │   └── ui.py
│   ├── radar/
│   │   ├── __init__.py
│   │   ├── act.py
│   │   ├── cli.py
│   │   ├── fetchers.py
│   │   ├── gates.py
│   │   ├── llm.py
│   │   ├── pipeline.py
│   │   ├── research.py
│   │   └── sources.py
│   ├── __init__.py
│   ├── behavior.py
│   ├── churn.py
│   ├── cli.py
│   ├── complexity.py
│   ├── config.py
│   ├── digest.py
│   ├── graphs.py
│   ├── handoff.py
│   ├── hooks.py
│   ├── identity.py
│   ├── languages.py
│   ├── ranking.py
│   ├── scanner.py
│   ├── tests_map.py
│   ├── tickets.py
│   ├── trends.py
│   ├── utils.py
│   └── writers.py
├── repo_scan.egg-info/
│   ├── dependency_links.txt
│   ├── entry_points.txt
│   ├── PKG-INFO
│   ├── requires.txt
│   ├── SOURCES.txt
│   └── top_level.txt
├── tests/
│   ├── __snapshots__/
│   │   ├── test_scanner_snapshots.ambr
│   │   ├── test_scanner_unit.ambr
│   │   └── test_writers_snapshots.ambr
│   ├── conftest.py
│   ├── fake_llm.py
│   ├── test_act.py
│   ├── test_behavior.py
│   ├── test_hub.py
│   ├── test_hub_ui.py
│   ├── test_intent_governance.py
│   ├── test_languages.py
│   ├── test_llm_routing.py
│   ├── test_packaging.py
│   ├── test_phase_a.py
│   ├── test_portability.py
│   ├── test_prs.py
│   ├── test_radar_full.py
│   ├── test_radar_gates.py
│   ├── test_radar_ingest.py
│   ├── test_radar_llm.py
│   ├── test_radar_pipeline.py
│   ├── test_scan.py
│   ├── test_scanner_snapshots.py
│   ├── test_scanner_unit.py
│   ├── test_tests_map.py
│   ├── test_tickets.py
│   └── …
└── …
```

## Reports

- [[reports/health]] — file sizes, complexity, git churn
- [[reports/dependencies]] — dependency graphs (Mermaid)
- [[reports/calls]] — call graphs (Mermaid)

## Architecture

- [[architecture/dependency-graph]] — stable dep graph for cross-linking
- [[architecture/overview]] — hand-written system overview _(create this)_

## Research

- [[research/index]] — ingested sources _(populated by RADAR)_
- [[research/theory]] — distilled understanding _(yours to write)_
