# Dashboard audit improvements

**Date:** 2026-06-11

Nine post-launch improvements to the vault audit dashboard, adding
actionable trend data and sharper risk indicators.

## Summary cards

- **Trend sparklines** on vault-% and files cards (`sparkSVG()` in
  `_graph_dashboard.py`), pulling the last 12 rows from
  `docs/reports/trend.md` via `load_trend_sparkline()` in `trends.py`.
- **Last-scan delta arrows** (↑/↓) on vault-% and untracked-code cards,
  computed from `vault_delta` in `build_state()`.
- **Knowledge debt score** — new card showing a 0–100 composite
  (40% coverage gap + 30% stale docs + 30% untracked code).
- **Approved-but-unhealthy badge** — inline warning count on the
  stale-docs card for specs that are approved but have provenance
  score < 3.

## Signal matrix

- Matrix cells are now clickable; tapping filters the graph by that
  signal (same as the filter buttons, but reachable from the matrix).

## New sections

- **Fragile code links** — collapsible panel listing files with ≤1
  vault citation (`thin_citations()` in `provenance.py`).
- **Scan trend chart** — full SVG chart plotting vault-% and file count
  over the last 12 scans with gridlines and date labels.

## Agentic loop

- **Completed trail** — last finished run lights up all stages it
  passed through in green on the Mermaid diagram (without overriding
  active blue or waiting amber).
- **Governance risk badge** — approved specs with score < 3 show an
  "approved but unhealthy" badge in the provenance chain panel.

## Backend

- `repo_scan/trends.py` — `load_trend_sparkline()` parses trend rows.
- `repo_scan/provenance.py` — `knowledge_debt`, `thin_citations()`.
- `repo_scan/hub/graph.py` — `approved_unhealthy` count in coverage.
- `repo_scan/hub/server.py` — `trend_sparkline` and `vault_delta` in
  `build_state()`.
- `repo_scan/hub/contract.py` — `TrendSparklineRow`, `VaultDelta`
  TypedDicts; `HUB_STATE_KEYS` extended.
- `repo_scan/hub/agentic_loop.py` — `_completed_trail()`,
  `classDef completed`.
