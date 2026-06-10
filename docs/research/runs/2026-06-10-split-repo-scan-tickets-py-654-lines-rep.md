---
type: "research-run"
question: "Split repo_scan/tickets.py (654 lines). `repo_scan/tickets.py` is 654 lines — past the 600-line critical threshold where files become hard to navigate and review. Acceptance criteria: No resulting file above 300 lines; All tests still pass. Research current best practices and draft a spec for this work."
sources: ["url-refactoring-com-catalog-movefunction-html", "url-realpython-com-python-all-attribute"]
run_at: "2026-06-10 18:50 UTC"
---

# Research run — Split repo_scan/tickets.py (654 lines). `repo_scan/tickets.py` is 654 lines — past the 600-line critical threshold where files become hard to navigate and review. Acceptance criteria: No resulting file above 300 lines; All tests still pass. Research current best practices and draft a spec for this work.
_Run 2026-06-10 18:50 UTC_

**Strategy:** Mirror the approved tkt-0025 pattern: convert tickets.py into a tickets/ package along semantic seams (parse/card, propose/evidence, workflow/board, CLI), delete the stale module, and facade-reexport the published surface. Pair Move Function seam selection with thin __init__.py + __all__ so behavior stays identical and a line-cap test can enforce the ≤300-line acceptance criterion.

## Ingested

- [[sources/url-refactoring-com-catalog-movefunction-html\|Move Function]] — Fowler's Move Function is the canonical guide for relocating functions to the module where their data and callers live, which directly governs cohesion-based seam selection when splitting tickets.py.
- [[sources/url-realpython-com-python-all-attribute\|Python's __all__: Packages, Modules, and Wildcard Imports – Real Python]] — Documents how to define a stable public API via __all__ and re-exports in __init__.py, which is required to preserve the 15+ existing `from repo_scan.tickets import ...` call sites after converting the module to a package.

## Failed

- `url:https://hynek.me/articles/importhammer/` — fetch failed for https://hynek.me/articles/importhammer/: HTTP Error 404: Not Found
