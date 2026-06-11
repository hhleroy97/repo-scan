---
type: changelog
date: 2026-06-09
tags:
  - changelog
  - radar
  - architecture
linked_files: ["[[repo_scan/ranking.py]]", "[[repo_scan/writers.py]]", "[[repo_scan/digest.py]]"]
---
# 2026-06-09 — PageRank centrality (first RADAR-driven change)

This change went through the full RADAR loop before a line was written —
the first spec produced, gated, and implemented end-to-end.

## Provenance

- Research: 5 sources ingested across two runs (aider, networkx, deprank,
  impact-graph, arXiv 2006.10892 on PageRank for documentation prioritization)
- Analysis: [[2026-06-09-should-repo-scan-replace-its-heuristic-i-analysis]]
  (confidence medium) — recommended inline PageRank, rejected networkx
- Gate 1: paused non-interactively, resumed with `--approve post_analyze`
- Spec: [[2026-06-09-should-repo-scan-replace-its-heuristic-i-spec]] — drafted,
  audited (revise), revised, re-audited
- Gate 2: paused; human approved with implementation requested
- Decision trail: docs/research/decisions.md

## What changed

- **`ranking.py`** — structural centrality upgraded from direct in-degree to
  damped PageRank (α=0.85, 100 iters, 1e-6 tol) with dangling-node
  redistribution, power iteration inline (~40 lines, no networkx).
  `_build_file_adjacency` requires BOTH edge endpoints to resolve (stricter
  than in-degree, per audit). Isolated files score 0; edgeless repos skip
  iteration entirely (no uniform-1/n degenerate case). `imported_by` remains
  the direct count; raw `pagerank` exposed in every ranked row.
- **`writers.py` / `digest.py`** — "Start here" table gains a PageRank column
  and clarifies "Imported by" is direct dependents only; digest bullets
  include the raw score.
- **Behavior change (flagged by audit):** importer-only files (outgoing edges,
  `imported_by=0`) now receive a nonzero structural term.

## Audit issues → resolutions

1. Both-endpoint edge resolution — implemented + documented + tested
2. Sparse-repo baseline mischaracterized — edgeless case tested (all-zero, churn still differentiates)
3. Importer-only nonzero centrality — explicit test
4. Disconnected components untested — explicit test (nonzero within components)
5. Committed docs drift — repo rescanned in this commit
6. "~50 lines" estimate — actual implementation is the evidence now

## Verification

- 7 new tests (71 total): star, chain transitivity, empty/dangling, disconnected
  components, strict adjacency, importer-only, edgeless repo.
- Rescan of this repo: `repo_scan/utils.py` and `config.py` (the transitive
  hubs) now rank above files that merely have high churn.
