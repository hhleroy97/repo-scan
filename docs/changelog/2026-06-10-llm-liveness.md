---
type: "changelog"
date: "2026-06-10"
tags: [changelog, radar, llm]
---

# LLM liveness heartbeat + longer timeouts

A real feature loop (tkt-0010) hit the 420s `llm_timeout` mid-research —
and the only signal was a dead run. Two problems: the cap was too tight for
frontier-model research, and a silent in-flight call is indistinguishable
from a hang, so the human instinct is to assume the worst.

## Changes

- `llm.complete()` now runs the agent CLI under a poll loop instead of a
  blocking `subprocess.run`: while the process is alive it emits a heartbeat
  event every `llm_heartbeat_seconds` (default 120, new config key) —
  `research · composer-2.5 still working · 6m elapsed (pid alive, limit
  25m)` — into the shared agent feed, visible on the dashboard and
  `radar top`.
- Timeout enforcement is unchanged in spirit (process killed, `LLMError`)
  but the error message now points at the `llm_timeout` config key.
- Repo policy raised: `llm_timeout` 420 -> 1500s, `act_timeout` -> 2700s.
  A killed call loses that stage's work, so generous caps + heartbeats beat
  tight caps + retries.

## Tests

`test_complete_timeout_kills_and_raises` (slow backend killed at the cap)
and `test_complete_emits_heartbeat_while_running` (liveness events land in
the feed). Suite: 187 passed.
