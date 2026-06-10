---
type: "changelog"
date: 2026-06-10
tags:
  - changelog
  - hub
  - radar
---

# 2026-06-10 — Consistent agent feedback on every surface

> [!success] One progress call, three surfaces
> CLI, web dashboard, and radar top now report the same stage text from the
> same write — no more "running" with no clue what the agent is doing.

## What was built

- `hub/progress.py` — `progress()` is the single way pipeline stages report:
  prints to the terminal, stamps `stage`/`stage_detail` on the run record,
  and appends to the shared agent event feed. Surfaces cannot drift apart.
- `hub/state.py` — `set_run_stage()` (live stage on run records) and the
  agent event feed (`docs/.radar/events.jsonl`, capped at 250 entries):
  `append_event()` / `load_events()`.
- Instrumented stages:
  - loop: research, analyze, gate 1 (with "waiting on human" when prompt),
    draft, audit (incl. revision rounds), gate 2, record
  - act: pre-implement gate, branch/worktree, implement (names the act
    model, e.g. composer-2.5), test (shows the test command and fix
    rounds), post-implement gate
  - every LLM call emits a feed event with role, model, token in/out, and
    duration; daemon lifecycle events (loop done, implementation committed,
    scan started) land in the feed too
- Web dashboard: runs show a live stage line; new "Agent feed" card on the
  Now tab with per-event timestamps and icons.
- radar top: stage line under active runs + AGENT FEED panel.
- Daemon scan block indentation fixed (introduced during instrumentation,
  caught by the suite before shipping).

## Tests

4 new/extended: event feed append/load/cap, run-stage updates (incl. no-op
without a run record), act happy path asserts stage + llm events, TUI frame
renders stage lines and the feed. 168 passing.
