---
type: "spec"
problem: "Hidden seam: repo_scan/hub/daemon.py <-> tests/test_act.py (70% coupled). `repo_scan/hub/daemon.py` and `tests/test_act.py` changed together in 7 commits (70% degree) but share no import edge — an implicit contract the dependency graph can't see. Acceptance criteria: Make the dependency explicit (shared module or import); Coupling degree drops below threshold in coupling.md. Research current best practices and draft a spec for this work."
status: "draft"
audit_verdict: "revise"
analysis: "[[2026-06-10-hidden-seam-repo-scan-hub-daemon-py-test-analysis]]"
drafted_at: "2026-06-10 19:23 UTC"
---

# Spec — Hidden seam: repo_scan/hub/daemon.py <-> tests/test_act.py (70% coupled). `repo_scan/hub/daemon.py` and `tests/test_act.py` changed together in 7 commits (70% degree) but share no import edge — an implicit contract the dependency graph can't see. Acceptance criteria: Make the dependency explicit (shared module or import); Coupling degree drops below threshold in coupling.md. Research current best practices and draft a spec for this work.
_Drafted 2026-06-10 19:23 UTC by radar — **status: draft**_

Verifying key facts in the codebase so the revised spec matches reality.
## Goal

Close tkt-0018: name the implicit daemon→`cmd_act` orchestration contract (worktree invocation, vault commit, RC 0/2/other → run state, gates, notifications) as an explicit hub module so the dependency graph shows import edges, and reduce git co-change until `repo_scan/hub/daemon.py` ↔ `tests/test_act.py` is **absent** from `coupling.md` (degree strictly below `coupling_min_degree` 50%). **Baseline (live scan):** 7 shared commits, 64% degree (~13 daemon / ~9 `test_act` revs), import edge **none**. **Fixture baseline (synthetic):** same 7 shared with 6 `test_act`-only + 5 `daemon`-only → ~56% (round(700/12.5)), not 64%. Per tkt-0016 precedent, AC1 is satisfied by shared `hub.act_run` with edges `daemon → act_run` and `test_hub_act_run → act_run`, not a direct `daemon → test_act` import. **AC1 does not clear the hidden-seam banner** at merge: `hidden_seams` checks direct edges only; the daemon↔`test_act` row remains until AC2 (pair absent from coupling output). Ticket AC1 prose still reads like seam clearance — **human reviewer:** confirm shared-module reinterpretation and that AC1 closure is import-graph only, not banner removal.

## Approach

Extract `_run_act` body into `repo_scan/hub/act_run.py`: invoke `cmd_act(..., worktree=True)`, vault commit in `finally`, map RC to `update_run` / `append_event` / `notify`. Inject `pending_gate_for`, `dashboard_url`, and **`commit_vault`** callables from the `_run_act` wrapper (same pattern as tkt-0016 `cfg_hub` — **no** `act_run` import from `daemon`, avoiding `daemon ↔ act_run` cycle). Land with contract tests asserting RC semantics and import edges. **AC2** requires pair **absent** from `analyze_history` output (exactly 50% still lists). Merge-time fixture proves decoupling math; live `coupling.md` compliance is **not merge-gated** — ticket may stay open until post-merge divergent history + rescan. **Divergent commits must touch only `daemon.py` or only `test_act.py`** — `act_run.py`-only or `act_fixtures.py`-only commits do not move this pair’s degree. Fixture: 7 pair @ ~56%, co-touch refactor → 8 shared (~59% fixture / ~53% live with rev sum ~24); fixture needs **≥6** subsequent `test_act`-only (rev sum ~33); **live history after co-touch needs ~9+ `test_act`-only** (daemon≈14, test_act≈19 → degree &lt;50%), not ≥6. Consolidate duplicated act fixtures so pipeline work stops co-touching `test_act.py` when only daemon scheduling changes. **Coupling fixture tracked set** must include `act_run.py` (mirror tkt-0016 `settings.py` in `tracked`).

## Changes

- **`repo_scan/hub/act_run.py`** (new) — `ACT_RC_SUCCESS = 0`, `ACT_RC_PAUSED = 2`; `run_act(root, cfg, run, *, pending_gate_for, dashboard_url, commit_vault) -> int` owning invocation + outcome mapping; module docstring documents hub-owned act-run lifecycle.
- **`repo_scan/hub/daemon.py`** — `from .act_run import run_act`; `_run_act` thin delegate passing `_pending_gate_for`, `_dashboard_url`, and module-level `commit_vault`; no behavioral change to `daemon_tick` / `_spawn`.
- **`tests/support/act_fixtures.py`** (new) — shared `act_repo`, `feature_act_repo`, `_stub_agent`, `IMPLEMENT_AGENT`, `COUNTING_AGENT`; imported by `test_act.py` and `test_daemon.py` (drop local copies).
- **`tests/test_act.py`** — drop hub-orchestration tests; retain radar `cmd_act` coverage only (no `act_run` import).
- **`tests/test_hub_act_run.py`** (new) — import-edge AST checks, RC constants, outcome-mapping contract tests, coupling-degree fixture.
- **`docs/tickets/tkt-0018.md`** — baseline 64% live / ~56% fixture, 7 shared; AC1 import-only vs AC2 history; post-merge rescan note (~9+ live solo-side commits).
- **Regenerated scan docs** (after sufficient divergent history) — `docs/reports/coupling.md`, `docs/scan.json`, dependency-graph artifacts.

Do **not** refactor `_run_loop`, unify loop/act outcome helpers, or change `cmd_act` semantics.

## Tests

| Acceptance criterion | Automated test |
|---|---|
| Explicit dependency (shared module) | `tests/test_hub_act_run.py::test_daemon_imports_act_run` — `daemon.py` imports `hub.act_run`; `_run_act` delegates to `run_act`. |
| Explicit dependency (shared module) | `tests/test_hub_act_run.py::test_act_run_module_contract` — `act_run.py` exports RC constants and `run_act`; no import from `daemon`. |
| Act-run contract preserved | `tests/test_hub_act_run.py::test_act_run_rc_constants` — `ACT_RC_SUCCESS`/`ACT_RC_PAUSED` match `cmd_act` return codes used in existing act tests. |
| Act-run contract preserved | `tests/test_hub_act_run.py::test_act_run_outcome_mapping` — temp repo + stub `cmd_act` + injected `commit_vault`: RC 0 → `done`, RC 2 + pending gate → `waiting-on-gate`, RC 2 without gate → `stopped`, other → `failed`. |
| Coupling degree below threshold | `tests/test_hub_act_run.py::test_daemon_test_act_degree_below_threshold` — temp git fixture, `tracked` includes `daemon.py`, `test_act.py`, **`act_run.py`**: **7** pair, **6** `test_act`-only, **5** `daemon`-only (~56%), **1** co-touch refactor, then **≥6** `test_act`-only (no `act_run.py`-only decouple commits); `analyze_history` → pair absent. |
| Coupling degree below threshold | Post-rescan (manual, after ~**9+** live `test_act`-only commits if refactor co-touches both): `daemon.py`↔`test_act.py` **absent** from coupling table and hidden-seam warning. |
| No regression | `tests/test_act.py`, `tests/test_daemon.py` — full suites pass unchanged behavior. |

## Documentation

- **`repo_scan/hub/act_run.py`** — module docstring: hub adapter between daemon run records and `radar.act.cmd_act`; documents RC semantics, state transitions, injected vault hook.
- **`repo_scan/hub/daemon.py`** — `_run_act` docstring points to `act_run.run_act` as orchestration owner.
- **`tests/support/act_fixtures.py`** — brief module docstring: shared act/daemon test scaffolding.
- **`docs/tickets/tkt-0018.md`** — remediation summary; reconcile ticket “70%” prose to live 64%; AC1 cannot clear hidden-seam banner without AC2.
- Regenerated coupling and dependency-graph artifacts after rescan.

## Risks

- Refactor commit co-touching `daemon.py` and `test_act.py` adds shared 7→8; live AC2 needs ~9+ solo-side commits, not the fixture’s ≥6.
- `act_run` importing `state`/`notify`/`radar.act` blurs hub↔radar layering; keep module a thin adapter, not a second `act.py`.
- Importing `commit_vault` from `daemon` inside `act_run` recreates a cycle — injection is mandatory.
- Fixture consolidation touches `test_act.py` in the same PR as `act_run` — schedule solo-side follow-ups before claiming AC2 on live history.
- AC2 closure not merge-gated; synthetic fixture can pass while live seam persists until divergent history accumulates.

## Out of scope

Unifying `_run_loop` / `_run_act` outcome helpers; `cmd_act` / worktree / gate pipeline refactors; consolidating `test_intent_governance.py` fixtures; pytestarch / import-linter layer rules (follow-on after `act_run` lands); other hidden seams (`config`↔`daemon`, `daemon`↔`test_hub`, `server`↔`ui`); changing `coupling_min_degree` / `hidden_seams` semantics; amending ticket AC1 wording without reviewer sign-off.

## Audit

> [!warning] Audit verdict: revise
> The spec tracks live scan data (7 shared, 64%, daemon≈13/test_act≈9) and tkt-0016 AC1/AC2 split well, but misidentifies where act/daemon tests live, contains a live post-refactor degree error, and proposes an AC1 closure path that does not connect `test_act.py` to the new shared module the way both sides of tkt-0016 did.
> - Changes claim `tests/test_act.py` will drop hub-orchestration tests, but that file only exercises `cmd_act` in isolation; daemon↔act integration (`daemon_tick`, fan-out, run-state assertions) lives in `tests/test_daemon.py` — misattributes the seam and omits required `test_daemon.py` fixture-import edits from the Changes list.
> - Post-refactor live math is wrong: with shared=8 and rev sum 24 (daemon≈14, test_act≈10 after one co-touch), `round(100*8/12)=67%`, not ~53%; the ≥9 solo `test_act`-only commits conclusion is correct but the intermediate figure contradicts `behavior.analyze_history` (same formula as tkt-0016).
> - AC1 is weaker than the cited tkt-0016 precedent: both `config` and `daemon` import `hub.settings`, but this spec only wires `daemon → act_run` and `test_hub_act_run → act_run`, leaving `tests/test_act.py` with no import path to the named contract — the daemon↔test_act pair stays a direct-edge seam on the import graph even after AC1.
> - Research analysis recommends a `test_act → act_run` contract import for dependency-graph visibility; the spec moves tests to `test_hub_act_run.py` without stating why that satisfies ticket AC1 for the `daemon↔test_act` pair specifically (not merely mirroring production-side extraction).
> - Co-change root cause is understated: analysis identifies duplicated `act_repo` / stub-agent fixtures across `test_act.py` and `test_daemon.py` as the main driver of historical co-touch; `act_run` extraction alone does not link those files — AC2 depends on fixture consolidation plus many post-merge solo commits, which should be the primary decoupling mechanism in Approach, not a side note.
> - Missing risk: landing fixture consolidation + `act_run` in one PR may produce a single commit touching `daemon.py`, `test_act.py`, and `test_daemon.py` (worse than the modeled one co-touch pair), and new `test_hub_act_run` outcome-mapping tests overlap existing `test_daemon_runs_act_for_inprogress_ticket` / parallel-act integration coverage — clarify what regressions the unit tests catch that integration tests do not.
> - `tests/support/` does not exist today; spec should note creating that package (e.g. `__init__.py`) so shared `act_fixtures` imports work under the repo's test layout.

## Provenance

- analysis: [[2026-06-10-hidden-seam-repo-scan-hub-daemon-py-test-analysis]]
