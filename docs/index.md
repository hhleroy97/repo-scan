# Repo index
_Last scan: 2026-06-09 23:11 UTC_

> Repo intelligence tool. Run it against any codebase — analyzes structure, generates dependency and call graphs as Mermaid diagrams, scores complexity, tracks git churn, writes everything to `docs/` committed to git and readable in Obsidian.

## Overview

| Metric | Value |
|--------|-------|
| Source files | 33 |
| Total lines | 3,552 |
| Languages | PY: 33 |
| Large files (>300 lines) | 1 |
| Critical files (>600 lines) | 1 |
| Branch | main |
| Last commit | 2083b77 feat: phase B4 — metric-triggered radar full, scan nudge, CLI e2e |
| Remote | https://github.com/hhleroy97/repo-scan.git |
| Manifests | `pyproject.toml`, `setup.py` |

## Entry points

- `repo-scan` → repo_scan:main (pyproject)
- `radar` → repo_scan.radar.cli:main (pyproject)

## Start here (ranked by importance)

_Composite of import centrality × git churn × complexity × size._

| File | Score | Imported by | Commits | CC | Lines |
|------|-------|-------------|---------|----|-------|
| `repo_scan/writers.py` | 49.0 | 3 | 0 | 31 | 272 |
| `repo_scan/config.py` | 36.5 | 5 | 0 | 0 | 42 |
| `setup.py` | 30.5 | 0 | 5 | 0 | 13 |
| `repo_scan/radar/pipeline.py` | 30.5 | 2 | 0 | 11 | 286 |
| `pyproject.toml` | 30.5 | 0 | 5 | 0 | 14 |
| `repo_scan/graphs.py` | 28.9 | 0 | 0 | 42 | 111 |
| `repo_scan/radar/sources.py` | 28.1 | 2 | 0 | 14 | 166 |
| `repo_scan/scanner.py` | 27.5 | 0 | 2 | 20 | 103 |
| `README.md` | 18.0 | 0 | 3 | 0 | 0 |
| `tests/test_radar_pipeline.py` | 15.3 | 0 | 0 | 19 | 113 |
| `repo_scan/radar/cli.py` | 14.8 | 0 | 2 | 0 | 80 |
| `repo_scan/radar/fetchers.py` | 12.9 | 1 | 0 | 0 | 170 |
| `repo_scan/radar/research.py` | 11.8 | 1 | 0 | 0 | 136 |
| `repo_scan/languages.py` | 11.7 | 0 | 0 | 16 | 61 |
| `repo_scan/ranking.py` | 11.3 | 0 | 0 | 16 | 52 |

## Structure

```
repo-scan/
├── docs/
│   ├── architecture/
│   │   └── dependency-graph.md
│   ├── changelog/
│   │   ├── 2026-06-09-phase-a.md
│   │   ├── 2026-06-09-phase-a2-split.md
│   │   ├── 2026-06-09-phase-b1-ingest.md
│   │   ├── 2026-06-09-phase-b2-research.md
│   │   ├── 2026-06-09-phase-b3-loop.md
│   │   └── 2026-06-09-phase-b4-autonomy.md
│   ├── reports/
│   │   ├── calls.md
│   │   ├── dependencies.md
│   │   └── health.md
│   ├── research/
│   │   ├── sources/
│   │   ├── candidates.md
│   │   ├── index.md
│   │   └── tags.md
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
│   ├── test_radar_full.py
│   ├── test_radar_gates.py
│   ├── test_radar_ingest.py
│   ├── test_radar_llm.py
│   ├── test_radar_pipeline.py
│   └── test_scan.py
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

## Action items

- [ ] Split `docs/scan.json` (617 lines)
