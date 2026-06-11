---
type: changelog
date: 2026-06-09
tags:
  - changelog
  - radar
  - testing
linked_files: ["[[repo_scan/radar/cli.py]]"]
---
# 2026-06-09 — Phase B4: metric-triggered autonomy + e2e

Final planned phase. The loop can now trigger itself off scan metrics, and the
whole stack is verified end-to-end through the real CLI with a fake LLM.

## What changed

- **`radar full`** — reads `docs/scan.json`, finds the file with the highest
  churn × complexity priority, generates a research problem from it, and runs
  the full loop. Requires `"radar_enabled": true`; exits cleanly when there is
  no candidate overlap. Supports the same `--gates` / `--approve` knobs.
- **Hook integration (decision)** — the pre-commit hook stays scan-only and
  advisory; LLM loops never run inside a commit. Instead, when `radar_enabled`
  and candidates exist, the scan prints a nudge to run `radar full`
  intentionally. Rationale: HANDOFF constraint #3 ("never block a commit") and
  loop latency make in-hook LLM calls a footgun.
- **CLI-level e2e** — subprocess test drives the real `radar` entry point
  (`python -m repo_scan.radar.cli`) against a tmp repo with a `.repo-scan.json`
  pointing `llm_cli` at the fake-LLM queue: research → analyze → gates (auto)
  → draft → audit → record, asserting on the spec and loop changelog files.
- **Dogfooding** — this repo now sets `"radar_enabled": true`, so scans emit
  `docs/research/candidates.md` for itself.
- **README** — full `radar` section: commands, LLM backend config, gate modes,
  pause/resume, output map, plus a Development section.

## Verification

- 6 new tests (62 total, all offline): candidate picking (no scan.json / no
  overlap / top priority), `radar full` guards, subprocess e2e, scan nudge path.
- Final rescan of this repo committed with this entry.

## Plan status

All phases from the build order are complete:
A (digest) → A2 (module split) → B1 (ingest) → B2 (research) → B3 (gates +
loop) → B4 (autonomy + e2e). Future work parked: trafilatura/pymupdf optional
installs, TS/Python call graphs, PageRank-proper ranking, multi-repo knowledge
sharing.
