# Repo index
_Last scan: 2026-06-11 03:18 UTC_

> Repo intelligence tool. Run it against any codebase — analyzes structure, generates dependency and call graphs as Mermaid diagrams, scores complexity, tracks git churn, writes everything to `docs/` committed to git and readable in Obsidian.

> [!warning] 1 file(s) exceed 600 lines — see [[reports/health]]
> Largest: `repo_scan/hub/static/mermaid.min.js` (2028 lines)

> [!note] Since last scan (2026-06-11 01:31 UTC)
> lines +236, files +5, hotspot functions 0, critical files 0
> - `repo_scan/hub/server.py` complexity +2
> - `repo_scan/tickets/merge.py` complexity +1
> - `repo_scan/radar/research.py` complexity +1

## Overview

| Metric | Value |
|--------|-------|
| Source files | 133 |
| Total lines | 19,742 |
| Languages | TS: 1, PY: 132 |
| Large files (>300 lines) | 14 |
| Critical files (>600 lines) | 1 |
| Branch | main |
| Last commit | 89bf2e7 feat: boundary hardening — import contracts + scan.json schema |
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
| `repo_scan/utils.py` | 35.5 | 0.1375 | 35 | 0 | 0 | 97 | **no** |
| `repo_scan/provenance.py` | 30.1 | 0.0134 | 8 | 0 | 82 | 333 | yes |
| `repo_scan/radar/act.py` | 28.7 | 0.0111 | 13 | 0 | 76 | 541 | yes |
| `repo_scan/hub/prs.py` | 26.8 | 0.0063 | 6 | 0 | 74 | 530 | yes |
| `repo_scan/hub/graph.py` | 25.2 | 0.0059 | 4 | 0 | 70 | 480 | yes |
| `repo_scan/config.py` | 23.2 | 0.0543 | 44 | 19 | 0 | 104 | **no** |
| `repo_scan/graphs.py` | 21.7 | 0.0148 | 8 | 0 | 54 | 294 | yes |
| `repo_scan/radar/llm.py` | 20.9 | 0.0169 | 16 | 0 | 50 | 274 | yes |
| `repo_scan/hub/server.py` | 20.8 | 0.0077 | 6 | 17 | 29 | 405 | **no** |
| `repo_scan/radar/research.py` | 18.7 | 0.0072 | 5 | 0 | 51 | 272 | **no** |
| `README.md` | 14.1 | 0.0000 | 0 | 30 | 0 | 0 | **no** |
| `repo_scan/ranking.py` | 13.7 | 0.0110 | 4 | 0 | 34 | 113 | **no** |
| `repo_scan/radar/pipeline.py` | 12.9 | 0.0110 | 13 | 16 | 0 | 524 | yes |
| `repo_scan/hub/state.py` | 12.5 | 0.0450 | 39 | 0 | 0 | 212 | **no** |
| `repo_scan/provenance_audit.py` | 11.8 | 0.0076 | 2 | 0 | 30 | 136 | yes |

```mermaid
xychart-beta
    title "Importance score (top files)"
    x-axis ["utils.py", "provenance.py", "act.py", "prs.py", "graph.py", "config.py", "graphs.py", "llm.py"]
    y-axis "Score" 0 --> 100
    bar [35.5, 30.1, 28.7, 26.8, 25.2, 23.2, 21.7, 20.9]
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
    provenance.py: [0.02, 0.98]
    act.py: [0.02, 0.93]
    prs.py: [0.02, 0.90]
    graph.py: [0.02, 0.85]
    config.py: [0.63, 0.02]
    graphs.py: [0.02, 0.66]
    llm.py: [0.02, 0.61]
    server.py: [0.57, 0.35]
    research.py: [0.02, 0.62]
    README.md: [0.98, 0.02]
    ranking.py: [0.02, 0.41]
    pipeline.py: [0.53, 0.02]
```

## Structure

```
repo-scan/
├── docs/
│   ├── architecture/
│   │   ├── agentic-loop.md
│   │   ├── dependency-graph.md
│   │   └── graph-viewer-roadmap.md
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
│   │   ├── 2026-06-10-now-tab-layout.md
│   │   ├── 2026-06-10-parallel-loops.md
│   │   ├── 2026-06-10-phase-c3-workflow.md
│   │   ├── 2026-06-10-phase2-freshness.md
│   │   ├── 2026-06-10-pipeline-telemetry.md
│   │   ├── 2026-06-10-pr-merge-ui.md
│   │   ├── 2026-06-10-pr-remediate.md
│   │   ├── 2026-06-10-repo-snapshot.md
│   │   ├── 2026-06-10-tkt-0001-writers-refactor.md
│   │   ├── 2026-06-10-vault-autocommit.md
│   │   ├── 2026-06-11-boundary-hardening.md
│   │   ├── 2026-06-11-citation-scanner.md
│   │   ├── 2026-06-11-dashboard-improvements.md
│   │   ├── 2026-06-11-freshness-vanity.md
│   │   ├── 2026-06-11-mermaid-flash-fix.md
│   │   ├── 2026-06-11-project-state-checkpoint.md
│   │   └── 2026-06-11-vault-provenance.md
│   ├── planning/
│   │   ├── HANDOFF_06_10_2026_Repo_Reorg.md
│   │   ├── phase-1-week1.md
│   │   ├── phase-2-week2.md
│   │   ├── phase-3-week3.md
│   │   ├── phase-4-week4.md
│   │   ├── phase-5-week5.md
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
│   │   ├── tags.md
│   │   └── theory.md
│   ├── specs/
│   │   ├── 2026-06-09-should-repo-scan-replace-its-heuristic-i-spec.md
│   │   ├── 2026-06-10-add-a-list-for-the-open-tickets-to-the-n-spec.md
│   │   ├── 2026-06-10-convert-tickets-to-most-human-friendly-t-spec.md
│   │   ├── 2026-06-10-hidden-seam-pyproject-toml-setup-py-100-spec.md
│   │   ├── 2026-06-10-hidden-seam-repo-scan-config-py-repo-sca-spec.md
│   │   ├── 2026-06-10-hidden-seam-repo-scan-hub-daemon-py-test-spec.md
│   │   ├── 2026-06-10-hidden-seam-repo-scan-hub-server-py-repo-spec.md
│   │   ├── 2026-06-10-hidden-seam-repo-scan-radar-cli-py-repo-spec.md
│   │   ├── 2026-06-10-hidden-seam-repo-scan-scanner-py-repo-sc-spec.md
│   │   ├── 2026-06-10-i-want-to-add-a-more-robust-way-to-visua-spec.md
│   │   ├── 2026-06-10-move-the-agentic-loop-graph-and-untracke-spec.md
│   │   ├── 2026-06-10-refactor-repo-scan-graphs-py-cc-56-3-com-spec.md
│   │   ├── 2026-06-10-refactor-repo-scan-hub-daemon-py-cc-38-1-spec.md
│   │   ├── 2026-06-10-refactor-repo-scan-languages-py-cc-18-3-spec.md
│   │   ├── 2026-06-10-refactor-repo-scan-radar-pipeline-py-cc-spec.md
│   │   ├── 2026-06-10-refactor-repo-scan-radar-sources-py-cc-1-spec.md
│   │   ├── 2026-06-10-refactor-repo-scan-scanner-py-cc-27-8-co-spec.md
│   │   ├── 2026-06-10-refactor-repo-scan-writers-py-cc-52-7-co-spec.md
│   │   ├── 2026-06-10-refactor-tests-test-radar-pipeline-py-cc-spec.md
│   │   ├── 2026-06-10-split-repo-scan-hub-ui-py-706-lines-repo-spec.md
│   │   └── 2026-06-10-split-repo-scan-tickets-py-654-lines-rep-spec.md
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
│   │   ├── tkt-0031.md
│   │   ├── tkt-0032.md
│   │   ├── tkt-0033.md
│   │   ├── tkt-0034.md
│   │   ├── tkt-0035.md
│   │   ├── tkt-0036.md
│   │   ├── tkt-0037.md
│   │   ├── tkt-0038.md
│   │   └── tkt-0039.md
│   ├── digest.md
│   ├── index.md
│   ├── NORTH_STAR.md
│   ├── RADAR_CONTEXT.md
│   └── scan.json
├── repo_scan/
│   ├── hub/
│   │   ├── static/
│   │   ├── ui/
│   │   ├── __init__.py
│   │   ├── act_run.py
│   │   ├── agentic_loop.py
│   │   └── …
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

- [ ] Split `repo_scan/hub/static/mermaid.min.js` (2028 lines)
