# Live run panel on hub Now tab

**Date:** 2026-06-10

## What changed

- `/api/state` exposes `live_runs` — queued, running, and waiting-on-gate runs
  with `stage`, `stage_detail`, ticket id, and gate name.
- Phone dashboard Now tab shows a **Live now** card stack at the top with
  prominent stage headlines.
- Poll interval adapts: 3s when live runs exist, 12s when idle.

## Tests

- `tests/test_hub.py::test_build_state_live_runs`
