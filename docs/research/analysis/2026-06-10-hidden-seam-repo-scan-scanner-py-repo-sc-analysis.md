---
type: "analysis"
problem: "Hidden seam: repo_scan/scanner.py <-> repo_scan/writers.py (67% coupled). `repo_scan/scanner.py` and `repo_scan/writers.py` changed together in 5 commits (67% degree) but share no import edge — an implicit contract the dependency graph can't see. Acceptance criteria: Make the dependency explicit (shared module or import); Coupling degree drops below threshold in coupling.md. Research current best practices and draft a spec for this work."
confidence: "medium"
sources: ["arxiv-2510.03050"]
generated_at: "2026-06-10 07:53 UTC"
---

# Analysis — Hidden seam: repo_scan/scanner.py <-> repo_scan/writers.py (67% coupled). `repo_scan/scanner.py` and `repo_scan/writers.py` changed together in 5 commits (67% degree) but share no import edge — an implicit contract the dependency graph can't see. Acceptance criteria: Make the dependency explicit (shared module or import); Coupling degree drops below threshold in coupling.md. Research current best practices and draft a spec for this work.
_Generated 2026-06-10 07:53 UTC — confidence: medium_

## Findings

- scanner.py already imports writers.py (`from .writers import write_*`), but `get_python_dep_edges` strips leading dots from relative imports (`writers` vs `repo_scan.writers`), so `hidden_seams` reports a false-negative seam—the dependency exists in code but not in the dep graph.
- Beyond the graph bug, a real implicit contract remains: `_write_reports` sequences seven `write_*` calls with ad-hoc argument tuples (line_counts, behavior, edges, delta, seams) that co-evolve whenever report shape changes, explaining 56–67% historical change coupling despite a one-way import.
- The arXiv microservices-preparation catalogue argues decomposition must start with code-level dependency refactorings—explicit boundaries, transfer objects, and narrow APIs—not architecture-only moves; that maps directly to extracting a facade module between orchestration and markdown writers.
- tkt-0007 precedent (delete redundant file) does not apply here; the analogue is introduce an explicit shared module (`report_pipeline` or similar) that owns the write sequence and a typed payload derived from `ScanContext`, shrinking coordinated edits to one hub.
- Acceptance criteria require two distinct outcomes: (1) visible dependency edge in the graph, and (2) coupling degree below the ≥50% threshold in coupling.md (currently 5 shared commits, 56%); fixing the graph alone satisfies AC1 but likely leaves AC2 unmet until structural decoupling lets the pair diverge in git history.
- Existing characterization infrastructure (`test_scanner_snapshots`, `test_writers_snapshots`, `test_behavior::test_hidden_seams_excludes_imported_pairs`) can gate the refactor; a planned `graphs.py` ast-based import walker (tkt-0003) would permanently fix relative-import resolution but should be coordinated or partially landed first.

## Recommendation

Extract `repo_scan/report_pipeline.py` with a typed `ReportPayload` (or reuse `ScanContext` read-only view) and a single `write_scan_reports(...)` entry point that owns call order and signatures, then thin `_write_reports` to delegate through it so the scanner→writers contract is explicit and localized. In parallel, fix relative-import resolution in `get_python_dep_edges` (minimal dot-aware patch or ast walker) so the import edge appears in `docs/reports/coupling.md`, and gate both changes with existing scanner/writers snapshot tests before rescanning to confirm the seam clears and degree drops below 50%.

## Risks

- Import-edge fix may close AC1 while historical coupling degree stays ≥50% until enough post-refactor commits accumulate without paired changes.
- A poorly scoped `report_pipeline` module could become a second god-object absorbing orchestration, writers, and trends logic.
- Snapshot and golden-file drift across seven report writers during extraction if payload typing is incomplete.
- Overlap with the separate `graphs.py` ast refactor (tkt-0003) risks duplicate work or conflicting import-resolution semantics.
- Writers' public `write_*` signatures are depended on by direct unit/snapshot tests; changing them breaks the established writers-refactor contract.

## Evidence

- [[arxiv-2510.03050\|Refactoring Towards Microservices: Preparing the Ground for Service Extraction]]
- research run: [[2026-06-10-hidden-seam-repo-scan-scanner-py-repo-sc]]
