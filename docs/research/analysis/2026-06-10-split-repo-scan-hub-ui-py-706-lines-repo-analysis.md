---
type: "analysis"
problem: "Split repo_scan/hub/ui.py (706 lines). `repo_scan/hub/ui.py` is 706 lines — past the 600-line critical threshold where files become hard to navigate and review. Acceptance criteria: No resulting file above 300 lines; All tests still pass. Research current best practices and draft a spec for this work."
confidence: "high"
sources: ["arxiv-2605.02741", "url-refactoring-com-catalog-extractclass-html", "url-docs-python-org-3-tutorial-modules-html-packages"]
generated_at: "2026-06-10 18:28 UTC"
linked_files: ["tests/test_hub_ui.py"]
---

# Analysis — Split repo_scan/hub/ui.py (706 lines). `repo_scan/hub/ui.py` is 706 lines — past the 600-line critical threshold where files become hard to navigate and review. Acceptance criteria: No resulting file above 300 lines; All tests still pass. Research current best practices and draft a spec for this work.
_Generated 2026-06-10 18:28 UTC — confidence: high_

## Findings

- ui.py is a single assembly module: one raw HTML template (~718 lines inside `_DASHBOARD_TEMPLATE`) plus `DASHBOARD_HTML = template.replace('/* __HUB_CONTRACT__ */', js_contract_block())`. The public API is only `DASHBOARD_HTML`; consumers are `server.py` and `tests/test_hub_ui.py`, so a package refactor can keep `from repo_scan.hub.ui import DASHBOARD_HTML` stable via `ui/__init__.py`.
- Natural cohesion seams are semantic, not arbitrary line chunks: (~105 lines) embedded CSS; (~15 lines) HTML chrome (header, nav, viewer, toast); (~150 lines) shared runtime JS (api, pending/busy chrome, SSE/poll, `render`/`setTab`/`formBusy`); (~65 lines) ticket contract helpers (`filterOpenTickets`, `sortTickets`, `rOpenTickets`); (~175 lines) Now tab (stats grid, live runs, feed, usage, `rNowPRsAndGates` orchestration); (~115 lines) PR diagnosis/merge/fix actions; (~70 lines) Gates tab; (~95 lines) Tickets tab; (~45 lines) Activity/telemetry plus doc viewer and boot (`openDoc`, `refresh`, `connectSSE`).
- Martin Fowler Extract Class maps cleanly: each tab renderer (`rNow`, `rGates`, `rTickets`, `rActivity`) plus its action handlers (`prAct`, `gateDecide`, `ticketAct`, etc.) form a cohesive unit; shared cross-tab utilities (esc, toast, pending, `render` dispatcher) belong in a separate runtime fragment, not duplicated per tab.
- Python's package pattern supports converting `ui.py` → `ui/` subpackage where fragment modules export string constants and `__init__.py` concatenates them in strict order, preserving the no-build-step, all-inline constraint documented in the module docstring.
- The arXiv 'Modular Mirage' / Volume-Quality inverse law warns against cosmetic splits (e.g., splitting the raw string every 250 lines): boundaries must follow tab/renderer responsibility or coupling and review burden shift without improving navigability.
- Existing tests in `test_hub_ui.py` assert presence and ordering of symbols in the assembled `DASHBOARD_HTML` (e.g., `rNow` layout order, `rOpenTickets` early return, contract block injection). Parity of the final concatenated string is the primary regression guard—no browser tests exist.
- The `/* __HUB_CONTRACT__ */` marker must remain at a fixed position in the `<script>` block (after core runtime, before ticket-specific helpers) so `js_contract_block()` injects `OPEN_TICKET_STATUSES`, `TICKET_STATUS_ORDER`, and `TICKET_BADGE_CLS` correctly.
- Meeting the ≤300-line cap requires at least three modules and realistically six to seven: CSS (~110), shell (~40), runtime (~170), now (~120), prs+gates (~185), tickets (~100), activity+viewer+boot (~55), plus `__init__.py` (~25)—all comfortably under 300 individually.
- Open ticket tkt-0023 (52% hidden seam ui.py ↔ test_hub.py) will improve once tests continue importing only `DASHBOARD_HTML` from the package root while implementation fragments live in sibling modules tests need not import.

## Recommendation

Convert `repo_scan/hub/ui.py` into a `repo_scan/hub/ui/` subpackage that exports the same `DASHBOARD_HTML` from `__init__.py`. Split the template into cohesive string fragments (`_css`, `_shell`, `_runtime`, `_now`, `_prs_gates`, `_tickets`, `_activity`) aligned with tab/renderer responsibilities per Extract Class, concatenate in document order, and keep contract injection unchanged. Verify with existing `test_hub_ui.py` (and full test suite); optionally add one assembly test asserting fragment join order and contract-marker placement.

## Risks

- Wrong fragment concatenation order silently breaks JS (e.g., `render` dispatch referencing `rGates` before it is defined, or contract constants used before injection).
- Placing the `/* __HUB_CONTRACT__ */` marker incorrectly breaks ticket filtering/sorting/badge styling without failing most tests.
- Splitting PR logic away from `rNowPRsAndGates` without keeping shared helpers (`rPRCard`, `rGateCard`) co-located could recreate tight cross-fragment coupling.
- Pursuing the 300-line cap via arbitrary sub-splits of the largest Now/PR block would reproduce Modular Mirage—worse cohesion for marginal line-count gain.
- Substring-based tests may pass even if whitespace or minor markup drifts; consider a golden-length or checksum assertion on `DASHBOARD_HTML` if byte-parity is required.
- Git history blame on `ui.py` fragments across new files—acceptable trade-off but reviewers lose single-file archaeology.

## Evidence

- [[arxiv-2605.02741\|AI-Generated Smells: An Analysis of Code and Architecture in LLM and Agent-Driven Development]]
- [[url-refactoring-com-catalog-extractclass-html\|Extract Class]]
- [[url-docs-python-org-3-tutorial-modules-html-packages\|6. Modules]]
- research run: [[2026-06-10-split-repo-scan-hub-ui-py-706-lines-repo]]
