---
type: changelog
date: 2026-06-10
tags:
  - changelog
  - radar
  - tickets
linked_files: ["[[repo_scan/radar/act.py]]"]
---
# Phase 2 — agent freshness depth

**Date:** 2026-06-10

## What changed

### Pre-act context bundle

`build_act_context()` prepends diff stat, spec excerpt, acceptance criteria,
fresh `repo_snapshot()`, and recent act changelog lines to `ACT_PROMPT`.

### Record stage on PR merge

`record_merge_verification()` rescans after squash-merge, compares metric
fingerprints, appends a delta note, and auto-closes when the metric cleared.
Intent (`feature:`) tickets still close on merge.

### Auto-close metrics-resolved tickets

`auto_close_resolved_proposed()` closes `proposed` scan tickets when their
fingerprint no longer triggers — wired from `generate_tickets()`.

## Tests

- `tests/test_phase2_freshness.py`
