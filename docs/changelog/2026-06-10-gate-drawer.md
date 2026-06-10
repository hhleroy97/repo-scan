# Gate drawer on hub

**Date:** 2026-06-10

## What changed

- Tap a gate card to expand a drawer with spec excerpt (40 lines), linked
  analysis doc, acceptance criteria checklist, and stale-spec warning when
  `drafted_at` predates latest `main` commit.
- `gate_drawer.py` enriches `/api/state` gate rows server-side.

## Tests

- `tests/test_gate_drawer.py`
