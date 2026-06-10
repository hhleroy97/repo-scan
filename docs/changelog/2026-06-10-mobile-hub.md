---
type: changelog
date: 2026-06-10
phase: hub
tags: [hub, daemon, dashboard, mobile]
---

# Mobile hub — daemon, decision inbox, phone dashboard

The loop no longer needs a terminal. A resident daemon runs scans and loops;
gates publish to a file-backed decision inbox that any surface can answer;
a zero-dependency web dashboard makes that surface your phone.

Research basis: GitHits landscape pass (HumanLayer's daemon/channel split and
approveFunctionCall API, Happy's relay architecture, claude-code-monitor's
mobile web UI, the Telegram gate pattern). We extended our existing
file-backed gates rather than adopting any of them — HumanLayer independently
converged on the same design.

## New: repo_scan/hub/

- **state.py** — run lifecycle records (queued -> running -> waiting-on-gate ->
  done/stopped/failed), decision inbox keyed by (problem, gate) with
  first-write-wins idempotency, per-stage loop checkpoints, daemon metadata,
  and a persistent dashboard token. All under `docs/.radar/` (gitignored).
- **daemon.py** — `radar daemon`: one tick resumes a paused run when its
  decision arrives, rescans on a schedule (default 6h, proposing tickets),
  or starts a loop for the next approved ticket. Survives restarts; state is
  all files.
- **server.py** — `radar serve`: stdlib ThreadingHTTPServer with bearer-token
  auth (query/header/cookie). GET /api/state, /api/doc (sandboxed to docs/);
  POST /api/gate, /api/ticket. Runs the daemon in a background thread by
  default.
- **notify.py** — best-effort ntfy push (optional `ntfy_topic` config):
  gate pauses, loop outcomes, new ticket proposals; taps deep-link to the
  dashboard.
- **ui.py** — single self-contained mobile-first HTML page (no build step,
  no CDN): Now / Gates / Tickets / Activity tabs, approve/reject buttons,
  full-document viewer, 12s polling.

## Pipeline changes

- Gates check the decision inbox before pausing — the dashboard and the
  terminal are equal writers. Inbox decisions record their source and comment
  in `decisions.md`.
- `cmd_loop` checkpoints each stage (research, analysis, draft, audit) to
  `.radar/checkpoints/`; resuming a paused loop replays zero completed LLM
  calls. Checkpoints and decisions clear when a loop fully ends.
- Gate payloads now carry the problem plus a mobile-sized detail block
  (confidence, findings, risks, audit issues, doc path).
- `ticket_problem()` extracted so cmd_full and the daemon key the same
  problem string (checkpoints/decisions stay aligned across surfaces).

## Remote access

Documented Tailscale as the transport: install on desktop + phone, open the
tokenized URL against the tailnet name. No relay server, no open ports, no
hosted infrastructure.

## Tests

17 new tests (`tests/test_hub.py`, plus a tightened pipeline resume test): decision
idempotency, run lifecycle, gate-inbox consumption (approve + reject),
checkpointed resume consuming zero research/analyze responses, full daemon
cycle (start -> gate1 -> resume -> gate2 -> done, ticket to in-progress),
scheduled scan staleness, server auth, state payload, gate/ticket POSTs,
doc-endpoint path sandboxing, ntfy payloads. 139 total, all passing.
