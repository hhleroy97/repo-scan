---
type: "analysis"
problem: "Split repo_scan/tickets.py (654 lines). `repo_scan/tickets.py` is 654 lines — past the 600-line critical threshold where files become hard to navigate and review. Acceptance criteria: No resulting file above 300 lines; All tests still pass. Research current best practices and draft a spec for this work."
confidence: "high"
sources: ["url-refactoring-com-catalog-movefunction-html", "url-realpython-com-python-all-attribute"]
generated_at: "2026-06-10 18:51 UTC"
---

# Analysis — Split repo_scan/tickets.py (654 lines). `repo_scan/tickets.py` is 654 lines — past the 600-line critical threshold where files become hard to navigate and review. Acceptance criteria: No resulting file above 300 lines; All tests still pass. Research current best practices and draft a spec for this work.
_Generated 2026-06-10 18:51 UTC — confidence: high_

## Findings

- repo_scan/tickets.py (~749 lines) decomposes cleanly along behavior ownership (Fowler Move Function): parse/card derivation (~175 lines), scan proposal + evidence (~150 lines), file workflow mutations (~130 lines), generation/auto-close/fingerprint (~85 lines), board (~20 lines), and CLI (~75 lines)—each slice stays under the 300-line cap.
- Fifteen-plus call sites across tests, hub, radar, scanner, and cli import `from repo_scan.tickets import …`; converting the module to a `tickets/` package with a thin `__init__.py` and explicit `__all__` re-exports preserves the public API without touching consumers (Real Python / PEP 8 guidance).
- Tests monkeypatch `repo_scan.tickets.record_merge_verification` and `repo_scan.tickets.now_date`; the facade must re-export patched symbols at the package root so existing test hooks keep working.
- `record_merge_verification` already lazy-imports `scanner` and `trends` to break cycles; it should live in an isolated submodule (e.g. `merge.py`) with lazy imports retained—`scanner.py` already imports `generate_tickets` from tickets at import time.
- `propose_from_scan` is the largest single function (~100 lines) and depends only on `cfg` plus normalized scan signal dicts—ideal boundary for a `propose.py` module separate from parse I/O and workflow.
- Prior in-repo precedent (tkt-0025 ui split) validates the pattern: semantic package, delete the monolith, facade-reexport, line-cap enforcement test alongside existing `test_tickets.py` / `test_tickets_workflow.py` suites.

## Recommendation

Convert `repo_scan/tickets.py` into `repo_scan/tickets/` with modules `constants`, `parse`, `evidence`, `propose`, `io`, `workflow`, `generation`, `merge`, `board`, and `cli`, moving functions to the module that owns their data (parse+card together, propose+evidence adjacent to scan signals, workflow mutations together). Add `__init__.py` that re-exports every currently imported public symbol via `__all__`, delete the old file, and add a parametrized line-count test (≤300 per file) plus full pytest run to satisfy acceptance criteria.

## Risks

- Circular import regressions if `merge.py` or `generation.py` promote lazy `scanner`/`trends` imports to module level.
- Incomplete `__all__` or missing facade re-exports breaking hub/radar imports or monkeypatch paths in `test_phase2_freshness.py` and `test_scanner_snapshots.py`.
- Cross-module import tangles (e.g. `workflow` ↔ `io` ↔ `board`) if write paths are split without keeping shared helpers (`tickets_dir`, `criteria_ready`) in a single low-level module.
- Refactor reduces line count but not cyclomatic complexity—hotspot rank may persist until `propose_from_scan` is further decomposed in a follow-up.

## Evidence

- [[url-refactoring-com-catalog-movefunction-html\|Move Function]]
- [[url-realpython-com-python-all-attribute\|Python's __all__: Packages, Modules, and Wildcard Imports – Real Python]]
- research run: [[2026-06-10-split-repo-scan-tickets-py-654-lines-rep]]
