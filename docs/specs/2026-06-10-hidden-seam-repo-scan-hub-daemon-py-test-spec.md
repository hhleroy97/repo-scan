---
type: "spec"
problem: "Hidden seam: repo_scan/hub/daemon.py <-> tests/test_act.py (70% coupled). `repo_scan/hub/daemon.py` and `tests/test_act.py` changed together in 7 commits (70% degree) but share no import edge — an implicit contract the dependency graph can't see. Acceptance criteria: Make the dependency explicit (shared module or import); Coupling degree drops below threshold in coupling.md. Research current best practices and draft a spec for this work."
status: "approved"
audit_verdict: "revise"
analysis: "[[2026-06-10-hidden-seam-repo-scan-hub-daemon-py-test-analysis]]"
drafted_at: "2026-06-10 21:55 UTC"
---

# Spec — Hidden seam: repo_scan/hub/daemon.py <-> tests/test_act.py (70% coupled). `repo_scan/hub/daemon.py` and `tests/test_act.py` changed together in 7 commits (70% degree) but share no import edge — an implicit contract the dependency graph can't see. Acceptance criteria: Make the dependency explicit (shared module or import); Coupling degree drops below threshold in coupling.md. Research current best practices and draft a spec for this work.
_Drafted 2026-06-10 21:55 UTC by radar — **status: approved**_

Reviewing the codebase and coupling docs so the spec matches current structure and conventions.
Reviewing the codebase and coupling docs so the spec matches current structure and conventions.

## Goal

Close tkt-0018: make the implicit daemon↔act contract visible where static analysis can see it, and reduce git co-change until `repo_scan/hub/daemon.py` ↔ `tests/test_act.py` is **absent** from `coupling.md` (degree strictly below `coupling_min_degree` 50%). **Baseline (scan 2026-06-10 21:18 UTC):** 8 shared, 67% degree (~24 rev sum), import edge **none**. **Partial remediation landed:** `hub.act_run`, `daemon → act_run` orchestration, `tests/test_hub_act_run.py` (daemon/contract/coupling fixture), `tests/support/act_fixtures.py`. **Remaining:** wire `test_act → act_run` for `ACT_RC_*` only—not `run_act` orchestration—so AC1 is asymmetric vs tkt-0016 (`config`+`daemon → settings`) but satisfies shared-module precedent. Hidden-seam banner persists until AC2. **Human reviewer:** confirm ticket AC1 accepts import-graph closure via `act_run` without banner removal; AC2 may stay open post-merge (per tkt-0016).

## Approach

Treat `repo_scan/hub/act_run.py` as canonical hub adapter (**done**). Finish AC1: `test_act → act_run` imports `ACT_RC_SUCCESS` / `ACT_RC_PAUSED` for `cmd_act` return-code assertions—named RC surface shared with daemon orchestration, not a second orchestration consumer. Ownership: `test_act.py` = `cmd_act` behavior; `test_daemon.py` = `daemon_tick` integration; `test_hub_act_run.py` = hub adapter contract. **AC2** requires pair **absent** from `analyze_history` (exactly 50% still lists). Merge-time fixture proves decoupling math; live `coupling.md` is **not merge-gated**. **Live AC2 math (baseline 8 shared):** one co-touch → 9 shared (~69%); then **≥10** solo `test_act`-only commits still round to 50% (listed)—need **≥11** solo commits for strictly &lt;50%, or avoid co-touch and accumulate **≥10** solo commits from current baseline. Split commits: never touch `daemon.py`, `test_act.py`, and `test_daemon.py` together; `act_run.py`-only commits do not move this pair's degree.

## Changes

- **`repo_scan/hub/act_run.py`** — **done**; verify module docstring documents RC semantics and injected `commit_vault` hook.
- **`repo_scan/hub/daemon.py`** — **done**; verify `_run_act` thin delegate to `run_act`.
- **`tests/test_hub_act_run.py`** — **done** except `test_act_imports_act_run` (add).
- **`tests/support/act_fixtures.py`** — **done**; verify shared fixtures; no further duplication.
- **`tests/test_act.py`** — **remaining:** `from repo_scan.hub.act_run import ACT_RC_PAUSED, ACT_RC_SUCCESS`; replace `cmd_act(...) == 0` / `== 2` with constants (leave non-RC literals, e.g. `counter.txt` count `== 2`, unchanged).
- **`tests/test_daemon.py`** — no changes; full suite must pass.
- **`docs/tickets/tkt-0018.md`** — baseline 67%/8 shared; AC1 = both consumers import `act_run` (orchestration vs RC-only); AC2 = post-merge rescan.
- **Regenerated scan docs** (after sufficient divergent history) — `docs/reports/coupling.md`, `docs/scan.json`, dependency-graph artifacts.

## Tests

| Acceptance criterion | Automated test |
|---|---|
| Explicit dependency (shared module) | `test_hub_act_run.py::test_daemon_imports_act_run` — **done** |
| Explicit dependency (shared module) | `test_hub_act_run.py::test_act_imports_act_run` — **add:** `test_act.py` imports `hub.act_run`; `cmd_act` RC assertions use `ACT_RC_*` (AST scoped to `cmd_act(...)` compare nodes; permit other `== 0`/`== 2`) |
| Explicit dependency (shared module) | `test_hub_act_run.py::test_act_run_module_contract` — **done** |
| Act-run contract preserved | `test_hub_act_run.py::test_act_run_rc_constants` — **done** |
| Act-run contract preserved | `test_hub_act_run.py::test_act_run_outcome_mapping` — **done** |
| Coupling degree below threshold | `test_hub_act_run.py::test_daemon_test_act_degree_below_threshold` — **done** (fixture: 7 pair, 6 `test_act`-only, 5 `daemon`-only, 1 co-touch, ≥6 `test_act`-only decouple → absent) |
| Coupling degree below threshold | Post-rescan (manual): after **≥11** live `test_act`-only commits if refactor co-touches both (**≥10** if no co-touch from baseline); pair absent from coupling table |
| No regression | `tests/test_act.py`, `tests/test_daemon.py` — full suites pass |

## Documentation

- **`repo_scan/hub/act_run.py`** — module docstring: hub adapter; RC semantics, state transitions, injected vault hook (**verify**).
- **`repo_scan/hub/daemon.py`** — `_run_act` docstring points to `act_run.run_act` (**verify**).
- **`tests/support/act_fixtures.py`** — module docstring: shared act/daemon scaffolding (**verify**).
- **`docs/tickets/tkt-0018.md`** — reconcile ticket "70%" to live 67%; AC1 import-only, not banner clearance.
- Regenerated coupling and dependency-graph artifacts after rescan.

## Risks

- `test_act → act_run` (RC constants only) does not import `run_act`; hidden-seam banner persists until AC2 (by design).
- Co-touch refactor 8→9 shared; live AC2 needs **≥11** solo `test_act` commits (or **≥10** without co-touch)—not the fixture's ≥6.
- `act_fixtures` edits in the same PR as `test_act` RC wiring can produce multi-file test commits and sustain `test_act`↔`test_daemon` co-evolution (different pair).
- Landing RC wiring + fixture churn in one commit inflates shared count; prefer split commits.
- Over-growing `act_run` blurs hub↔radar layering; keep it a thin adapter.

## Out of scope

Re-extracting `_run_act` (**done**); `cmd_act` / worktree / gate pipeline refactors; unifying `_run_loop` / `_run_act` helpers; `test_intent_governance.py` fixture consolidation; import-linter layer rules; other hidden seams; changing `coupling_min_degree` / `hidden_seams` semantics; amending ticket AC1 wording without reviewer sign-off.

## Audit

> [!warning] Audit verdict: revise
> The spec correctly incorporates audit feedback (test_act→act_run, partial remediation status, AC1/AC2 split, post-co-touch ≥11 math) but should be revised for the no-co-touch AC2 threshold and tightened on what AC1 does and does not change in coupling.md before human review.
> - Live AC2 no-co-touch math is wrong: with verified baseline (shared=8, daemon≈14 revs, test_act≈10 revs from scan.json), nine solo test_act-only commits yield 48% (pair absent); ten yield 47%. The spec claims '≥10 solo commits still round to 50%' and 'need ≥10 if no co-touch'—both contradict behavior.analyze_history (round(100*shared/avg_revs)).
> - Post-co-touch AC2 math (≥11 solo after shared 8→9) is correct and consistent with the formula; the no-co-touch error is not a symmetric off-by-one but a factual misstatement about what ten solo commits produce.
> - Partial remediation is accurately scoped (act_run, daemon delegate, act_fixtures, test_hub_act_run minus test_act_imports_act_run), but the spec understates the preferred landing path: RC-only wiring in test_act.py alone avoids a co-touch bump and lowers live AC2 to ≥9 solo commits rather than ≥11.
> - AC1 remains asymmetric vs tkt-0016 (production imports run_act; test_act imports RC constants only): spec acknowledges this and flags reviewer sign-off, but should state explicitly that daemon↔test_act still has no direct import edge and the coupling.md 'none — seam' column persists until AC2 removes the row—not merely the hidden-seam banner.
> - Fixture history starts at 7 shared co-touch commits while live baseline is already 8 shared (67%); the spec cites live 8/67% in Goal but does not note that the coupling fixture's opening state is stale relative to scan.json—implementers may misread whether one more co-touch is already baked in.
> - Missing risk: RC constants in act_run can drift from cmd_act semantics; test_act_run_rc_constants guards values but not that cmd_act still returns those codes—future act.py RC changes could re-couple daemon and test_act without touching act_run.
> - Missing risk: test_act_imports_act_run AST scoping (cmd_act(...) compare nodes only) can be bypassed by refactors that assign cmd_act output before assert, weakening AC1 enforcement without failing the new test.

## Provenance

- analysis: [[2026-06-10-hidden-seam-repo-scan-hub-daemon-py-test-analysis]]
