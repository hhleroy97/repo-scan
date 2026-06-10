---
type: "research-run"
question: "Hidden seam: repo_scan/hub/server.py <-> repo_scan/hub/ui.py (88% coupled). `repo_scan/hub/server.py` and `repo_scan/hub/ui.py` changed together in 7 commits (88% degree) but share no import edge — an implicit contract the dependency graph can't see. Acceptance criteria: Make the dependency explicit (shared module or import); Coupling degree drops below threshold in coupling.md. Research current best practices and draft a spec for this work."
sources: ["url-thoughtbot-com-blog-connascence-as-a-vocabulary-to-discuss-c", "url-peps-python-org-pep-0589", "gh-seddonym-import-linter"]
run_at: "2026-06-10 17:16 UTC"
---

# Research run — Hidden seam: repo_scan/hub/server.py <-> repo_scan/hub/ui.py (88% coupled). `repo_scan/hub/server.py` and `repo_scan/hub/ui.py` changed together in 7 commits (88% degree) but share no import edge — an implicit contract the dependency graph can't see. Acceptance criteria: Make the dependency explicit (shared module or import); Coupling degree drops below threshold in coupling.md. Research current best practices and draft a spec for this work.
_Run 2026-06-10 17:16 UTC_

**Strategy:** Coupling.md already shows a `server→ui` import for `DASHBOARD_HTML`, but 88% co-change persists because the JSON API schema and status constants are still implicit; the spec should extract a shared contract module (TypedDict + route/field constants) and add parity tests, mirroring the pyproject-only hidden-seam playbook while using connascence language to justify what moves.

## Ingested

- [[sources/url-thoughtbot-com-blog-connascence-as-a-vocabulary-to-discuss-c\|Connascence as a vocabulary to discuss Coupling]] — Names the real server↔ui seam—connascence of name/meaning on `/api/state` field names and duplicated ticket-status constants—and gives a vocabulary for moving that contract into a shared, local module.
- [[sources/url-peps-python-org-pep-0589\|PEP 589 – TypedDict: Type Hints for Dictionaries with a Fixed Set of Keys | peps.python.org]] — TypedDict is the stdlib-native way to make the `build_state()` payload an explicit, importable contract both `server.py` and tests can share without adding dependencies.
- [[sources/gh-seddonym-import-linter\|seddonym/import-linter — Lint your Python architecture.]] — Provides declarative layer/independence contracts to codify the intended hub boundary (e.g. `ui` must not import `server`) and lock in the explicit dependency graph after extraction.
