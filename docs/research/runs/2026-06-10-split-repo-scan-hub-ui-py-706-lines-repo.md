---
type: "research-run"
question: "Split repo_scan/hub/ui.py (706 lines). `repo_scan/hub/ui.py` is 706 lines — past the 600-line critical threshold where files become hard to navigate and review. Acceptance criteria: No resulting file above 300 lines; All tests still pass. Research current best practices and draft a spec for this work."
sources: ["arxiv-2605.02741", "url-refactoring-com-catalog-extractclass-html", "url-docs-python-org-3-tutorial-modules-html-packages"]
run_at: "2026-06-10 18:28 UTC"
---

# Research run — Split repo_scan/hub/ui.py (706 lines). `repo_scan/hub/ui.py` is 706 lines — past the 600-line critical threshold where files become hard to navigate and review. Acceptance criteria: No resulting file above 300 lines; All tests still pass. Research current best practices and draft a spec for this work.
_Run 2026-06-10 18:28 UTC_

**Strategy:** Treat ui.py as a published-interface assembly problem: decompose the raw template along CSS / HTML shell / per-tab JS renderer seams, then stitch fragments in ui/__init__.py with contract.js_contract_block() unchanged. Prioritize semantic cohesion over hitting the 300-line cap, and verify parity via existing test_hub_ui.py substring assertions on the assembled DASHBOARD_HTML.

## Ingested

- [[sources/arxiv-2605.02741\|AI-Generated Smells: An Analysis of Code and Architecture in LLM and Agent-Driven Development]] — Introduces the 'Modular Mirage' anti-pattern—files split without semantic cohesion—so split boundaries for ui.py should follow tab/renderer responsibilities (Now, Gates, Tickets, Activity) rather than arbitrary line chunks.
- [[sources/url-refactoring-com-catalog-extractclass-html\|Extract Class]] — Extract Class guidance on grouping related fields and methods by client/responsibility maps directly to clustering the inline JS renderers (rNow*, rGates, rTickets, rActivity) and shared chrome utilities into cohesive fragments.
- [[sources/url-docs-python-org-3-tutorial-modules-html-packages\|6. Modules]] — Official Python package pattern for converting a monolithic ui.py module into a ui/ subpackage whose __init__.py assembles and re-exports DASHBOARD_HTML, keeping server.py and test imports stable.
