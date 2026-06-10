---
type: plan
phase: 3
title: "Week 3 — UI depth"
status: planned
tags: [planning, ui, sse, gates]
prerequisite: "[[phase-2-week2]]"
linked_research:
  - "[[url-githits-sse-stdlib-dashboard]]"
---

# Phase 3 — UI depth

**Goal:** Phone dashboard feels instant; gate decisions are informed; documentation
drift becomes a hard signal.

**Prerequisite:** Phase 1 live panel + Phase 2 record stage.

## Task 3.0 — Loading states pass ✅

**Problem:** Merge, gate approve, PR remediate, and background refresh can take
seconds (merge + rescan) or minutes (agent fix). The UI looked frozen — only the
clicked button disabled with no card or header feedback.

**Shipped (2026-06-10):**
- Header status pill + animated busy bar during refresh and pending ops
- Per-card overlay with spinner on PR / gate / ticket actions
- Long-running PR remediate keeps overlay until background fix completes or times out
- Document viewer loading state

**Acceptance criteria:**
- [x] Merge shows "Merging & verifying…" overlay on PR card
- [x] Gate approve/reject shows card overlay + status pill
- [x] Background poll shows thin busy bar without wiping pending overlays
- [x] `fix_started` PR keeps loading state until follow-up refresh

**Files:** `repo_scan/hub/ui.py`, `tests/test_hub.py`

## Task 3.1 — SSE on hub ✅

**Shipped (2026-06-10):**
- `/api/events` SSE with heartbeat + `connected` frame
- `events.py` broadcast bus wired from state changes
- Client `EventSource` → `refresh()`; slower backup poll when live
- Reconnect after 5s on error; adaptive 3–12s poll when SSE down

**Tests:** `test_event_bus_broadcast`, `test_sse_*`, `test_dashboard_has_sse_client`

## Task 3.2 — Gate drawer

Gate card expands to show:
- Spec summary (first 40 lines via `/api/doc`)
- Linked analysis wikilink
- Warning if spec `drafted_at` older than last `main` commit
- Acceptance criteria checklist

## Task 3.3 — Doc drift check on act

If act changes `repo_scan/*.py` public CLI surface, require README diff or
trigger `doc_fix` round (one bounded retry).

**Detailed acceptance criteria:** to be written after Phase 2 ships.
