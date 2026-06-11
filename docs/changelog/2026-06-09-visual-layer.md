---
type: changelog
date: 2026-06-09
tags:
  - changelog
  - hub
  - architecture
linked_files: ["[[repo_scan/writers.py]]", "[[repo_scan/scanner.py]]"]
---
# 2026-06-09 — Visual layer for generated docs

Make the Obsidian/GitHub-rendered docs human-scannable: charts where there
were tables, callouts where there were plain lists, and color in the
dependency graphs.

## Changes

### New helpers (`repo_scan/writers.py`)
- `callout(kind, title, body)` — Obsidian callout blocks (`> [!warning] …`);
  GitHub renders the common kinds as alerts too.
- `mermaid_pie`, `mermaid_bar` (xychart-beta), `mermaid_quadrant` — chart
  builders with label truncation, value clamping (0.02–0.98), and duplicate
  label dedupe.
- `churn_complexity_quadrant(rows)` — shared churn × complexity quadrant
  (top-right = RADAR candidate zone); skipped when either axis is flat.

### index.md
- Health verdict callout at the top: `[!tip]` healthy / `[!note]` watermark
  files / `[!warning]` critical files with a link to `[[reports/health]]`.
- Bar chart of importance scores for the top 8 ranked files.
- Churn × complexity quadrant ("Where to focus").

### reports/health.md
- "Where the code lives" pie — lines of code by top-level directory
  (top 7 + other).
- Churn bar chart above the churn table.
- Action items wrapped in a `[!warning]` callout with the checklist inside.

### reports/dependencies.md — PageRank-tinted graphs
- `edges_to_mermaid(edges, scores)` now accepts node PageRank scores and
  emits `classDef`/`class` lines: **hot** (red, ≥60% of max), **warm**
  (amber, ≥25%), **cold** (gray). Legend line added to the report.
- `scanner.ranking_node_scores()` maps ranking rows to graph node names
  (dotted modules for Python incl. `__init__` collapse, rel paths for TS).
- Mermaid generation moved after ranking in `scan()` so scores exist.

### RADAR docs
- candidates.md: candidate-zone quadrant above the table; empty state is a
  `[!tip]` callout.
- specs: audit verdict is now a `[!success]`/`[!warning]` callout with notes
  and issues inside.
- loop.md changelog entries: outcome rendered as `[!success]` (approved) /
  `[!warning]` (stopped) / `[!danger]` (failed) callout.

## Fixes
- `get_line_counts` now skips the configured `docs_dir` — the scan was
  auditing its own output and flagging `docs/scan.json` as a critical file.

## Verification
- 9 new tests in `tests/test_visuals.py` (helpers, clamping/dedupe,
  PageRank tiers, end-to-end chart/callout presence in index/health/deps).
- 2 spec-verdict assertions updated to the callout format.
- Full suite: 80 passed. Rescan of this repo confirmed charts render and the
  false critical-file warning is gone.
