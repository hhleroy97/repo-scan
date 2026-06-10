---
type: "analysis"
problem: "Hidden seam: repo_scan/hub/daemon.py <-> tests/test_act.py (70% coupled). `repo_scan/hub/daemon.py` and `tests/test_act.py` changed together in 7 commits (70% degree) but share no import edge — an implicit contract the dependency graph can't see. Acceptance criteria: Make the dependency explicit (shared module or import); Coupling degree drops below threshold in coupling.md. Research current best practices and draft a spec for this work."
confidence: "high"
sources: ["url-www-ime-usp-br-gerosa-papers-changecoupling-pdf", "url-docs-pytest-org-en-stable-reference-fixtures-html"]
generated_at: "2026-06-10 21:14 UTC"
linked_files: ["repo_scan/hub/daemon.py", "tests/support/act_fixtures.py", "tests/test_act.py", "tests/test_hub_act_run.py"]
---

# Analysis — Hidden seam: repo_scan/hub/daemon.py <-> tests/test_act.py (70% coupled). `repo_scan/hub/daemon.py` and `tests/test_act.py` changed together in 7 commits (70% degree) but share no import edge — an implicit contract the dependency graph can't see. Acceptance criteria: Make the dependency explicit (shared module or import); Coupling degree drops below threshold in coupling.md. Research current best practices and draft a spec for this work.
_Generated 2026-06-10 21:14 UTC — confidence: high_

## Findings

- Change-coupling research (Gerosa/Oliva) frames the daemon.py↔test_act.py pair as an evolutionary/logical dependency invisible to static import graphs—consistent with repo-scan's hidden-seam detector and the 64–70% degree over 7 shared commits.
- The implicit contract is daemon act orchestration: invoke cmd_act with worktree=True, commit vault artifacts in finally, and map RC 0/2/other to run state, gates, events, and notifications—behavior test_act.py exercises only at the cmd_act layer without any import path to that hub adapter.
- Co-change is amplified by duplicated act scaffolding: test_act.py and test_daemon.py both carry act_repo/stub-agent fixtures and evolve together when act pipeline behavior changes, even though production edges are daemon→act_run→radar.act and radar.act←test_act.
- Partial remediation already exists: hub.act_run.py extracts the orchestration contract, daemon delegates to run_act, tests/test_hub_act_run.py asserts import edges and RC semantics, and tests/support/act_fixtures.py consolidates shared fixtures—but test_act.py still has no import edge to act_run, so the direct daemon↔test_act hidden seam remains in coupling.md.
- Per repo precedent (tkt-0016), AC1 (explicit dependency) and AC2 (degree below coupling_min_degree 50%) are separable: a shared production module with import edges satisfies structural explicitness; clearing the coupling table row requires post-refactor divergent history (~9+ test_act-only commits after any co-touching refactor on live history, per degree formula round(100*shared/avg_revs)).
- Pytest fixture guidance supports consolidating act_repo/stub-agent setup into tests/support/ (or conftest) so daemon scheduling changes land in test_daemon.py and cmd_act behavior changes land in test_act.py, reducing future shared commits without conflating test ownership.
- Change-coupling literature warns that tangled or oversized commits can inflate co-change signals; fixture and refactor work should avoid single commits touching daemon.py, test_act.py, and test_daemon.py together.

## Recommendation

Treat hub.act_run as the named explicit contract (already extracted): daemon imports it for orchestration, and add a minimal test_act.py import of act_run RC constants or a shared contract helper so the dependency graph shows test_act→act_run←daemon rather than an orphan pair. Keep cmd_act integration in test_daemon.py and cmd_act unit coverage in test_act.py, with shared fixtures in tests/support/act_fixtures.py. AC2 closes only after enough solo-side commits accumulate and a rescan removes the pair from coupling.md—do not expect the hidden-seam banner to clear at merge time.

## Risks

- A co-touching refactor commit (daemon.py + test_act.py) temporarily worsens coupling math until sufficient solo-side commits accumulate.
- Wiring test_act→hub.act_run inverts the production hub→radar direction unless act_run stays a thin adapter; over-extraction blurs hub vs radar.act boundaries.
- AC1 via test_hub_act_run.py alone may not satisfy ticket wording that names the daemon↔test_act pair specifically—reviewer may require test_act.py to import the shared module.
- Clearing coupling.md depends on git history, not import edges alone; act_run.py-only or fixture-only commits do not reduce the daemon↔test_act pair degree.
- Consolidating fixtures in the same PR as act_run extraction can produce a large co-touch commit unless changes are split across follow-up commits.

## Evidence

- [[url-www-ime-usp-br-gerosa-papers-changecoupling-pdf\|https://www.ime.usp.br/~gerosa/papers/changecoupling.pdf]]
- [[url-docs-pytest-org-en-stable-reference-fixtures-html\|Fixtures reference¶]]
- research run: [[2026-06-10-hidden-seam-repo-scan-hub-daemon-py-test]]
