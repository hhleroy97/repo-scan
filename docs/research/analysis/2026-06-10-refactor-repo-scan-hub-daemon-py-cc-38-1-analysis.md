---
type: "analysis"
problem: "Refactor repo_scan/hub/daemon.py (CC 38, 11 commits, untested). `repo_scan/hub/daemon.py` is both high-churn (11 commits) and high-complexity (total CC 38) with no matching test file. Acceptance criteria: Complexity of every function below rank C; Test file exists and passes; Trend delta confirms complexity drop. Research current best practices and draft a spec for this work."
confidence: "high"
sources: ["url-refactoring-com-catalog-decomposeconditional-html", "url-refactoring-com-catalog-consolidateduplicateconditionalfragm"]
generated_at: "2026-06-10 13:16 UTC"
linked_files: ["repo_scan/hub/daemon.py", "tests/test_act.py", "tests/test_daemon.py", "tests/test_hub.py", "tests/test_intent_governance.py"]
---

# Analysis — Refactor repo_scan/hub/daemon.py (CC 38, 11 commits, untested). `repo_scan/hub/daemon.py` is both high-churn (11 commits) and high-complexity (total CC 38) with no matching test file. Acceptance criteria: Complexity of every function below rank C; Test file exists and passes; Trend delta confirms complexity drop. Research current best practices and draft a spec for this work.
_Generated 2026-06-10 13:16 UTC — confidence: high_

## Findings

- Radon confirms a single hotspot: `daemon_tick` is rank E (CC 38); every other function in `repo_scan/hub/daemon.py` is already rank B or better (highest non-tick is `over_budget` at CC 8).
- `daemon_tick` is a four-phase sequential orchestrator (resume gate-waiting runs → scheduled scan when idle → budget gate for new work → act fan-out → loop fan-out) with early returns and nested conditionals—the exact shape Fowler's Decompose Conditional targets via named phase predicates and branch helpers.
- `_run_loop` and `_run_act` duplicate nearly identical rc→status/notify branching (rc 0 / rc 2 with gate vs stopped / failure); Slide Statements + consolidate-duplicate-fragments is the low-risk first extraction before touching the orchestrator.
- Coverage is partial and scattered across `tests/test_hub.py`, `tests/test_act.py`, and `tests/test_intent_governance.py` (daemon_tick cycles, parallel fan-out, scheduled scan, over_budget, reclaim_orphan_runs)—not a dedicated `tests/test_daemon.py`, which blocks the ticket's 'test file exists' criterion despite meaningful behavioral tests already existing.
- The repo's established refactor playbook (writers/scanner/sources specs) applies directly: radon + `docs/scan.json` baseline snapshot before edits, characterization tests before or alongside extraction, one helper per commit, full pytest after each step, then dogfood re-scan for trend/cc_by_file delta.
- Acceptance 'below rank C' means every function must reach radon rank B or better (CC ≤ 10); decomposing `daemon_tick` alone satisfies the complexity gate—no changes required to already-compliant helpers unless consolidation of run-outcome logic introduces a new shared helper that must stay ≤ 10.
- Module-level mutable state (`_run_threads`, `_VAULT_LOCK`) and threaded `_spawn` paths increase regression risk; tests must pin `parallel=False` or mock threads when asserting scheduler decisions, and clear `_run_threads` between cases.

## Recommendation

Follow the repo's characterization-then-extract playbook: snapshot radon output and a copy of `docs/scan.json`, then add `tests/test_daemon.py` by migrating and extending existing hub/act/governance daemon tests to cover each `daemon_tick` phase and the consolidated run-outcome paths. First unify `_run_loop`/`_run_act` outcome handling into a shared helper, then decompose `daemon_tick` into one phase function per numbered step in its docstring; re-run radon and a dogfood scan to confirm every function is rank B or better and `cc_by_file` for `repo_scan/hub/daemon.py` drops in trend delta.

## Risks

- Threading and process-global `_run_threads` can cause order-dependent or flaky tests if parallel spawn is not controlled or state is not reset between cases.
- Extracting phase helpers without moving the conditionals radon counts (cosmetic loop moves) will not lower `daemon_tick` CC and may add churn without meeting rank B.
- Consolidating `_run_loop`/`_run_act` outcome logic risks subtle notification/message regressions unless existing integration tests are migrated before refactor.
- Dogfood re-scan for trend delta mutates `docs/scan.json` and related reports; baseline must be copied outside `docs/` before any scan, matching prior audit lessons from scanner/sources refactors.
- Heavy imports (`radar.pipeline`, `radar.act`, `scanner.scan`) require monkeypatch seams; incomplete stubbing can yield false greens or hide scheduler regressions in fan-out and budget paths.

## Evidence

- [[url-refactoring-com-catalog-decomposeconditional-html\|Decompose Conditional]]
- [[url-refactoring-com-catalog-consolidateduplicateconditionalfragm\|Slide Statements]]
- research run: [[2026-06-10-refactor-repo-scan-hub-daemon-py-cc-38-1]]
