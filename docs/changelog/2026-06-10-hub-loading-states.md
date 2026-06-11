---
type: changelog
date: 2026-06-10
tags:
  - changelog
  - hub
linked_files: []
---
# Hub loading states

**Date:** 2026-06-10

## What changed

Slow hub actions now show explicit loading instead of a frozen UI:

- **Header status pill** + top **busy bar** during refresh and in-flight actions
- **Card overlays** on PR, gate, and ticket cards while awaiting API confirmation
- **Button labels** switch to in-progress text (Merging & verifying…, Approving…, etc.)
- **PR Fix & update** keeps overlay through background agent fix (`fix_started`)
- **Document viewer** shows spinner while `/api/doc` loads

## Tests

- `tests/test_hub.py::test_dashboard_loading_states`
