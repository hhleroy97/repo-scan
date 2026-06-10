# Repo index
_Last scan: 2026-06-10 00:21 UTC_

> Repo intelligence tool. Run it against any codebase — analyzes structure, generates dependency and call graphs as Mermaid diagrams, scores complexity, tracks git churn, writes everything to `docs/` committed to git and readable in Obsidian.

> [!note] No critical files; 1 file(s) above the 300-line watermark

## Overview

| Metric | Value |
|--------|-------|
| Source files | 35 |
| Total lines | 3,343 |
| Languages | PY: 35 |
| Large files (>300 lines) | 1 |
| Critical files (>600 lines) | 0 |
| Branch | main |
| Last commit | c5b6286 fix: emoji-free generated docs — pictographs render as tofu in Obsidian/WSL |
| Remote | https://github.com/hhleroy97/repo-scan.git |
| Manifests | `pyproject.toml`, `setup.py` |

## Entry points

- `repo-scan` → repo_scan:main (pyproject)
- `radar` → repo_scan.radar.cli:main (pyproject)

## Start here (ranked by importance)

_Composite of import-graph PageRank × git churn × complexity × size._
_"Imported by" counts direct dependents only; PageRank captures transitive importance._

| File | Score | PageRank | Imported by | Commits | CC | Lines |
|------|-------|----------|-------------|---------|----|-------|
| `repo_scan/writers.py` | 58.4 | 0.0409 | 1 | 4 | 43 | 393 |
| `repo_scan/graphs.py` | 45.3 | 0.0481 | 2 | 0 | 56 | 140 |
| `repo_scan/radar/pipeline.py` | 43.6 | 0.0576 | 2 | 3 | 11 | 292 |
| `repo_scan/radar/sources.py` | 39.3 | 0.0505 | 2 | 3 | 14 | 166 |
| `repo_scan/radar/cli.py` | 37.0 | 0.1006 | 5 | 0 | 0 | 80 |
| `repo_scan/ranking.py` | 34.6 | 0.0481 | 1 | 0 | 34 | 106 |
| `repo_scan/config.py` | 34.4 | 0.0958 | 6 | 0 | 0 | 42 |
| `tests/test_radar_pipeline.py` | 34.3 | 0.0337 | 0 | 3 | 19 | 113 |
| `repo_scan/languages.py` | 23.9 | 0.0409 | 1 | 0 | 18 | 66 |
| `repo_scan/scanner.py` | 23.2 | 0.0000 | 0 | 3 | 20 | 119 |
| `repo_scan/radar/fetchers.py` | 19.4 | 0.0433 | 1 | 0 | 0 | 170 |
| `setup.py` | 19.1 | 0.0000 | 0 | 5 | 0 | 13 |
| `pyproject.toml` | 19.1 | 0.0000 | 0 | 5 | 0 | 14 |
| `repo_scan/radar/gates.py` | 18.9 | 0.0481 | 1 | 0 | 0 | 85 |
| `README.md` | 18.8 | 0.0000 | 0 | 5 | 0 | 0 |

```mermaid
xychart-beta
    title "Importance score (top files)"
    x-axis ["writers.py", "graphs.py", "pipeline.py", "sources.py", "cli.py", "ranking.py", "config.py", "test_radar_pipeli…"]
    y-axis "Score" 0 --> 100
    bar [58.4, 45.3, 43.6, 39.3, 37, 34.6, 34.4, 34.3]
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
    writers.py: [0.80, 0.77]
    graphs.py: [0.02, 0.98]
    pipeline.py: [0.60, 0.20]
    sources.py: [0.60, 0.25]
    ranking.py: [0.02, 0.61]
    test_radar_pipeli…: [0.60, 0.34]
    languages.py: [0.02, 0.32]
    scanner.py: [0.60, 0.36]
    setup.py: [0.98, 0.02]
    pyproject.toml: [0.98, 0.02]
    README.md: [0.98, 0.02]
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
│   │   └── health.md
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
