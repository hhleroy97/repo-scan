---
type: "spec"
problem: "Split repo_scan/hub/ui.py (706 lines). `repo_scan/hub/ui.py` is 706 lines — past the 600-line critical threshold where files become hard to navigate and review. Acceptance criteria: No resulting file above 300 lines; All tests still pass. Research current best practices and draft a spec for this work."
status: "approved"
audit_verdict: "revise"
analysis: "[[2026-06-10-split-repo-scan-hub-ui-py-706-lines-repo-analysis]]"
drafted_at: "2026-06-10 18:35 UTC"
linked_files: ["repo_scan/hub/ui/__init__.py", "tests/test_hub.py", "tests/test_hub_contract.py", "tests/test_hub_ui.py"]
---

# Spec — Split repo_scan/hub/ui.py (706 lines). `repo_scan/hub/ui.py` is 706 lines — past the 600-line critical threshold where files become hard to navigate and review. Acceptance criteria: No resulting file above 300 lines; All tests still pass. Research current best practices and draft a spec for this work.
_Drafted 2026-06-10 18:35 UTC by radar — **status: approved**_

I'll check `ui.py` and the related tests so the revised spec matches the actual seams and audit findings.
## Goal

Split `repo_scan/hub/ui.py` (739 lines, past the 600-line review threshold) into a `repo_scan/hub/ui/` package whose modules stay at or below 300 lines each. Preserve the published surface: `from repo_scan.hub.ui import DASHBOARD_HTML` with **byte-identical** assembled HTML (contract injection unchanged). No build step, no framework, no external requests.

## Approach

Apply Martin Fowler’s Extract Class along semantic seams in `_DASHBOARD_TEMPLATE`, not arbitrary line chunks. Use a **regular package** (`ui/__init__.py`); each fragment exports one raw `_FRAGMENT` string; `__init__.py` concatenates in strict document order, then splices `contract.js_contract_block()` at `/* __HUB_CONTRACT__ */` (after shared runtime JS, before ticket helpers). **Remove `ui.py` before importing the package** so `import repo_scan.hub.ui` resolves the directory, not the stale module.

| Fragment | Responsibility |
|---|---|
| `_head` | `<!DOCTYPE html>` … `<title>`, through line before `<style>` |
| `_css` | `<style>…</style>` |
| `_shell` | `</head>`, `<body>` chrome (header, nav, viewer, toast), `<script>` open |
| `_runtime` | Shared JS through `render`/`setTab`/`formBusy`, **`schedulePoll`/`connectSSE`/`refresh`**, contract marker |
| `_now` | Post-marker ticket helpers, `rOpenTickets`, `rLiveRuns`, `rFeed`, `rUsage`, `stat`, `rNow` |
| `_prs_gates` | `const prLast`, PR merge/fix, `rNowPRsAndGates`, gate cards/`rGates`/`gateDecide` |
| `_tickets` | `ticketCard`, `rTickets`, ticket actions |
| `_activity` | `rTelemetry`, `rActivity`, `openDoc`/`closeDoc`, boot `refresh(); connectSSE();`, `</script></body></html>` |

**Cross-fragment JS:** `rNow` (in `_now`) calls `rNowPRsAndGates` (in `_prs_gates`) — intentional vs the research cohesion map; safe via function hoisting and because `const prLast` initializes before any `refresh()` runs. Delete `ui.py` after the package lands; `server.py` and tests keep the same import path.

## Changes

- **Delete `repo_scan/hub/ui.py`** — move template bytes only; no behavioral edits.
- **Add `repo_scan/hub/ui/__init__.py`** — join `[ _head, _css, _shell, _runtime, _now, _prs_gates, _tickets, _activity ]`; `DASHBOARD_HTML = _DASHBOARD_TEMPLATE.replace("/* __HUB_CONTRACT__ */", js_contract_block())`; re-export `DASHBOARD_HTML` only.
- **Add fragment modules** (`_head.py` … `_activity.py`) — each holds one `_FRAGMENT` per table above.
- **Update `tests/test_hub_contract.py`** — `test_ui_imports_contract_for_dashboard_html` AST-scans `repo_scan/hub/ui/__init__.py` (not `ui.py`); repoint `_UI` in the synthetic coupling-degree fixture to the package entry (`ui/__init__.py`).

## Tests

| Acceptance criterion | Automated test |
|---|---|
| No resulting file above 300 lines | **New** `tests/test_hub_ui.py::test_ui_package_modules_under_line_cap` |
| Byte-identical assembly | **New** `tests/test_hub_ui.py::test_dashboard_html_byte_parity` — golden `hashlib.sha256(DASHBOARD_HTML.encode()).hexdigest()` captured once at refactor time |
| Contract marker placement | **New** `tests/test_hub_ui.py::test_dashboard_contract_marker_placement` — marker absent post-assembly; `js_contract_block()` after `function render(` and before `function filterOpenTickets` |
| All tests still pass | Full `pytest`; primary regressions: all `tests/test_hub_ui.py`; **updated** `tests/test_hub_contract.py` (`test_ui_imports_contract_for_dashboard_html`, `test_dashboard_js_api_paths_match_contract`, coupling fixture); `tests/test_hub.py` dashboard integration tests |

Existing substring tests are the definition of done; no assertion changes unless fixing a genuine bug.

## Documentation

- **`ui/__init__.py` docstring** — carry over `ui.py` header (no-build-step, four tabs, contract injection, mobile-first inline rationale).
- **Fragment docstrings** — one line each naming responsibility.
- **`contract.py` docstring** — if it references `ui.py`, update to `ui` package / `DASHBOARD_HTML`.
- **`docs/research/decisions.md`** — append approved ui-package-split decision (2026-06-10 analyze record).

**Contract consumers:** `server.py`, `tests/test_hub_ui.py`, `tests/test_hub_contract.py` (imports `DASHBOARD_HTML`; AST/coupling tests touch the package path).

## Risks

- **Module→package rename** — `ui.py` must be deleted before `import repo_scan.hub.ui` resolves the package; coexistence or stale `.pyc` can shadow the wrong target.
- **Contract marker drift** — moving `/* __HUB_CONTRACT__ */` breaks ticket styling; caught by contract-marker and open-tickets tests.
- **Fragment join order** — wrong order breaks JS parse or tab render; caught by layout-order tests and full pytest.
- **Cosmetic split** — arbitrary chunks pass line-cap but fail review; enforce semantic boundaries in review.
- **Hidden whitespace drift** — re-indenting changes bytes without failing symbol tests; **required** byte-parity hash mitigates.
- **`test_hub_contract.py` coupling** — `_UI` path and AST scan must move with the package or pytest fails on delete.

## Out of scope

- Browser/Playwright tests; Node JS runtime for embedded script.
- Dashboard UX, tab layout, or `contract.py` contents.
- Build tooling (bundler, template engine, CDN assets).
- Resolving tkt-0023 coupling metrics or refactoring unrelated `test_hub.py` imports.
- Splitting other hub modules (`server.py`, `tui.py`) or serving JS as separate static files.

## Audit

> [!warning] Audit verdict: revise
> The package/concat/contract-injection approach is sound and line caps are achievable, but fragment boundaries must be revised to match the actual 739-line source order (especially `rNow` vs `rFeed`/`rUsage`/`stat` and `tok`) before byte-parity and cohesion can both hold.
> - `_now` fragment table contradicts source order and the byte-identical goal: `rNow` (lines 352–367) precedes `tok` and the entire PR block, while `rFeed`, `rUsage`, and `stat` appear at lines 483–504 (~115 lines later); listing them together in `_now` implies reordering or a non-contiguous fragment the concat plan does not define.
> - `tok` is omitted from the fragment map but sits immediately after `rNow` and is required by `rUsage`; `test_rnow_layout_metrics_then_live_then_actions` anchors on `function tok` following `rNow`.
> - `_prs_gates` omits `rFeed`, `rUsage`, and `stat`, which physically live between `prAct` and `toggleGate`/`rGateCard`; leaving them unassigned or forcing them into `_now` breaks either cohesion or byte parity.
> - Cross-fragment JS risk is under-documented: `refresh()` in `_runtime` calls `applyPrLast()` in the PR fragment (same hoisting pattern as `rNow`→`rNowPRsAndGates` but only the latter is called out).
> - Tests section cites `tests/test_hub.py` dashboard integration against `DASHBOARD_HTML`, but that file does not import or reference `DASHBOARD_HTML`/`hub.ui`.
> - Research/analysis consumer list (`server.py`, `test_hub_ui.py` only) is stale; `tests/test_hub_contract.py` is a real consumer and is correctly listed under Contract consumers but the split rationale understates test surface.
> - Coupling fixture repoint to `ui/__init__.py` is underspecified: `test_server_ui_degree_below_threshold` synthesizes history on `_UI = repo_scan/hub/ui.py`, while `docs/reports/coupling.md` still tracks `repo_scan/hub/ui.py` as a single path—post-split rescans/path semantics are not addressed.
> - Line-count opener says 706 lines (ticket/health index) while Goal says 739; current file is 739 lines—harmonize the baseline so the ≤300-line budget is audited against one number.

## Provenance

- analysis: [[2026-06-10-split-repo-scan-hub-ui-py-706-lines-repo-analysis]]
