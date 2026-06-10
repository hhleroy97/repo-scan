---
type: changelog
date: 2026-06-10
tags:
  - changelog
  - radar
  - hub
---

# Parallel research loops

Loops now fan out on threads like acts do — the daemon is no longer limited
to one research loop at a time.

## What changed

- **Threaded loop scheduling** — `daemon_tick` starts up to
  `max_parallel_loops` (default 2, new config key) research loops per tick,
  one per approved ticket, highest priority first. Each runs on its own
  thread via the unified `_spawn()` helper, so a long research stage never
  blocks the scheduler tick, gate resumes, or act fan-out.
- **Unified thread registry** — `_act_threads` became `_run_threads` and
  tracks both acts and loops. Orphan reclaim, the scan guard, and per-kind
  slot accounting all read from it.
- **Race-safe spec linking** — finished loops used to link "the newest spec
  file" onto their ticket, which is wrong the moment two loops finish out of
  order. New `spec_for_problem()` resolves the spec by deterministic problem
  slug; `radar full` and the daemon both use it.
- **Work queue** — new `approved_tickets()` returns the full priority-sorted
  queue (`pick_approved_ticket` is now a thin wrapper) so the daemon can take
  N tickets per tick instead of one.

## Why it's safe

- Checkpoints, pending gates, and decisions are already keyed by problem —
  concurrent loops never share state.
- Vault index/board files are full rewrites (benign last-writer-wins) and
  vault auto-commits hold `_VAULT_LOCK`.
- `max_parallel_loops: 1` restores the previous inline, one-at-a-time
  behavior (tests use this for determinism).

## Tests

- `test_daemon_fans_out_parallel_loops` — two approved tickets start two
  threaded loops in one tick, each pausing at its own gate 1.
- `test_spec_for_problem_matches_slug_not_mtime` — spec resolution keys off
  the problem slug, not file mtime.
