---
type: "spec"
problem: "Hidden seam: repo_scan/scanner.py <-> repo_scan/writers.py (67% coupled). `repo_scan/scanner.py` and `repo_scan/writers.py` changed together in 5 commits (67% degree) but share no import edge — an implicit contract the dependency graph can't see. Acceptance criteria: Make the dependency explicit (shared module or import); Coupling degree drops below threshold in coupling.md. Research current best practices and draft a spec for this work."
status: "approved"
audit_verdict: "revise"
analysis: "[[2026-06-10-hidden-seam-repo-scan-scanner-py-repo-sc-analysis]]"
drafted_at: "2026-06-10 13:31 UTC"
linked_files: ["repo_scan/graphs.py", "repo_scan/report_pipeline.py", "repo_scan/scanner.py", "repo_scan/writers.py", "tests/test_behavior.py"]
---

# Spec — Hidden seam: repo_scan/scanner.py <-> repo_scan/writers.py (67% coupled). `repo_scan/scanner.py` and `repo_scan/writers.py` changed together in 5 commits (67% degree) but share no import edge — an implicit contract the dependency graph can't see. Acceptance criteria: Make the dependency explicit (shared module or import); Coupling degree drops below threshold in coupling.md. Research current best practices and draft a spec for this work.
_Drafted 2026-06-10 13:31 UTC by radar — **status: approved**_

I'll verify the codebase against the audit findings so the revised spec matches reality.
## Goal

Close tkt-0008: make the orchestration→writers contract explicit via a shared `report_pipeline` module, fix `get_python_dep_edges` relative-import resolution (today `from .writers` is stripped to `writers` and never matches `repo_scan.writers`), and rescan so `docs/reports/coupling.md` no longer lists `scanner.py`↔`writers.py` as a hidden seam. **Baseline (live scan):** 5 shared commits, 53% degree, 11 scanner revs / 8 writers revs — reconcile ticket prose citing 56%/67%. Ticket AC1 wording (“shared module or import”) is satisfied by `scanner` + `report_pipeline` sharing a write contract, **not** by restoring a direct `scanner → writers` import after decoupling.

## Approach

Two coordinated tracks, characterization-first (writers/scanner snapshot precedent):

1. **Graph fix** — Dot-aware relative-import resolver in `get_python_dep_edges` (resolve `from .writers` / `from ..pkg` against source package + `repo_modules`; **no** tkt-0003 ast-walker slice). Makes the existing `scanner.py` import visible in dep edges and `hidden_seams` **pre-refactor**; post-refactor, `hidden_seams` does not follow `scanner → report_pipeline → writers`, so AC1 closure is the explicit pipeline contract, not a transitive import edge.

2. **Structural decoupling** — Extract `repo_scan/report_pipeline.py`. Build a narrow `ReportPayload` **from** `ScanContext` fields already computed before write (summaries, delta, seams, mermaid strings, behavior, ranking inputs) — do not duplicate evolving scan state. Single `write_scan_reports(root, cfg, payload)` owns six `write_*` calls plus `append_trend_log` (stays in the write hub per scanner CC spec). Thin `scanner._write_reports` to assemble payload and delegate; remove `from .writers import ...` from `scanner.py`. Keep `writers.py` formatters unchanged in the extraction commit so git co-change history can diverge immediately.

Land graph fix first (or same PR, tests before refactor). **AC2 requires degree strictly below 50%** (`coupling_min_degree: 50`); one divergent commit on scanner-only math yields `round(500/10)=50%` — still listed. Plan **≥2** post-decoupling commits touching `scanner`/`report_pipeline` without `writers`, or equivalent fixture history.

## Changes

- **`repo_scan/report_pipeline.py`** (new) — `ReportPayload` dataclass; `write_scan_reports(...)` sequencing `write_health_report`, `write_coupling_report`, `write_dep_report`, `write_call_report`, `write_index`, `write_scan_json`, then `append_trend_log`.
- **`repo_scan/scanner.py`** — Replace six ad-hoc `write_*` calls with `write_scan_reports`; drop `writers` import; keep delta/seam computation in scanner, payload assembly adjacent to `_write_reports`.
- **`repo_scan/graphs.py`** — Resolve relative imports to dotted `repo_scan.*` targets; document in `get_python_dep_edges` docstring.
- **`tests/test_graphs.py`** (new) — Fixture with `from .writers import ...`; assert `(repo_scan.scanner, repo_scan.writers)` edge.
- **`tests/test_report_pipeline.py`** (new) — Payload builder + `write_scan_reports` contract (monkeypatch writers, assert call order/args); import-boundary and degree fixtures (below).
- **Regenerated scan docs** — After merge **and** sufficient divergent history, run `repo-scan`; commit `docs/reports/coupling.md`, `docs/scan.json`, `docs/index.md`, `docs/digest.md`, `docs/reports/health.md`, `docs/architecture/dependency-graph.md`, `docs/reports/dependencies.md`.
- **`docs/tickets/tkt-0008.md`** — AC notes: reinterpret AC1; record baseline 53%/5 shared.

Do **not** change coupling thresholds, `hidden_seams` semantics, or unrelated seams.

## Tests

| Acceptance criterion | Automated test |
|---|---|
| Explicit orchestration→writers contract (shared module) | `tests/test_graphs.py::test_relative_import_resolves_intra_package_edge` — pre-refactor fixture; edge `repo_scan.scanner` → `repo_scan.writers`. |
| Explicit contract via `report_pipeline` | `tests/test_report_pipeline.py::test_scanner_imports_report_pipeline_not_writers` — no `repo_scan.writers` in `scanner` bindings; write path reaches `report_pipeline`. |
| Graph regression | `tests/test_behavior.py::test_hidden_seams_excludes_imported_pairs` — direct-edge exclusion only; **not** post-refactor `scanner/writers` gate. |
| Coupling degree below threshold | `tests/test_report_pipeline.py::test_scanner_writers_degree_below_threshold` — temp git fixture: 5 shared commits at 53%, then **≥2** commits touching only `scanner.py` + `report_pipeline.py`; `analyze_history` → pair absent or `degree < 50`. No live-repo root in pytest. |
| Coupling degree below threshold | Post-rescan: `scanner.py`↔`writers.py` **absent** from coupling table and hidden-seam warning; if still listed, degree **< 50%** (not required to show import **yes** — no direct import post-refactor). |
| No artifact regression | `tests/test_writers_snapshots.py` — byte-identical writer outputs. |
| No artifact regression | `tests/test_scanner_snapshots.py` — E2E `scan()` artifacts unchanged. |

## Documentation

- **`repo_scan/report_pipeline.py`** — Owns scan→docs write sequence, `ReportPayload`, and sole orchestration-layer `writers.write_*` consumption.
- **`repo_scan/scanner.py`** — `_write_reports` delegates to `report_pipeline`.
- **`repo_scan/graphs.py`** — Relative-import resolution documented.
- **`docs/tickets/tkt-0008.md`** — Remediation summary, AC1 reinterpretation, baseline metrics.
- Regenerated coupling and dependency-graph artifacts after rescan.

## Risks

- Graph fix alone clears hidden-seam warning only while direct import exists; decoupling without enough divergent history leaves pair at **exactly 50%** (boundary) — still reported and still a hidden seam.
- `report_pipeline` may become a new git co-change hub with both `scanner` and `writers` until write logic stabilizes.
- tkt-0003 ast refactor may overlap `graphs.py`; keep this ticket to minimal relative-import fix.
- Snapshot refresh if payload ordering shifts; run writers snapshots before scanner E2E.

## Out of scope

Other hidden seams (`hub/server`↔`ui`, `radar/*`, etc.), `write_candidates` / radar path, `graphs.py` full CC refactor, changing `coupling_min_degree` / `coupling_min_shared`, renaming `writers.py` functions.

## Audit

> [!warning] Audit verdict: revise
> The dual-track approach matches the codebase (live 53%/5 shared, relative-import bug, existing snapshot harness), but the spec must separate transient graph-fix effects from durable AC1/AC2 closure and fix contradictory success criteria before human review.
> - Goal conflates clearing the hidden-seam warning with AC2: after decoupling removes `scanner → writers`, the pair can reappear as a hidden seam at 53% until degree drops below 50%—`report_pipeline` is not transitive for `hidden_seams`.
> - Post-rescan AC2 row is logically impossible: `analyze_history` only emits pairs with `degree >= coupling_min_degree` (50), so a listed pair cannot also have degree < 50%.
> - Tests table row 1 labels AC1 'shared module' but maps to `test_relative_import_resolves_intra_package_edge`, which only exercises the graph resolver—not the `report_pipeline` contract.
> - AC1 reinterpretation ('shared module via `report_pipeline`, not direct import') conflicts with unchanged `tkt-0008.md` wording ('shared module or import') and is not flagged for explicit human reviewer approval, unlike the tkt-0007 audit recommendation.
> - Ticket/research premise 'share no import edge' is false in source: `scanner.py` already imports `writers`; only `get_python_dep_edges` misses `from .writers` (confirmed at `graphs.py` L119). Spec should correct provenance, not only reconcile 53%/67% degree.
> - Graph-fix benefit is transient: landing it pre-refactor clears the seam via a visible import edge, but post-refactor removes that edge again unless AC2 is met—spec does not state this regression explicitly.
> - AC2 closure is not merge-gated: fixture test covers synthetic history, but committed `docs/reports/coupling.md` compliance depends on manual regen after ≥2 future divergent commits—ticket may remain open at merge.
> - Boundary math typo: 'round(500/10)=50%' should be `round(100*5/10)`; the ≥2-commit plan is otherwise sound (11/8 revs → 53% baseline verified in `docs/scan.json`).
> - Missing risk: `get_python_dep_edges` is also used by `collect_digest_inputs()`—relative-import fix may change digest/dependency artifacts beyond coupling seams (tkt-0003 overlap).
> - Scope overlap: both this spec and approved `2026-06-10-refactor-repo-scan-graphs-py-cc-56-3-com-spec.md` plan new `tests/test_graphs.py`; coordinate to avoid duplicate/conflicting fixtures.

## Provenance

- analysis: [[2026-06-10-hidden-seam-repo-scan-scanner-py-repo-sc-analysis]]
