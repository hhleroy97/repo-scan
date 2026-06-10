---
type: "changelog"
date: "2026-06-10"
tags: [changelog, radar, tickets, governance]
---

# Intent intake, executable acceptance criteria, governance

Three pillars that turn the maintenance loop into a feature loop: ideas get
in, "done" is executable, and autonomy is bounded by policy.

## 1 — Intent intake (human idea -> first-class ticket)

- `new_ticket()` in `repo_scan/tickets.py`: a title (plus optional why,
  priority, criteria, kind) becomes a `feature` ticket with
  `origin: human`, `source: intent`, fingerprint `feature:<title-slug>` —
  re-submitting the same idea dedups instead of duplicating.
- CLI: `repo-scan tickets new "Add CSV export" --why ... --criterion ...
  --priority high --approve`.
- Dashboard: "New idea" composer at the top of the Tickets tab
  (`POST /api/ticket/new`) — capture intent from the phone; the daemon picks
  the ticket up like any scan-proposed one.

## 2 — Executable acceptance criteria

- `parse_ticket` now extracts the `- [ ]` criteria list; `ticket_problem`
  appends "Acceptance criteria: ..." so they ride into research, analysis,
  and the spec.
- `DRAFT_PROMPT` requires the spec's `## Tests` section to map each
  criterion to a concrete automated test (file + name) — tests are the
  definition of done.
- Act enforcement (`require_tests_for_kinds`, default `["feature"]`): if the
  implementation changed no test files, one dedicated acceptance round
  (`ACCEPTANCE_PROMPT`) asks the agent to add the spec's tests; still none
  and the run stops with outcome `no-acceptance-tests`, branch kept.

## 3 — Governance

- **Daily budgets** (`budget_daily_tokens`, `max_acts_per_day`):
  `over_budget()` in the daemon reads the usage ledger and today's act runs;
  over the cap, the tick stops *starting* new work (resumes still finish),
  notifies once per day, and logs a budget event.
- **Protected paths** (`protected_paths`, fnmatch globs): an implementation
  touching a match forces `post_implement` to `prompt` even when configured
  `auto`, and the gate payload lists the files.
- **Per-kind autonomy** (`gates_by_kind`): gate overrides keyed by ticket
  fingerprint prefix (`refactor:`, `feature:`...), merged per act run via
  `gates_for_kind()` — trust earned per work type, not globally.

## Tests

`tests/test_intent_governance.py` — 15 offline tests: intake (CLI, dedup,
criteria in body/board), criteria-in-problem, acceptance enforcement (stop,
retry-round success, non-feature exemption), kind parsing, gate merging,
protected-path forcing, both budget caps, and daemon budget blocking with
once-a-day notification. Full suite: 185 passed.
