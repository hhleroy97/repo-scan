# Repo index
_Last scan: 2026-06-09 22:39 UTC_

> Repo intelligence tool. Run it against any codebase — analyzes structure, generates dependency and call graphs as Mermaid diagrams, scores complexity, tracks git churn, writes everything to `docs/` committed to git and readable in Obsidian.

## Overview

| Metric | Value |
|--------|-------|
| Source files | 5 |
| Total lines | 1,648 |
| Languages | PY: 5 |
| Large files (>300 lines) | 2 |
| Critical files (>600 lines) | 1 |
| Branch | main |
| Last commit | 1e69bb8 chore: baseline docs/ scan output, RADAR context, ignore .obsidian |
| Remote | https://github.com/hhleroy97/repo-scan.git |
| Manifests | `pyproject.toml`, `setup.py` |

## Entry points

- `repo-scan` → repo_scan:main (pyproject)

## Start here (ranked by importance)

_Composite of import centrality × git churn × complexity × size._

| File | Score | Imported by | Commits | CC | Lines |
|------|-------|-------------|---------|----|-------|
| `repo_scan.py` | 85.0 | 2 | 1 | 148 | 1131 |
| `setup.py` | 30.1 | 0 | 2 | 0 | 12 |
| `pyproject.toml` | 30.1 | 0 | 2 | 0 | 13 |
| `README.md` | 15.0 | 0 | 1 | 0 | 0 |
| `tests/test_phase_a.py` | 0.7 | 0 | 0 | 0 | 78 |
| `tests/test_scan.py` | 0.7 | 0 | 0 | 0 | 80 |
| `tests/conftest.py` | 0.2 | 0 | 0 | 0 | 28 |

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
├── repo_scan.py
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

- [ ] Split `repo_scan.py` (1131 lines)
