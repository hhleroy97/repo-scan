---
type: "changelog"
date: 2026-06-10
tags:
  - changelog
  - radar
  - hub
  - llm
---

# 2026-06-10 — Agent factory: model routing, usage ledger, radar top, parallel acts

> [!success] One frontier judge, many cheap workers
> The expensive model now does the thinking (analyze, audit); composer-class
> models do the labor (act, act_fix) — one agent per ticket, in parallel,
> each in an isolated worktree. Every token is accounted for.

## Model routing (`llm_roles`)

- `complete()` grew a `role` parameter; config maps roles to models:
  `{"llm_roles": {"act": "composer-2.5", "act_fix": "composer-2.5"}}`
- Routing appends `--model <name>` to the agent CLI per call. Roles:
  `research`, `analyze`, `draft`, `audit`, `act`, `act_fix`.
- Default backends switched to `--output-format json`: same text out, plus
  the CLI's real usage envelope in.

## Usage ledger

- Every LLM call appends to `docs/.radar/usage.jsonl`: role, model, backend,
  real input/output/cache token counts (parsed from cursor-agent and claude
  JSON envelopes), duration, and reported cost when the CLI provides it.
  Plain-text backends fall back to a chars/4 estimate flagged `estimated`.
- `usage_summary()` aggregates totals, today, by-role, by-model; it ships in
  the `/api/state` payload, renders as a card in the web dashboard, and as a
  panel in `radar top`.

## radar top — terminal dashboard

- Stdlib curses TUI over the same `build_state()` the phone sees: scan
  stats, pending gates, runs, actionable tickets, the LLM usage panel, and
  the decision trail.
- `j/k` move, `a` approve, `r` reject (gates via the decision inbox — same
  multi-writer primitive as the web dashboard — tickets via the ticket API),
  `enter` opens gate detail, `q` quits. Pure render/action helpers are
  separated from the curses loop and unit-tested.

## Parallel acts — one agent per ticket

- Daemon-scheduled acts now run in isolated git worktrees under
  `~/.cache/repo-scan/worktrees/<repo>-<ticket>/`, one per `radar/<ticket>`
  branch — agents never touch the main checkout and never collide.
- `daemon_tick` fans out up to `max_parallel_acts` (default 2) act threads
  per tick; research loops stay serialized (they share the vault). Worktrees
  are pruned after a successful commit, kept on failure for inspection.
- Pending gate files are now keyed by (gate, problem) so concurrent runs
  paused at the same gate never clobber each other; legacy un-keyed files
  are still honored and swept.
- `runs.json` writes are lock-guarded; run records carry `kind` (loop/act).
- `radar act --worktree` exposes the isolated mode manually.

## Tests

16 new (8 routing/envelope/ledger, 7 TUI, parallel fan-out + worktree
isolation in the act suite, refreshed pending-file assertions): 164 passing.
