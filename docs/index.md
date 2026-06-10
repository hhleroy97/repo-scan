# Repo index
_Last scan: 2026-06-10 01:21 UTC_

> Repo intelligence tool. Run it against any codebase — analyzes structure, generates dependency and call graphs as Mermaid diagrams, scores complexity, tracks git churn, writes everything to `docs/` committed to git and readable in Obsidian.

> [!note] No critical files; 1 file(s) above the 300-line watermark

> [!tip] No metric changes since last scan

## Overview

| Metric | Value |
|--------|-------|
| Source files | 43 |
| Total lines | 4,261 |
| Languages | PY: 43 |
| Large files (>300 lines) | 1 |
| Critical files (>600 lines) | 0 |
| Branch | main |
| Last commit | 2bc8811 feat: C1 behavioral metrics — change coupling, bus-factor map, code age from one git pass |
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
| `repo_scan/writers.py` | 60.4 | 0.0295 | 1 | 7 | 52 | 469 | **no** |
| `repo_scan/graphs.py` | 44.0 | 0.0337 | 2 | 3 | 56 | 140 | **no** |
| `repo_scan/scanner.py` | 39.2 | 0.0000 | 0 | 8 | 27 | 146 | **no** |
| `repo_scan/config.py` | 36.0 | 0.1672 | 18 | 0 | 0 | 49 | **no** |
| `repo_scan/radar/pipeline.py` | 28.8 | 0.0416 | 2 | 3 | 11 | 292 | yes |
| `repo_scan/radar/sources.py` | 26.4 | 0.0364 | 2 | 3 | 14 | 166 | **no** |
| `repo_scan/ranking.py` | 24.7 | 0.0347 | 1 | 0 | 34 | 106 | **no** |
| `repo_scan/languages.py` | 24.4 | 0.0285 | 1 | 3 | 18 | 66 | **no** |
| `README.md` | 21.0 | 0.0000 | 0 | 7 | 0 | 0 | **no** |
| `repo_scan/tickets.py` | 19.5 | 0.0313 | 1 | 0 | 19 | 210 | yes |
| `tests/test_radar_pipeline.py` | 16.0 | 0.0244 | 0 | 0 | 19 | 113 | yes |
| `setup.py` | 15.3 | 0.0000 | 0 | 5 | 0 | 13 | **no** |
| `pyproject.toml` | 15.3 | 0.0000 | 0 | 5 | 0 | 14 | **no** |
| `repo_scan/behavior.py` | 14.1 | 0.0313 | 1 | 0 | 12 | 102 | yes |
| `repo_scan/complexity.py` | 12.8 | 0.0285 | 1 | 0 | 11 | 91 | **no** |

```mermaid
xychart-beta
    title "Importance score (top files)"
    x-axis ["writers.py", "graphs.py", "scanner.py", "config.py", "pipeline.py", "sources.py", "ranking.py", "languages.py"]
    y-axis "Score" 0 --> 100
    bar [60.4, 44, 39.2, 36, 28.8, 26.4, 24.7, 24.4]
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
    writers.py: [0.88, 0.93]
    graphs.py: [0.38, 0.98]
    scanner.py: [0.98, 0.48]
    pipeline.py: [0.38, 0.20]
    sources.py: [0.38, 0.25]
    ranking.py: [0.02, 0.61]
    languages.py: [0.38, 0.32]
    README.md: [0.88, 0.02]
    tickets.py: [0.02, 0.34]
    test_radar_pipeli…: [0.02, 0.34]
    setup.py: [0.62, 0.02]
    pyproject.toml: [0.62, 0.02]
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
│   │   └── 2026-06-09-visual-layer.md
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
│   │   └── 2026-06-09-should-repo-scan-replace-its-heuristic-i-spec.md
│   ├── tickets/
│   │   ├── board.md
│   │   ├── tkt-0001.md
│   │   ├── tkt-0002.md
│   │   ├── tkt-0003.md
│   │   ├── tkt-0004.md
│   │   └── tkt-0005.md
│   ├── digest.md
│   ├── index.md
│   ├── RADAR_CONTEXT.md
│   └── scan.json
├── repo_scan/
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
│   ├── SOURCES.txt
│   └── top_level.txt
├── tests/
│   ├── conftest.py
│   ├── fake_llm.py
│   ├── test_behavior.py
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
│   ├── test_trends.py
│   └── test_visuals.py
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
