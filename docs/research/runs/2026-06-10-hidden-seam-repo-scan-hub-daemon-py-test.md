---
type: "research-run"
question: "Hidden seam: repo_scan/hub/daemon.py <-> tests/test_act.py (70% coupled). `repo_scan/hub/daemon.py` and `tests/test_act.py` changed together in 7 commits (70% degree) but share no import edge — an implicit contract the dependency graph can't see. Acceptance criteria: Make the dependency explicit (shared module or import); Coupling degree drops below threshold in coupling.md. Research current best practices and draft a spec for this work."
sources: ["arxiv-2411.19099", "gh-zyskarch-pytestarch", "url-deviq-com-principles-explicit-dependencies-principle"]
run_at: "2026-06-10 18:50 UTC"
---

# Research run — Hidden seam: repo_scan/hub/daemon.py <-> tests/test_act.py (70% coupled). `repo_scan/hub/daemon.py` and `tests/test_act.py` changed together in 7 commits (70% degree) but share no import edge — an implicit contract the dependency graph can't see. Acceptance criteria: Make the dependency explicit (shared module or import); Coupling degree drops below threshold in coupling.md. Research current best practices and draft a spec for this work.
_Run 2026-06-10 18:50 UTC_

**Strategy:** Treat the 70% co-change as evidence of a missing published contract at the daemon→act orchestration boundary; the spec should separate concerns (daemon tests import daemon, act tests stay on act), optionally extract a shared integration module, and add an architecture test that pins the import edge so coupling.md and the dependency graph agree.

## Ingested

- [[sources/arxiv-2411.19099\|Enhancing Software Maintenance: A Learning to Rank Approach for Co-changed Method Identification]] — Frames co-changing artifacts without structural import edges as implicit evolutionary coupling and argues they should be surfaced and reduced for maintainability—the exact failure mode repo-scan flags as a hidden seam.
- [[sources/gh-zyskarch-pytestarch\|zyskarch/pytestarch — Test framework for software architecture based on imports between modules.]] — Provides a pytest-native pattern for encoding required import relationships as architecture rules, turning an invisible temporal contract into an explicit, CI-enforced dependency edge.
- [[sources/url-deviq-com-principles-explicit-dependencies-principle\|Explicit Dependencies Principle]] — States that collaborators hidden inside implementation are harder to test and analyze than dependencies declared in public interfaces—direct guidance for choosing a shared module or direct import over co-change-only coupling.
