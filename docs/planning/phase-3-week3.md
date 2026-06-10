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

## Task 3.1 — SSE on hub

Implement `/api/events` SSE per [[url-githits-sse-stdlib-dashboard]]:
- Push on `append_event`, gate submit, run status change
- Client `EventSource` triggers `refresh()` or partial DOM update
- Fallback to adaptive poll if SSE disconnects

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
