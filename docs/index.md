# Repo index
_Last scan: 2026-06-10 15:07 UTC_

> Repo intelligence tool. Run it against any codebase — analyzes structure, generates dependency and call graphs as Mermaid diagrams, scores complexity, tracks git churn, writes everything to `docs/` committed to git and readable in Obsidian.

> [!note] No critical files; 8 file(s) above the 300-line watermark

> [!note] Since last scan (2026-06-10 09:06 UTC)
> lines +1098, files +5, hotspot functions 0, critical files 0
> - `repo_scan/hub/prs.py` complexity +75
> - `repo_scan/hub/daemon.py` complexity -38
> - `repo_scan/radar/pipeline.py` complexity -30

## Overview

| Metric | Value |
|--------|-------|
| Source files | 70 |
| Total lines | 10,375 |
| Languages | PY: 70 |
| Large files (>300 lines) | 8 |
| Critical files (>600 lines) | 0 |
| Branch | main |
| Last commit | 8f5b278 radar: implement tkt-0013 — Refactor repo_scan/hub/daemon.py (CC 38, 11 commits, unteste (#9) |
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
| `repo_scan/tickets.py` | 39.2 | 0.0311 | 24 | 0 | 88 | 508 | yes |
| `repo_scan/utils.py` | 36.5 | 0.2405 | 28 | 0 | 0 | 80 | **no** |
| `repo_scan/hub/prs.py` | 32.7 | 0.0099 | 5 | 0 | 75 | 526 | yes |
| `repo_scan/radar/act.py` | 25.3 | 0.0145 | 11 | 0 | 52 | 445 | yes |
| `repo_scan/radar/pipeline.py` | 21.4 | 0.0169 | 12 | 11 | 0 | 498 | yes |
| `repo_scan/config.py` | 20.6 | 0.0571 | 30 | 13 | 0 | 61 | **no** |
| `repo_scan/graphs.py` | 20.5 | 0.0126 | 5 | 0 | 54 | 172 | yes |
| `repo_scan/hub/daemon.py` | 19.0 | 0.0081 | 3 | 12 | 0 | 395 | yes |
| `README.md` | 18.9 | 0.0000 | 0 | 22 | 0 | 0 | **no** |
| `repo_scan/radar/llm.py` | 18.9 | 0.0189 | 12 | 0 | 40 | 249 | yes |
| `repo_scan/hub/ui.py` | 18.0 | 0.0098 | 2 | 9 | 0 | 467 | yes |
| `repo_scan/scanner.py` | 15.7 | 0.0085 | 3 | 12 | 0 | 222 | yes |
| `repo_scan/ranking.py` | 13.1 | 0.0096 | 2 | 0 | 34 | 106 | **no** |
| `repo_scan/hub/tui.py` | 12.4 | 0.0082 | 2 | 0 | 25 | 218 | yes |
| `repo_scan/hub/server.py` | 12.0 | 0.0106 | 4 | 0 | 18 | 281 | **no** |

```mermaid
xychart-beta
    title "Importance score (top files)"
    x-axis ["tickets.py", "utils.py", "prs.py", "act.py", "pipeline.py", "config.py", "graphs.py", "daemon.py"]
    y-axis "Score" 0 --> 100
    bar [39.2, 36.5, 32.7, 25.3, 21.4, 20.6, 20.5, 19]
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
    prs.py: [0.02, 0.85]
    act.py: [0.02, 0.59]
    pipeline.py: [0.50, 0.02]
    config.py: [0.59, 0.02]
    graphs.py: [0.02, 0.61]
    daemon.py: [0.55, 0.02]
    README.md: [0.98, 0.02]
    llm.py: [0.02, 0.45]
    ui.py: [0.41, 0.02]
    scanner.py: [0.55, 0.02]
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
│   │   ├── 2026-06-10-pr-remediate.md
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
│   │   ├── 2026-06-10-hidden-seam-repo-scan-scanner-py-repo-sc-spec.md
│   │   ├── 2026-06-10-i-want-to-add-a-more-robust-way-to-visua-spec.md
│   │   ├── 2026-06-10-refactor-repo-scan-graphs-py-cc-56-3-com-spec.md
│   │   ├── 2026-06-10-refactor-repo-scan-hub-daemon-py-cc-38-1-spec.md
│   │   ├── 2026-06-10-refactor-repo-scan-languages-py-cc-18-3-spec.md
│   │   ├── 2026-06-10-refactor-repo-scan-radar-pipeline-py-cc-spec.md
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
│   │   ├── tkt-0012.md
│   │   ├── tkt-0013.md
│   │   ├── tkt-0014.md
│   │   ├── tkt-0015.md
│   │   ├── tkt-0016.md
│   │   └── tkt-0017.md
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
│   ├── report_pipeline.py
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
│   ├── test_daemon.py
│   ├── test_graphs.py
│   ├── test_hub.py
│   ├── test_hub_ui.py
│   ├── test_intent_governance.py
│   ├── test_languages.py
│   ├── test_llm_routing.py
│   ├── test_packaging.py
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
