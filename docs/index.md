# Repo index
_Last scan: 2026-06-10 03:06 UTC_

> Repo intelligence tool. Run it against any codebase — analyzes structure, generates dependency and call graphs as Mermaid diagrams, scores complexity, tracks git churn, writes everything to `docs/` committed to git and readable in Obsidian.

> [!note] No critical files; 3 file(s) above the 300-line watermark

> [!warning] Since last scan (2026-06-10 02:07 UTC)
> lines +1128, files +7, hotspot functions +4, critical files 0
> - `repo_scan/hub/server.py` complexity +18
> - `repo_scan/radar/pipeline.py` complexity +17
> - `repo_scan/hub/daemon.py` complexity +15

## Overview

| Metric | Value |
|--------|-------|
| Source files | 52 |
| Total lines | 5,714 |
| Languages | PY: 52 |
| Large files (>300 lines) | 3 |
| Critical files (>600 lines) | 0 |
| Branch | main |
| Last commit | b1788a1 feat: .repo-scan.local.json for machine-private config (ntfy topic stays out of git) |
| Remote | https://github.com/hhleroy97/repo-scan.git |
| Manifests | `pyproject.toml`, `setup.py` |

## Entry points

- `repo-scan` → repo_scan:main (pyproject)
- `radar` → repo_scan.radar.cli:main (pyproject)

## Start here (ranked by importance)

_Composite of import-graph PageRank × git churn × complexity × size._
_"Imported by" counts direct dependents only; PageRank captures transitive importance._

| File | Score | PageRank | Imported by | Commits | CC | Lines | Tests |
|------|-------|----------|-------------|---------|----|-------|-------|
| `repo_scan/config.py` | 51.1 | 0.1560 | 23 | 6 | 0 | 55 | **no** |
| `repo_scan/radar/pipeline.py` | 40.7 | 0.0351 | 3 | 5 | 28 | 380 | yes |
| `repo_scan/scanner.py` | 40.6 | 0.0000 | 0 | 10 | 28 | 151 | **no** |
| `repo_scan/writers.py` | 35.2 | 0.0234 | 1 | 8 | 0 | 485 | yes |
| `repo_scan/graphs.py` | 33.9 | 0.0267 | 2 | 0 | 56 | 140 | **no** |
| `README.md` | 30.0 | 0.0000 | 0 | 12 | 0 | 0 | **no** |
| `repo_scan/tickets.py` | 28.0 | 0.0315 | 3 | 0 | 33 | 303 | yes |
| `tests/test_radar_pipeline.py` | 25.5 | 0.0208 | 1 | 4 | 19 | 114 | yes |
| `repo_scan/ranking.py` | 23.5 | 0.0275 | 1 | 0 | 34 | 106 | **no** |
| `setup.py` | 17.8 | 0.0000 | 0 | 7 | 0 | 14 | **no** |
| `pyproject.toml` | 17.8 | 0.0000 | 0 | 7 | 0 | 16 | **no** |
| `repo_scan/hub/server.py` | 16.8 | 0.0208 | 1 | 0 | 18 | 200 | **no** |
| `repo_scan/radar/sources.py` | 16.1 | 0.0289 | 2 | 0 | 14 | 166 | **no** |
| `repo_scan/radar/gates.py` | 14.7 | 0.0305 | 3 | 0 | 13 | 100 | yes |
| `repo_scan/languages.py` | 14.5 | 0.0226 | 1 | 0 | 18 | 66 | **no** |

```mermaid
xychart-beta
    title "Importance score (top files)"
    x-axis ["config.py", "pipeline.py", "scanner.py", "writers.py", "graphs.py", "README.md", "tickets.py", "test_radar_pipeli…"]
    y-axis "Score" 0 --> 100
    bar [51.1, 40.7, 40.6, 35.2, 33.9, 30, 28, 25.5]
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
    config.py: [0.50, 0.02]
    pipeline.py: [0.42, 0.50]
    scanner.py: [0.83, 0.50]
    writers.py: [0.67, 0.02]
    graphs.py: [0.02, 0.98]
    README.md: [0.98, 0.02]
    tickets.py: [0.02, 0.59]
    test_radar_pipeli…: [0.33, 0.34]
    ranking.py: [0.02, 0.61]
    setup.py: [0.58, 0.02]
    pyproject.toml: [0.58, 0.02]
    server.py: [0.02, 0.32]
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
│   │   ├── 2026-06-10-behavior-and-tickets.md
│   │   ├── 2026-06-10-loop.md
│   │   ├── 2026-06-10-mobile-hub.md
│   │   ├── 2026-06-10-phase-c3-workflow.md
│   │   └── 2026-06-10-tkt-0001-writers-refactor.md
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
│   │   └── 2026-06-10-refactor-repo-scan-writers-py-cc-52-7-co-spec.md
│   ├── tickets/
│   │   ├── board.md
│   │   ├── tkt-0001.md
│   │   ├── tkt-0002.md
│   │   ├── tkt-0003.md
│   │   ├── tkt-0004.md
│   │   ├── tkt-0005.md
│   │   ├── tkt-0006.md
│   │   ├── tkt-0007.md
│   │   └── tkt-0008.md
│   ├── digest.md
│   ├── index.md
│   ├── RADAR_CONTEXT.md
│   └── scan.json
├── repo_scan/
│   ├── hub/
│   │   ├── __init__.py
│   │   ├── daemon.py
│   │   ├── notify.py
│   │   ├── server.py
│   │   ├── state.py
│   │   └── ui.py
│   ├── radar/
│   │   ├── __init__.py
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
│   │   └── test_writers_snapshots.ambr
│   ├── conftest.py
│   ├── fake_llm.py
│   ├── test_behavior.py
│   ├── test_hub.py
│   ├── test_phase_a.py
│   ├── test_portability.py
│   ├── test_radar_full.py
│   ├── test_radar_gates.py
│   ├── test_radar_ingest.py
│   ├── test_radar_llm.py
│   ├── test_radar_pipeline.py
│   ├── test_scan.py
│   ├── test_tests_map.py
│   ├── test_tickets.py
│   ├── test_tickets_workflow.py
│   ├── test_trends.py
│   ├── test_visuals.py
│   └── test_writers_snapshots.py
├── .gitignore
├── .repo-scan.json
├── pyproject.toml
├── README.md
└── setup.py
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
