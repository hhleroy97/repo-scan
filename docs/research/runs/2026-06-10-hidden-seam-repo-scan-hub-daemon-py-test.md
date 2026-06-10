---
type: "research-run"
question: "Hidden seam: repo_scan/hub/daemon.py <-> tests/test_act.py (70% coupled). `repo_scan/hub/daemon.py` and `tests/test_act.py` changed together in 7 commits (70% degree) but share no import edge — an implicit contract the dependency graph can't see. Acceptance criteria: Make the dependency explicit (shared module or import); Coupling degree drops below threshold in coupling.md. Research current best practices and draft a spec for this work."
sources: ["url-www-ime-usp-br-gerosa-papers-changecoupling-pdf", "url-docs-pytest-org-en-stable-reference-fixtures-html"]
run_at: "2026-06-10 21:11 UTC"
---

# Research run — Hidden seam: repo_scan/hub/daemon.py <-> tests/test_act.py (70% coupled). `repo_scan/hub/daemon.py` and `tests/test_act.py` changed together in 7 commits (70% degree) but share no import edge — an implicit contract the dependency graph can't see. Acceptance criteria: Make the dependency explicit (shared module or import); Coupling degree drops below threshold in coupling.md. Research current best practices and draft a spec for this work.
_Run 2026-06-10 21:11 UTC_

**Strategy:** Pair foundational change-coupling measurement (why the seam alerts) with two explicit-boundary tactics: a production ACL adapter for orchestration semantics and a pytest fixture-support module for test-side decoupling—matching the spec’s dual AC1 (import graph) and AC2 (historical degree) requirements.

## Ingested

- [[sources/url-www-ime-usp-br-gerosa-papers-changecoupling-pdf\|https://www.ime.usp.br/~gerosa/papers/changecoupling.pdf]] — Foundational change-coupling reference that defines implicit evolutionary dependencies invisible to static analysis and quantifies them with support/confidence—the same metrics repo-scan uses for coupling.md degree thresholds and hidden-seam detection.
- [[sources/url-docs-pytest-org-en-stable-reference-fixtures-html\|Fixtures reference¶]] — Official pytest guidance on `conftest.py`, `pytest_plugins`, and fixture decomposition supports consolidating duplicated `act_repo`/stub-agent helpers into `tests/support/act_fixtures.py` so `test_act.py` and `test_daemon.py` stop co-changing without a shared import edge.

## Failed

- `url:https://martinfowler.com/eaaCatalog/antiCorruptionLayer.html` — fetch failed for https://martinfowler.com/eaaCatalog/antiCorruptionLayer.html: HTTP Error 404: Not Found
