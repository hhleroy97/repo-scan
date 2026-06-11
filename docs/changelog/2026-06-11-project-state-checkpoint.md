# Project state checkpoint — 2026-06-11

**Version:** 0.2.0  
**Commits:** 152  
**Python source:** ~11,000 lines across 77 modules  
**Tests:** 52 files (pytest + syrupy snapshots)  
**Vault docs:** 235 markdown files  

---

## What repo-scan is today

repo-scan is a **self-hosting agentic documentation system** for git repos.
It started as a static analysis scanner that writes Markdown reports, and has
grown into a full loop: scan → tickets → RADAR research → spec → implement →
PR → rescan.  Everything commits to a `docs/` vault that doubles as an
Obsidian knowledge base and machine-readable ground truth.

### Core loop

```
repo-scan  →  tickets  →  radar full  →  gate  →  radar act  →  PR  →  rescan
   ↑                                                                      │
   └──────────────────────────────────────────────────────────────────────-─┘
```

---

## Capability inventory

### 1. Static analysis (`repo-scan` CLI)

| Capability | Module(s) |
|------------|-----------|
| Language detection + line counts | `languages.py` (tokei / fallback) |
| Dependency graphs (Python AST, TS via madge, C via cflow) | `graphs.py` |
| Complexity scoring (radon / lizard) | `complexity.py` |
| Git churn analysis | `churn.py` |
| Change coupling, ownership, bus factor, code age | `behavior.py` |
| PageRank file ranking (inline power iteration) | `ranking.py` |
| Test coverage mapping (heuristic) | `tests_map.py` |
| Code → vault citation scanning | `citations.py` |
| Vault provenance scoring (E/L/C/F signals) | `provenance.py` |
| Report generation (Markdown + Mermaid + scan.json) | `writers.py`, `report_pipeline.py` |
| Scan-over-scan trend tracking | `trends.py` |
| Token-budgeted digest export | `digest.py` |
| Repo identity / manifest detection | `identity.py` |
| Auto-proposed work tickets from metrics | `tickets/` package |

### 2. RADAR agentic loop (`radar` CLI)

| Capability | Module(s) |
|------------|-----------|
| Source ingestion (arxiv, GitHub, URLs, local) | `radar/fetchers.py`, `radar/sources.py` |
| LLM-driven research with run logs | `radar/research.py`, `radar/llm.py` |
| Full pipeline: research → analyze → gate → draft → audit → gate → record | `radar/pipeline.py` |
| Human-in-the-loop gates (prompt / auto / deny) | `radar/gates.py` |
| Implementation stage: branch, edit, test, fix, commit, PR | `radar/act.py` |
| Model routing and usage ledger | `radar/llm.py` |
| Worktree-based parallel execution | `radar/act.py`, `hub/act_run.py` |

### 3. Hub dashboard (`radar serve`)

| Capability | Module(s) |
|------------|-----------|
| Mobile-first web dashboard (zero CDN, inline everything) | `hub/ui/` package (17 fragments) |
| Token-authenticated REST + SSE API | `hub/server.py` |
| Five tabs: Now, Gates, Tickets, Activity, Dashboard | `hub/ui/_now.py` … `_activity.py` |
| Knowledge graph with force-directed layout | `hub/ui/_graph.py`, `_graph_sim.py` |
| Provenance scoring visualization (score rings, signal matrix) | `hub/ui/_graph_dashboard.py` |
| Nine supplementary views (coverage heatmap, provenance flow, governance risk, citation density, stale queue, completeness radar, orphan clusters, change impact, timeline) | `hub/ui/_graph_views.py`, `_graph_views2.py` |
| Agentic loop Mermaid with live stage highlighting | `hub/agentic_loop.py`, `hub/ui/_graph_loop.py` |
| Force graph tuning (7 sliders, edge toggles, freeze) | `hub/ui/_graph.py` |
| Provenance tools (lint, autolink, audit from UI) | `hub/ui/_graph_dashboard.py` |
| Terminal curses dashboard (`radar top`) | `hub/tui.py` |
| Background daemon: scheduled rescans, parallel acts, budget caps | `hub/daemon.py` |
| PR visibility, merge, CI remediation via `gh` | `hub/prs.py` |
| Push notifications via ntfy.sh | `hub/notify.py` |
| Stage timing + token burn telemetry | `hub/telemetry.py` |

### 4. Provenance maintenance

| Capability | Module(s) |
|------------|-----------|
| Pre-commit linked_files linter | `provenance_lint.py` |
| CLI audit with regression check | `provenance_audit.py` |
| Orphan analysis auto-linker | `provenance.py` (`autolink_orphan_analyses`) |
| Auto-populate linked_files from ticket fingerprints | `tickets/io.py` |
| Cursor rule enforcing Vault: citations in new modules | `.cursor/rules/vault-citations.mdc` |

---

## Vault health at checkpoint

| Metric | Value |
|--------|-------|
| Score 3 (healthy) | 107 docs |
| Score 2 | 30 docs |
| Score 1 | 7 docs |
| Score 0 | 0 docs |
| Code → doc citations | 145 |
| Knowledge debt | 11.4 |
| Tickets | 39 (open + closed) |
| Specs | 21 |
| Research sources | 65 |
| Research analyses | 21 |

---

## Architecture / design decisions in effect

1. **Zero runtime dependencies** — stdlib only; optional tools degrade gracefully
2. **Docs as ground truth** — `docs/` is the canonical state; UI is a derived view
3. **No build step for UI** — single inline HTML page, vendored Mermaid, no CDN
4. **Mobile-first** — dashboard designed for phone over Tailscale
5. **Obsidian-native** — wikilinks, YAML frontmatter, Mermaid blocks work in Obsidian
6. **Self-hosting** — repo-scan scans itself; its own tickets drive RADAR loops
7. **Gate-controlled autonomy** — four named gates, configurable per-kind
8. **Provenance contract** — E/L/C/F signals with machine-checkable scoring

---

## What's getting large

The project has grown organically through five planning phases.  Areas that
may warrant extraction or splitting:

| Area | Size | Notes |
|------|------|-------|
| `hub/ui/` | 17 fragment files | Already split from a 706-line monolith; fragments stay under 300 lines each |
| `hub/daemon.py` | ~380 lines, CC 38 | Four-phase scheduler; decompose conditional is a standing ticket |
| `scanner.py` | ~280 lines, CC 28 | Orchestration monolith; `report_pipeline.py` partially decoupled |
| `writers.py` | 633 lines | Largest module; extract-function refactors are speced |
| `tickets/` | 11 modules | Already extracted from 654-line monolith; stable |
| `docs/` vault | 235 files | Growing with every scan/loop; consider archival strategy |
| `docs/changelog/` | 43+ entries | Works but no automated pruning |

---

## Runtime / deployment

- Runs on any machine with Python 3.10+ and git
- No Docker, no cloud, no database
- Hub serves on port 8800 (configurable)
- State persists in `docs/.radar/` (gitignored runtime) + `docs/` (committed vault)
- Designed for single-developer repos; no multi-user auth beyond bearer token

---

*This checkpoint captures the project as of commit `598a65f` (152 commits).
Next logical milestone: address the seven score-1 docs, review the three
newly proposed tickets (tkt-0037..0039), and consider whether `writers.py`
and `hub/daemon.py` refactors should proceed via RADAR or manual passes.*
