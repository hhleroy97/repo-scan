# Repo index
_Last scan: 2026-06-09 22:43 UTC_

> Repo intelligence tool. Run it against any codebase — analyzes structure, generates dependency and call graphs as Mermaid diagrams, scores complexity, tracks git churn, writes everything to `docs/` committed to git and readable in Obsidian.

## Overview

| Metric | Value |
|--------|-------|
| Source files | 19 |
| Total lines | 1,716 |
| Languages | PY: 19 |
| Large files (>300 lines) | 1 |
| Critical files (>600 lines) | 0 |
| Branch | main |
| Last commit | 727b427 feat: phase A — robust initial digest (ranking, scan.json, tree, digest, AGENTS.md, madge fix) |
| Remote | https://github.com/hhleroy97/repo-scan.git |
| Manifests | `pyproject.toml`, `setup.py` |

## Entry points

- `repo-scan` → repo_scan:main (pyproject)

## Start here (ranked by importance)

_Composite of import centrality × git churn × complexity × size._

| File | Score | Imported by | Commits | CC | Lines |
|------|-------|-------------|---------|----|-------|
| `repo_scan/hooks.py` | 36.4 | 2 | 0 | 0 | 37 |
| `pyproject.toml` | 30.5 | 0 | 3 | 0 | 13 |
| `setup.py` | 30.4 | 0 | 3 | 0 | 12 |
| `repo_scan/graphs.py` | 29.1 | 0 | 0 | 42 | 111 |
| `repo_scan/writers.py` | 28.5 | 0 | 0 | 31 | 272 |
| `README.md` | 20.0 | 0 | 2 | 0 | 0 |
| `repo_scan/scanner.py` | 13.2 | 0 | 0 | 16 | 99 |
| `tests/test_phase_a.py` | 12.9 | 0 | 1 | 0 | 78 |
| `tests/test_scan.py` | 12.9 | 0 | 1 | 0 | 80 |
| `repo_scan/languages.py` | 11.8 | 0 | 0 | 16 | 61 |
| `repo_scan/ranking.py` | 11.4 | 0 | 0 | 16 | 52 |
| `repo_scan/identity.py` | 11.3 | 0 | 0 | 14 | 81 |
| `tests/conftest.py` | 11.0 | 0 | 1 | 0 | 28 |
| `repo_scan/digest.py` | 9.4 | 0 | 0 | 13 | 46 |
| `repo_scan/handoff.py` | 5.7 | 0 | 0 | 0 | 156 |

## Structure

```
repo-scan/
├── docs/
│   ├── architecture/
│   │   └── dependency-graph.md
│   ├── changelog/
│   │   └── 2026-06-09-phase-a.md
│   ├── reports/
│   │   ├── calls.md
│   │   ├── dependencies.md
│   │   └── health.md
│   ├── research/
│   ├── digest.md
│   ├── index.md
│   ├── RADAR_CONTEXT.md
│   └── scan.json
├── repo_scan/
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
│   ├── test_phase_a.py
│   └── test_scan.py
├── .gitignore
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
