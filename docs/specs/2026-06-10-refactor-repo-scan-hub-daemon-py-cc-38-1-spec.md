---
type: "spec"
problem: "Refactor repo_scan/hub/daemon.py (CC 38, 11 commits, untested). `repo_scan/hub/daemon.py` is both high-churn (11 commits) and high-complexity (total CC 38) with no matching test file. Acceptance criteria: Complexity of every function below rank C; Test file exists and passes; Trend delta confirms complexity drop. Research current best practices and draft a spec for this work."
status: "draft"
audit_verdict: "revise"
analysis: "[[2026-06-10-refactor-repo-scan-hub-daemon-py-cc-38-1-analysis]]"
drafted_at: "2026-06-10 13:26 UTC"
---

# Spec — Refactor repo_scan/hub/daemon.py (CC 38, 11 commits, untested). `repo_scan/hub/daemon.py` is both high-churn (11 commits) and high-complexity (total CC 38) with no matching test file. Acceptance criteria: Complexity of every function below rank C; Test file exists and passes; Trend delta confirms complexity drop. Research current best practices and draft a spec for this work.
_Drafted 2026-06-10 13:26 UTC by radar — **status: draft**_

I'll read `daemon.py`, related tests, and existing refactor specs so the revised spec matches repo patterns and fixes the audit issues.
## Goal

Lower cyclomatic complexity in `repo_scan/hub/daemon.py` so every function is radon rank B or better (CC ≤ 10). The sole rank-C+ hotspot is `daemon_tick` (CC 38, rank E); all other functions are already compliant (`over_budget` highest at CC 8). Preserve scheduler semantics: tick order resume → mid-flight guard → scheduled scan when idle → budget gate for new work → act fan-out → loop fan-out (with phase-local early returns), file-backed state, threaded `_spawn` behavior, and public signatures (`daemon_tick`, `cmd_daemon`, `commit_vault`, `over_budget`, `reclaim_orphan_runs`). Daemon behavior is already covered in 11+ cases across `tests/test_hub.py`, `tests/test_act.py`, and `tests/test_intent_governance.py`; the gap is a dedicated `tests/test_daemon.py`, not zero coverage.

## Approach

Follow the repo's sources-style precedent: baseline snapshot, migrate tests into a dedicated module, then Fowler Decompose Conditional on `daemon_tick` only.

**Phase 0 — Baseline (before edits).** Run `radon cc -s -a repo_scan/hub/daemon.py`. Copy `docs/scan.json` outside `docs/` (e.g. `/tmp/daemon-cc-baseline.json`). Record derived `cc_by_file` for `repo_scan/hub/daemon.py` (currently 38 — sole rank-C+ function) and `docs/reports/health.md` hotspot row for `daemon_tick`. No dogfood re-scan until Phase 3.

**Phase 1 — Tests (no production refactor).** Add `tests/test_daemon.py` by migrating and extending daemon coverage from `tests/test_hub.py`, `tests/test_act.py`, and `tests/test_intent_governance.py` (including `commit_vault` cases). Pin `max_parallel_acts=1` and `max_parallel_loops=1` for deterministic scheduler assertions; clear `daemon._run_threads` in fixtures between cases. Full pytest green against current code.

**Phase 2 — Extract `daemon_tick` (one helper per commit; pytest after each).** Decompose the orchestrator into private helpers that own the branches radon counts. Helpers need not mirror the module docstring's four numbered phases — the docstring omits mid-flight guard and budget gate; code has six logical steps:

1. `_prune_finished_threads()` — dead-thread cleanup from `_run_threads`
2. `_resume_gate_waiting_runs(root, cfg, …) -> list[str]` — resume phase; on any resume, refresh `active`/`busy` before downstream phases
3. `_tick_midflight_guard(active, busy, actions) -> list[str] | None` — return `actions` early when foreign-owned `queued`/`running` runs exist
4. `_maybe_run_scheduled_scan(root, cfg, actions) -> list[str] | None` — scan when idle; **return immediately** (skip budget, act, loop) when scan runs
5. `_apply_budget_gate(root, cfg, actions) -> list[str] | None` — notify-once daily budget block; return early when over budget
6. `_fan_out_acts(root, cfg, …) -> list[str]` — act fan-out; **return immediately** when any act starts (loop fan-out skipped same tick)
7. `_fan_out_loops(root, cfg, …) -> list[str]` — loop fan-out

Parent `daemon_tick` becomes a thin sequential coordinator; early returns and cross-phase state refresh unchanged. Do **not** refactor `_run_loop` / `_run_act` — already rank B and not on the acceptance gate.

**Phase 3 — Verify.** Restore Phase 0 `scan.json` copy immediately before dogfood re-scan. Re-run `radon cc -s -a` and self-scan; compare `cc_by_file`, `health.md` hotspot row, and `index.md` `cc_movers` vs Phase 0 baseline.

## Changes

- **`tests/test_daemon.py`** (new) — Migrated daemon tests plus phase-focused cases; shared fixtures stubbing `cmd_loop`, `cmd_act`, `scan`, `notify`, and thread spawning where needed.
- **`tests/test_hub.py`**, **`tests/test_act.py`**, **`tests/test_intent_governance.py`** — Remove migrated daemon tests (including `test_commit_vault_*`); retain hub server/inbox, act pipeline, and non-daemon governance tests.
- **`repo_scan/hub/daemon.py`** — Phase 2 only: phase helpers above; slim `daemon_tick`; no signature or observable tick-order changes.
- **`repo_scan/hub/state.py`**, **`repo_scan/radar/pipeline.py`**, **`repo_scan/radar/act.py`**, **`repo_scan/scanner.py`** — No changes expected.
- **`docs/scan.json`**, **`docs/reports/health.md`**, **`docs/index.md`** — Updated by Phase 3 self-scan after baseline restore, not hand-edited.

## Tests

| Acceptance criterion | Automated verification |
|----------------------|------------------------|
| Complexity of every function below rank C | `radon cc -s -a repo_scan/hub/daemon.py` — no function rank C+; `daemon_tick` and each new `_`-helper CC ≤ 10; `over_budget` must not regress above 10. |
| Test file exists and passes | `pytest tests/test_daemon.py` — all tests green. |
| Trend delta confirms complexity drop | Phase 0: derived `cc_by_file` = 38, `health.md` cites `daemon_tick`. Phase 3: after baseline restore + re-scan, derived `cc_by_file` is 0, hotspot row cleared, `index.md` `cc_movers` shows drop vs Phase 0. |

**`tests/test_daemon.py` inventory (migrated + new):**

| Area | Test names |
|------|------------|
| Full tick cycle | `test_daemon_full_cycle`, `test_daemon_scheduled_scan` |
| Resume / orphans | `test_reclaim_orphan_runs_resurrects_work`, `test_daemon_tick_survives_live_act_thread` |
| Fan-out | `test_daemon_fans_out_parallel_loops`, `test_daemon_fans_out_parallel_acts`, `test_daemon_runs_act_for_inprogress_ticket` |
| Budget | `test_over_budget_tokens`, `test_over_budget_acts_per_day`, `test_daemon_blocks_new_work_when_over_budget` |
| Vault | `test_commit_vault_commits_docs_only`, `test_commit_vault_noop_when_clean_or_disabled` |
| Phase isolation (new) | `test_resume_phase_skips_busy_runs`, `test_scan_phase_skips_when_threads_alive`, `test_midflight_blocks_new_work`, `test_act_fanout_skips_loop_same_tick` |

Assert scheduler behavior via `daemon_tick` and public helpers (`over_budget`, `reclaim_orphan_runs`, `commit_vault`); do not add direct tests of private `_run_loop` / `_run_act`.

**Regression surface (green throughout):** `pytest tests/test_daemon.py tests/test_hub.py tests/test_act.py tests/test_intent_governance.py`.

## Documentation

- **`repo_scan/hub/daemon.py` module docstring** — Extend numbered list to include mid-flight guard and budget gate (or add a "tick internals" note) so docstring matches code; keep four user-facing phases explicit where possible.
- **Phase helpers** — One-line docstrings: step role, inputs, and early-return conditions (especially scan/act same-tick returns and post-resume state refresh).
- **`tests/test_hub.py` module docstring** — Remove daemon section reference after migration.
- **README / contributor docs** — No change unless a testing section lists per-module test files; then add `tests/test_daemon.py` entry.

## Risks

- Module-level `_run_threads` and `_VAULT_LOCK` make ordering-sensitive tests flaky without `max_parallel_*=1` and thread cleanup between cases.
- Cosmetic extraction (moving loops without relocating conditionals) will not lower `daemon_tick` CC; each helper must own counted branches.
- Losing act-phase or scan-phase early returns would allow loop fan-out in the same tick — characterize before extraction.
- `cmd_daemon` infinite loop is unsuitable for unit tests; scope verification to `daemon_tick` and extracted helpers.
- Dogfood re-scan without Phase 0 baseline restore confounds `cc_by_file` trend comparison.
- Hub coupling (`config.py` ↔ `daemon.py` ~58%) increases blast radius; one commit per extraction limits bisect cost.

## Out of scope

- Refactoring `cmd_daemon` polling loop or changing `daemon_poll_seconds` / `daemon_scan_hours` defaults.
- Consolidating `_run_loop` / `_run_act` outcome logic (already rank B; not required for acceptance).
- Changing budget governance rules, `max_parallel_acts` / `max_parallel_loops` semantics, or vault autocommit behavior.
- Thread-pool redesign, process-level daemonization, or replacing file-backed state.
- Refactoring `repo_scan/hub/state.py`, `notify.py`, or radar pipeline internals beyond import stability.
- E2E HTTP dashboard tests or full `cmd_loop` / `cmd_act` integration (remain in existing radar/act suites).
- Fixing pre-existing behavior surprises discovered during characterization (file separate tickets).

## Audit

> [!warning] Audit verdict: revise
> Radon baselines, test migration inventory, and Fowler decomposition direction match the repo and code, but scheduler early-return semantics, parallel-test fixture wording, and Phase 3 verification need tightening before human review.
> - Act-phase early return is mischaracterized: after act fan-out the code is `if actions: return actions`, which fires on any prior tick action (e.g. `resumed:*` from phase 1), not only when an act starts — `_fan_out_acts` contract and `test_act_fanout_skips_loop_same_tick` must assert this or loop fan-out can regress.
> - Phase 1 fixture guidance contradicts retained tests: blanket pin `max_parallel_acts=1` and `max_parallel_loops=1` conflicts with `test_daemon_fans_out_parallel_loops` and `test_daemon_fans_out_parallel_acts`, which require `max_parallel_* = 2`.
> - Phase 3 trend verification overstates `index.md`: `cc_movers` / trend callout only surfaces top movers (pipeline spec audit); assert derived `cc_by_file` from the Phase 0 baseline artifact vs post-restore `scan.json`, not a visible index callout line.
> - Phase 3 omits the concrete dogfood re-scan command sibling refactor specs require (e.g. `repo-scan` / `python -m repo_scan.cli scan`).
> - No sub-split contingency for `_fan_out_acts`: nested `_alive` plus the act-selection loop may stay rank C after one extraction — sources/languages specs require sub-split before proceeding.
> - Act vs loop slot counting is asymmetric (`_alive` uses thread intersection; loop fan-out counts non-act queued/running in state) — not called out; naive extraction could change scheduling capacity.
> - Documentation migration is incomplete: only `tests/test_hub.py` module docstring is listed; `tests/test_act.py` and `tests/test_intent_governance.py` also own migrated daemon/budget imports and section comments.
> - Internal inconsistency: prose cites six logical tick steps but the helper list numbers seven items (1–7).
> - Missing risk from sibling audits: concurrent rank-C hotspot changes on the branch between Phase 0 and Phase 3 can confound `cc_movers` ordering despite baseline restore.
> - Phase 0 `cc_by_file` = 38 should state derivation (sum `complexity[]` rows for the file under `complexity_min_rank: C`; for `daemon.py` that is currently only `daemon_tick`).
> - Linked analysis recommends unifying `_run_loop`/`_run_act` before decomposing `daemon_tick`; spec out-of-scopes that but does not note intentional divergence from the analysis recommendation.

## Provenance

- analysis: [[2026-06-10-refactor-repo-scan-hub-daemon-py-cc-38-1-analysis]]
