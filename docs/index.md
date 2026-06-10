# Repo index
_Last scan: 2026-06-10 00:38 UTC_

> Repo intelligence tool. Run it against any codebase — analyzes structure, generates dependency and call graphs as Mermaid diagrams, scores complexity, tracks git churn, writes everything to `docs/` committed to git and readable in Obsidian.

> [!note] No critical files; 1 file(s) above the 300-line watermark

> [!tip] No metric changes since last scan

## Overview

| Metric | Value |
|--------|-------|
| Source files | 39 |
| Total lines | 3,691 |
| Languages | PY: 39 |
| Large files (>300 lines) | 1 |
| Critical files (>600 lines) | 0 |
| Branch | main |
| Last commit | 6942774 feat: test-presence mapping — ranking Tests column, untested candidates get 2x priority |
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
| `repo_scan/writers.py` | 61.3 | 0.0334 | 1 | 6 | 44 | 406 | **no** |
| `repo_scan/graphs.py` | 51.7 | 0.0380 | 2 | 3 | 56 | 140 | **no** |
| `repo_scan/radar/pipeline.py` | 38.5 | 0.0470 | 2 | 3 | 11 | 292 | yes |
| `repo_scan/scanner.py` | 37.2 | 0.0000 | 0 | 7 | 24 | 129 | **no** |
| `repo_scan/cli.py` | 36.6 | 0.1004 | 7 | 0 | 0 | 64 | **no** |
| `repo_scan/radar/sources.py` | 34.7 | 0.0412 | 2 | 3 | 14 | 166 | **no** |
| `repo_scan/ranking.py` | 31.5 | 0.0392 | 1 | 0 | 34 | 106 | **no** |
| `repo_scan/languages.py` | 30.9 | 0.0322 | 1 | 3 | 18 | 66 | **no** |
| `repo_scan/config.py` | 30.6 | 0.0848 | 7 | 0 | 0 | 42 | **no** |
| `tests/test_radar_pipeline.py` | 20.9 | 0.0275 | 0 | 0 | 19 | 113 | yes |
| `README.md` | 20.0 | 0.0000 | 0 | 6 | 0 | 0 | **no** |
| `repo_scan/complexity.py` | 18.4 | 0.0322 | 1 | 0 | 11 | 91 | **no** |
| `tests/test_trends.py` | 17.3 | 0.0275 | 0 | 0 | 14 | 61 | yes |
| `setup.py` | 17.0 | 0.0000 | 0 | 5 | 0 | 13 | **no** |
| `pyproject.toml` | 17.0 | 0.0000 | 0 | 5 | 0 | 14 | **no** |

```mermaid
xychart-beta
    title "Importance score (top files)"
    x-axis ["writers.py", "graphs.py", "pipeline.py", "scanner.py", "cli.py", "sources.py", "ranking.py", "languages.py"]
    y-axis "Score" 0 --> 100
    bar [61.3, 51.7, 38.5, 37.2, 36.6, 34.7, 31.5, 30.9]
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
    writers.py: [0.86, 0.79]
    graphs.py: [0.43, 0.98]
    pipeline.py: [0.43, 0.20]
    scanner.py: [0.98, 0.43]
    sources.py: [0.43, 0.25]
    ranking.py: [0.02, 0.61]
    languages.py: [0.43, 0.32]
    test_radar_pipeli…: [0.02, 0.34]
    README.md: [0.86, 0.02]
    complexity.py: [0.02, 0.20]
    test_trends.py: [0.02, 0.25]
    setup.py: [0.71, 0.02]
```

## Structure

```
repo-scan/
├── docs/
│   ├── architecture/
│   │   └── dependency-graph.md
│   ├── changelog/
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
│   ├── test_phase_a.py
│   ├── test_portability.py
│   ├── test_radar_full.py
│   ├── test_radar_gates.py
│   ├── test_radar_ingest.py
│   ├── test_radar_llm.py
│   ├── test_radar_pipeline.py
│   ├── test_scan.py
│   ├── test_tests_map.py
│   ├── test_trends.py
│   └── test_visuals.py
├── .gitignore
├── .repo-scan.json
├── pyproject.toml
├── README.md
├── setup.py
└── Untitled.canvas
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
