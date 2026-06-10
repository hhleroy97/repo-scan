# repo_snapshot — ranked context for RADAR loops

**Date:** 2026-06-10

## What changed

- `repo_snapshot()` in `repo_scan/radar/research.py` builds a ranked map from
  `scan.json` (hotspots, open tickets, trend deltas, coupling alert, digest excerpt).
- `repo_snapshot_digest()` deduplicates identical snapshots across parallel loops
  (keyed on `scan.generated_at` + git HEAD).
- Research propose and analyze/draft stages inject the snapshot instead of the
  old five-line `repo_context_snippet`.
- Config: `repo_snapshot_max_chars` (default 2500).

## Tests

- `tests/test_repo_snapshot.py`
