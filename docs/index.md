# Repo index
_Last scan: 2026-06-10 00:00 UTC_

> Repo intelligence tool. Run it against any codebase — analyzes structure, generates dependency and call graphs as Mermaid diagrams, scores complexity, tracks git churn, writes everything to `docs/` committed to git and readable in Obsidian.

## Overview

| Metric | Value |
|--------|-------|
| Source files | 33 |
| Total lines | 3,665 |
| Languages | PY: 33 |
| Large files (>300 lines) | 1 |
| Critical files (>600 lines) | 1 |
| Branch | main |
| Last commit | 950e289 feat: Obsidian graph support — frontmatter metadata and provenance wikilinks across radar artifacts |
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
| `repo_scan/writers.py` | 62.1 | 0.1166 | 3 | 0 | 31 | 274 |
| `repo_scan/radar/pipeline.py` | 51.3 | 0.0778 | 2 | 2 | 11 | 286 |
| `repo_scan/radar/sources.py` | 46.1 | 0.0681 | 2 | 2 | 14 | 166 |
| `repo_scan/ranking.py` | 42.9 | 0.0649 | 1 | 0 | 34 | 106 |
| `tests/test_radar_pipeline.py` | 40.6 | 0.0456 | 0 | 2 | 19 | 113 |
| `repo_scan/config.py` | 36.5 | 0.1198 | 5 | 0 | 0 | 42 |
| `repo_scan/radar/fetchers.py` | 35.0 | 0.0585 | 1 | 2 | 0 | 170 |
| `repo_scan/radar/research.py` | 32.9 | 0.0552 | 1 | 2 | 0 | 136 |
| `setup.py` | 30.5 | 0.0000 | 0 | 5 | 0 | 13 |
| `pyproject.toml` | 30.5 | 0.0000 | 0 | 5 | 0 | 14 |
| `tests/test_radar_ingest.py` | 30.2 | 0.0456 | 0 | 2 | 0 | 141 |
| `repo_scan/graphs.py` | 28.9 | 0.0000 | 0 | 0 | 42 | 111 |
| `README.md` | 24.0 | 0.0000 | 0 | 4 | 0 | 0 |
| `repo_scan/radar/gates.py` | 21.9 | 0.0649 | 1 | 0 | 0 | 85 |
| `repo_scan/radar/llm.py` | 19.3 | 0.0552 | 1 | 0 | 0 | 91 |

## Structure

```
repo-scan/
├── docs/
│   ├── architecture/
│   │   └── dependency-graph.md
│   ├── changelog/
│   │   ├── 2026-06-09-loop.md
│   │   ├── 2026-06-09-obsidian-graph.md
│   │   ├── 2026-06-09-pagerank-ranking.md
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

## Action items

- [ ] Split `docs/scan.json` (628 lines)
