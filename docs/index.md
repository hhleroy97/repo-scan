# Repo index
_Last scan: 2026-06-10 17:51 UTC_

> Repo intelligence tool. Run it against any codebase — analyzes structure, generates dependency and call graphs as Mermaid diagrams, scores complexity, tracks git churn, writes everything to `docs/` committed to git and readable in Obsidian.

> [!warning] 2 file(s) exceed 600 lines — see [[reports/health]]
> Largest: `repo_scan/hub/ui.py` (708 lines)

> [!warning] Since last scan (2026-06-10 17:47 UTC)
> lines +161, files +1, hotspot functions +1, critical files 0
> - `tests/test_radar_cli_gates.py` complexity +15

## Overview

| Metric | Value |
|--------|-------|
| Source files | 78 |
| Total lines | 12,163 |
| Languages | PY: 78 |
| Large files (>300 lines) | 10 |
| Critical files (>600 lines) | 2 |
| Branch | main |
| Last commit | 316c538 radar: implement tkt-0015 — Hidden seam: repo_scan/radar/cli.py <-> repo_scan/radar/gate (#14) |
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
| `repo_scan/tickets.py` | 42.3 | 0.0438 | 30 | 0 | 115 | 654 | yes |
| `repo_scan/utils.py` | 36.2 | 0.1899 | 28 | 0 | 0 | 84 | **no** |
| `repo_scan/radar/act.py` | 26.5 | 0.0141 | 13 | 0 | 76 | 523 | yes |
| `repo_scan/hub/prs.py` | 25.3 | 0.0091 | 6 | 0 | 74 | 530 | yes |
| `repo_scan/config.py` | 20.0 | 0.0537 | 35 | 15 | 0 | 66 | **no** |
| `repo_scan/graphs.py` | 19.4 | 0.0202 | 8 | 0 | 54 | 282 | yes |
| `repo_scan/hub/ui.py` | 19.3 | 0.0075 | 2 | 13 | 0 | 708 | yes |
| `repo_scan/hub/server.py` | 17.9 | 0.0106 | 6 | 11 | 21 | 331 | **no** |
| `repo_scan/radar/pipeline.py` | 17.3 | 0.0154 | 13 | 12 | 0 | 503 | yes |
| `repo_scan/radar/research.py` | 16.5 | 0.0102 | 5 | 0 | 50 | 262 | **no** |
| `README.md` | 15.9 | 0.0000 | 0 | 26 | 0 | 0 | **no** |
| `repo_scan/radar/llm.py` | 15.3 | 0.0162 | 12 | 0 | 40 | 253 | yes |
| `repo_scan/hub/daemon.py` | 14.2 | 0.0068 | 3 | 12 | 0 | 395 | yes |
| `repo_scan/scanner.py` | 13.4 | 0.0125 | 4 | 13 | 0 | 222 | yes |
| `repo_scan/writers.py` | 11.7 | 0.0110 | 4 | 0 | 12 | 498 | yes |

```mermaid
xychart-beta
    title "Importance score (top files)"
    x-axis ["tickets.py", "utils.py", "act.py", "prs.py", "config.py", "graphs.py", "ui.py", "server.py"]
    y-axis "Score" 0 --> 100
    bar [42.3, 36.2, 26.5, 25.3, 20, 19.4, 19.3, 17.9]
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
    act.py: [0.02, 0.66]
    prs.py: [0.02, 0.64]
    config.py: [0.58, 0.02]
    graphs.py: [0.02, 0.47]
    ui.py: [0.50, 0.02]
    server.py: [0.42, 0.18]
    pipeline.py: [0.46, 0.02]
    research.py: [0.02, 0.43]
    README.md: [0.98, 0.02]
    llm.py: [0.02, 0.35]
    daemon.py: [0.46, 0.02]
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
│   │   ├── 2026-06-10-act-doc-drift.md
│   │   ├── 2026-06-10-act-stage.md
│   │   ├── 2026-06-10-act.md
│   │   ├── 2026-06-10-agent-factory.md
│   │   ├── 2026-06-10-agent-feedback.md
│   │   ├── 2026-06-10-behavior-and-tickets.md
│   │   ├── 2026-06-10-gate-drawer.md
│   │   ├── 2026-06-10-hub-loading-states.md
│   │   ├── 2026-06-10-hub-sse.md
│   │   ├── 2026-06-10-intent-governance.md
│   │   ├── 2026-06-10-live-run-panel.md
│   │   ├── 2026-06-10-llm-liveness.md
│   │   ├── 2026-06-10-llm-null-byte-fix.md
│   │   ├── 2026-06-10-loop.md
│   │   ├── 2026-06-10-mobile-hub.md
│   │   ├── 2026-06-10-parallel-loops.md
│   │   ├── 2026-06-10-phase-c3-workflow.md
│   │   ├── 2026-06-10-phase2-freshness.md
│   │   ├── 2026-06-10-pr-merge-ui.md
│   │   ├── 2026-06-10-pr-remediate.md
│   │   ├── 2026-06-10-repo-snapshot.md
│   │   ├── 2026-06-10-tkt-0001-writers-refactor.md
│   │   └── 2026-06-10-vault-autocommit.md
│   ├── planning/
│   │   ├── phase-1-week1.md
│   │   ├── phase-2-week2.md
│   │   ├── phase-3-week3.md
│   │   └── README.md
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
│   │   ├── 2026-06-10-hidden-seam-repo-scan-config-py-repo-sca-spec.md
│   │   ├── 2026-06-10-hidden-seam-repo-scan-hub-server-py-repo-spec.md
│   │   ├── 2026-06-10-hidden-seam-repo-scan-radar-cli-py-repo-spec.md
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
│   │   ├── tkt-0017.md
│   │   ├── tkt-0018.md
│   │   ├── tkt-0019.md
│   │   ├── tkt-0020.md
│   │   ├── tkt-0021.md
│   │   ├── tkt-0022.md
│   │   ├── tkt-0023.md
│   │   ├── tkt-0024.md
│   │   ├── tkt-0025.md
│   │   ├── tkt-0026.md
│   │   ├── tkt-0027.md
│   │   ├── tkt-0028.md
│   │   ├── tkt-0029.md
│   │   ├── tkt-0030.md
│   │   └── tkt-0031.md
│   ├── digest.md
│   ├── index.md
│   ├── RADAR_CONTEXT.md
│   └── scan.json
├── repo_scan/
│   ├── hub/
│   │   ├── __init__.py
│   │   ├── contract.py
│   │   ├── daemon.py
│   │   ├── events.py
│   │   ├── gate_drawer.py
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

## Action items

- [ ] Split `repo_scan/hub/ui.py` (708 lines)
- [ ] Split `repo_scan/tickets.py` (654 lines)
