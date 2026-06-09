# Repo index
_Last scan: 2026-06-09 22:54 UTC_

> Repo intelligence tool. Run it against any codebase — analyzes structure, generates dependency and call graphs as Mermaid diagrams, scores complexity, tracks git churn, writes everything to `docs/` committed to git and readable in Obsidian.

## Overview

| Metric | Value |
|--------|-------|
| Source files | 33 |
| Total lines | 3,269 |
| Languages | PY: 33 |
| Large files (>300 lines) | 1 |
| Critical files (>600 lines) | 0 |
| Branch | main |
| Last commit | 6a140a5 feat: phase B3 — file-backed gates and full radar loop pipeline |
| Remote | https://github.com/hhleroy97/repo-scan.git |
| Manifests | `pyproject.toml`, `setup.py` |

## Entry points

- `repo-scan` → repo_scan:main (pyproject)
- `radar` → repo_scan.radar.cli:main (pyproject)

## Start here (ranked by importance)

_Composite of import centrality × git churn × complexity × size._

| File | Score | Imported by | Commits | CC | Lines |
|------|-------|-------------|---------|----|-------|
| `repo_scan/config.py` | 36.5 | 5 | 0 | 0 | 42 |
| `repo_scan/languages.py` | 32.8 | 3 | 0 | 16 | 61 |
| `setup.py` | 30.5 | 0 | 5 | 0 | 13 |
| `pyproject.toml` | 30.5 | 0 | 5 | 0 | 14 |
| `repo_scan/graphs.py` | 29.1 | 0 | 0 | 42 | 111 |
| `repo_scan/radar/pipeline.py` | 29.1 | 2 | 1 | 0 | 248 |
| `repo_scan/writers.py` | 28.5 | 0 | 0 | 31 | 272 |
| `repo_scan/radar/sources.py` | 26.6 | 2 | 0 | 13 | 132 |
| `tests/test_radar_pipeline.py` | 16.9 | 0 | 1 | 12 | 102 |
| `repo_scan/radar/llm.py` | 16.3 | 1 | 1 | 0 | 90 |
| `repo_scan/radar/gates.py` | 16.1 | 1 | 1 | 0 | 85 |
| `repo_scan/scanner.py` | 15.7 | 0 | 0 | 20 | 103 |
| `repo_scan/radar/cli.py` | 14.9 | 0 | 2 | 0 | 80 |
| `repo_scan/radar/fetchers.py` | 13.1 | 1 | 0 | 0 | 167 |
| `README.md` | 12.0 | 0 | 2 | 0 | 0 |

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
