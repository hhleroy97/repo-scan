---
type: changelog
date: 2026-06-09
tags:
  - changelog
  - radar
  - testing
linked_files: ["[[repo_scan/trends.py]]", "[[repo_scan/tests_map.py]]"]
---
# 2026-06-09 — Assessment hardening: the reflexion-loop foundation

The scan is the sensor layer for RADAR; this phase makes it strong enough
to carry the loop. Three new signal sources plus CI, motivated by the
hhl_site portability run exposing that complexity (and therefore the whole
candidate feed) was Python-only.

## 0. CI (GitHub Actions)

`.github/workflows/ci.yml` — pytest on Python 3.10 + 3.12 with radon,
lizard, and madge installed so optional-tool paths actually execute.
README badge added. The 96-test suite now runs on every push.

## 1. Multi-language complexity (`lizard`)

- `get_lizard_complexity()` runs lizard (`pip install lizard`) over the
  repo with exclude-dir filters and maps CCN onto radon's A–F rank scale.
- `get_complexity()` merges: radon for Python (kept — better Python
  semantics), lizard for everything else, lizard for Python too when radon
  is missing.
- Impact on hhl_site: complexity went from invisible (CC=0 everywhere) to
  9 ranked hotspots — `PageSection.tsx` is rank F (CCN 42). The candidates
  feed now works on frontend repos.

## 2. Scan-over-scan trend deltas (`repo_scan/trends.py`)

The "verify" half of the reflexion loop — interventions are only
improvements if the metrics move.

- Each scan summarizes itself (files, lines, hotspot functions, critical
  files, per-file CC) and diffs against the previous `scan.json` before
  overwriting it.
- `index.md` gets a "Since last scan" callout — `[!warning]` when hotspots
  or critical files increased, with the top complexity movers per file.
- `reports/trend.md` keeps a capped (60-row) per-scan history table.

## 3. Test-presence mapping (`repo_scan/tests_map.py`)

- Heuristic: a source file is "tested" when a test-looking file
  (`test_*`, `*_test`, `*.test.*`, `*.spec.*`, or anything under
  tests/test/__tests__ dirs) shares its stem tokens. `index.tsx`/`main.py`
  match on their parent directory name.
- Ranking table gains a Tests column (`yes` / `**no**`).
- Untested RADAR candidates get a 2x priority boost — high churn x high
  complexity x no safety net is the strongest refactor trigger we emit.

## Verification

- 12 new tests (lizard rank mapping + exclusion, trend summaries/deltas/
  callouts/log, test-map heuristics, end-to-end column assertions).
- Full suite: 96 passed.
- Validated on hhl_site: CC column populated, Tests column all-no (real
  finding — only App.tsx has a test), trend rows accumulating.
