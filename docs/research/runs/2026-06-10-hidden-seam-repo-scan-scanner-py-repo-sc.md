---
type: "research-run"
question: "Hidden seam: repo_scan/scanner.py <-> repo_scan/writers.py (67% coupled). `repo_scan/scanner.py` and `repo_scan/writers.py` changed together in 5 commits (67% degree) but share no import edge — an implicit contract the dependency graph can't see. Acceptance criteria: Make the dependency explicit (shared module or import); Coupling degree drops below threshold in coupling.md. Research current best practices and draft a spec for this work."
sources: ["arxiv-2510.03050"]
run_at: "2026-06-10 07:51 UTC"
---

# Research run — Hidden seam: repo_scan/scanner.py <-> repo_scan/writers.py (67% coupled). `repo_scan/scanner.py` and `repo_scan/writers.py` changed together in 5 commits (67% degree) but share no import edge — an implicit contract the dependency graph can't see. Acceptance criteria: Make the dependency explicit (shared module or import); Coupling degree drops below threshold in coupling.md. Research current best practices and draft a spec for this work.
_Run 2026-06-10 07:51 UTC_

**Strategy:** Strategy: pair change-coupling theory with seam formalization, then follow the repo's tkt-0007 precedent—extract a single facade module that owns the write sequence and data contract, fix `get_python_dep_edges` relative-import resolution so the scanner→writers edge is visible, and gate the move with existing scanner/writers snapshot tests so coupling degree can fall without artifact drift.

## Ingested

- [[sources/arxiv-2510.03050\|Refactoring Towards Microservices: Preparing the Ground for Service Extraction]] — This refactoring-toward-extraction paper prescribes breaking tight local dependencies by introducing explicit transfer objects and narrow APIs—directly analogous to extracting a `report_pipeline` module with a typed payload between scan orchestration and markdown writers.

## Failed

- `url:https://martinfowler.com/bliki/ChangeCoupling.html` — fetch failed for https://martinfowler.com/bliki/ChangeCoupling.html: HTTP Error 404: Not Found
- `url:https://martinfowler.com/bliki/SoftwareSeam.html` — fetch failed for https://martinfowler.com/bliki/SoftwareSeam.html: HTTP Error 404: Not Found
