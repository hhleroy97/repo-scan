---
type: "analysis"
problem: "Hidden seam: repo_scan/hub/daemon.py <-> tests/test_act.py (70% coupled). `repo_scan/hub/daemon.py` and `tests/test_act.py` changed together in 7 commits (70% degree) but share no import edge — an implicit contract the dependency graph can't see. Acceptance criteria: Make the dependency explicit (shared module or import); Coupling degree drops below threshold in coupling.md. Research current best practices and draft a spec for this work."
confidence: "high"
sources: ["arxiv-2411.19099", "gh-zyskarch-pytestarch", "url-deviq-com-principles-explicit-dependencies-principle"]
generated_at: "2026-06-10 18:50 UTC"
---

# Analysis — Hidden seam: repo_scan/hub/daemon.py <-> tests/test_act.py (70% coupled). `repo_scan/hub/daemon.py` and `tests/test_act.py` changed together in 7 commits (70% degree) but share no import edge — an implicit contract the dependency graph can't see. Acceptance criteria: Make the dependency explicit (shared module or import); Coupling degree drops below threshold in coupling.md. Research current best practices and draft a spec for this work.
_Generated 2026-06-10 18:50 UTC — confidence: high_

## Findings

- The 64–70% co-change between daemon.py and test_act.py reflects an implicit orchestration contract: daemon._run_act invokes cmd_act with worktree=True and maps return codes (0/2/other) to run state, gates, vault commits, and notifications, while test_act.py exercises cmd_act in isolation with no import path to that orchestration layer.
- test_daemon.py already owns daemon↔act integration (daemon_tick fan-out, act-started actions, gate resume) but duplicates act_repo fixtures and stub-agent helpers from test_act.py, so feature work on the act pipeline tends to land in the same commits as daemon orchestration changes even when the production import graph shows daemon→act←test_act only.
- Per the tkt-0016 precedent in this repo, AC1 is satisfied by a shared production module with visible import edges (e.g. hub.act_run imported by daemon and test_act), not a direct daemon↔test_act import; AC2 requires the pair be absent from coupling.md (degree strictly below 50%), which may need post-merge divergent solo-side commits after any co-touching refactor.
- The Explicit Dependencies Principle and pytestarch both argue against hiding the daemon→act collaboration inside _run_act: publish the act-run lifecycle (RC semantics, state transitions, vault hook) as an explicit hub-owned API that tests can target without reaching into daemon internals.
- Co-change analysis research (arxiv-2411.19099) frames this as evolutionary coupling without structural edges—accurate for alerting but the fix is to extract and name the real contract, then separate test ownership so scheduling changes touch test_daemon.py and cmd_act behavior touches test_act.py, reducing future shared commits.

## Recommendation

Extract daemon's act orchestration from _run_act into repo_scan/hub/act_run.py (run invocation, RC→run-state mapping, vault commit wrapper) and have daemon import it; add a small contract test in test_act.py that imports act_run constants/helpers so the dependency graph shows test_act→act_run←daemon. Consolidate duplicated act fixtures into tests/support/act_fixtures.py, keep integration scenarios in test_daemon.py, and add a coupling-degree fixture test mirroring tkt-0016; optionally encode layer rules with pytestarch once the shared module lands.

## Risks

- A refactor commit touching daemon.py and test_act.py together will temporarily worsen coupling math until enough solo-side commits accumulate.
- Extracting too much logic into act_run.py may duplicate act.py concerns or blur hub vs radar layering boundaries.
- test_act importing a hub module for contract tests inverts the usual production dependency direction (hub depends on radar, not vice versa) unless act_run is kept as a thin adapter over cmd_act.
- Clearing the hidden-seam warning in coupling.md depends on import-graph analysis semantics—shared-module edges may not remove the daemon↔test_act row until co-change degree actually drops below 50%.
- Adding pytestarch introduces a new dev dependency the project does not yet use; contract tests in existing test files may suffice per repo precedent.

## Evidence

- [[arxiv-2411.19099\|Enhancing Software Maintenance: A Learning to Rank Approach for Co-changed Method Identification]]
- [[gh-zyskarch-pytestarch\|zyskarch/pytestarch — Test framework for software architecture based on imports between modules.]]
- [[url-deviq-com-principles-explicit-dependencies-principle\|Explicit Dependencies Principle]]
- research run: [[2026-06-10-hidden-seam-repo-scan-hub-daemon-py-test]]
