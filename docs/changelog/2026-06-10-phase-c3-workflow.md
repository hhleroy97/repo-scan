---
type: changelog
date: 2026-06-10
tags:
  - changelog
  - radar
  - tickets
linked_files: ["[[repo_scan/tickets.py]]", "[[repo_scan/radar/pipeline.py]]"]
---
# 2026-06-10 — C3: ticket review workflow + RADAR integration

Closes the circuit the project was always aiming at:
ticket → human approval → RADAR intervention → measured improvement → close.

## Changes

### Ticket review CLI (`repo-scan tickets`)
- `repo-scan tickets` — list, sorted by status column then priority.
- `repo-scan tickets approve|start|reject|done <id>` — frontmatter status
  update + board rebuild. Obsidian editing keeps working identically;
  ticket files remain the single source of truth.

### Approved tickets drive `radar full`
- `pick_approved_ticket()` — highest-priority approved ticket is the work
  queue of record; raw churn×complexity candidates are now the fallback.
- The ticket's title + Why section become the loop's problem statement.
- When the loop's gates pass, the ticket moves to `in-progress` and a note
  with the spec wikilink is appended; a stopped/failed loop leaves the
  ticket approved (no state lost).

### Metrics-resolved detection
- `generate_tickets` now returns the set of open tickets whose fingerprint
  no longer triggers — the underlying metric cleared (file split, CC
  dropped, seam decoupled, tests added).
- Board cards get "**metrics resolved, ready to close**"; the scan prints
  `repo-scan tickets done <id>` nudges. Closing stays a human decision.

## Verification

- 6 new workflow tests (status roundtrip + board, priority-ordered queue,
  CLI list/approve/error paths, resolved flagging, radar full consuming an
  approved ticket and preserving state on stopped loops) + tuple-return
  updates to existing ticket tests.
- Full suite: 115 passed. Live CLI verified against this repo's 8 tickets.
