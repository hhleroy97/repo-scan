---
type: "spec"
problem: "Hidden seam: repo_scan/hub/server.py <-> repo_scan/hub/ui.py (88% coupled). `repo_scan/hub/server.py` and `repo_scan/hub/ui.py` changed together in 7 commits (88% degree) but share no import edge — an implicit contract the dependency graph can't see. Acceptance criteria: Make the dependency explicit (shared module or import); Coupling degree drops below threshold in coupling.md. Research current best practices and draft a spec for this work."
status: "approved"
audit_verdict: "revise"
analysis: "[[2026-06-10-hidden-seam-repo-scan-hub-server-py-repo-analysis]]"
drafted_at: "2026-06-10 17:30 UTC"
linked_files: ["repo_scan/hub/contract.py", "repo_scan/hub/server.py", "tests/test_hub.py", "tests/test_hub_contract.py", "tests/test_hub_ui.py"]
---

# Spec — Hidden seam: repo_scan/hub/server.py <-> repo_scan/hub/ui.py (88% coupled). `repo_scan/hub/server.py` and `repo_scan/hub/ui.py` changed together in 7 commits (88% degree) but share no import edge — an implicit contract the dependency graph can't see. Acceptance criteria: Make the dependency explicit (shared module or import); Coupling degree drops below threshold in coupling.md. Research current best practices and draft a spec for this work.
_Drafted 2026-06-10 17:30 UTC by radar — **status: approved**_

Verifying a few codebase facts so the revised spec matches the audit and implementation.
---
## Goal

Close the `server.py`↔`ui.py` seam (baseline: 7 shared commits, 88% degree; import edge `server → ui` via `DASHBOARD_HTML`—already visible, not in `hidden_seams`). The durable problem is connascence the graph under-specifies: `/api/*` route strings, `build_state()` JSON shape, and ticket workflow constants duplicated across Python and inline JS. Make those contracts explicit in a shared hub module so server and UI evolve through one importable surface, and reduce git co-change until rescanned `docs/reports/coupling.md` no longer lists the pair (`degree < coupling_min_degree` ⇒ absent from table). **Reviewer sign-off:** AC1 means explicit shared contracts, not removing the existing import edge (tkt-0008 audit gap).

## Approach

Follow the tkt-0008 `report_pipeline` extraction shape (shared module as published interface) but use PEP 589 `TypedDict` here—zero runtime cost, documents JSON wire shape; tkt-0008 used `@dataclass` for an in-process payload. Extract `repo_scan/hub/contract.py`: `API_*` path constants, ticket status/order/badge maps from `repo_scan.tickets`, POST `action → status` mapping, `HubState` keys, and `js_contract_block()` emitting ticket constants plus `API_*` literals for embedded JS. `server.py` imports contract for route matching and `build_state()`; `ui.py` splices `js_contract_block()` at `/* __HUB_CONTRACT__ */` when assembling `DASHBOARD_HTML` (no build step). Land extraction with parity tests first; then accumulate **~12–16** commits touching only `server.py`+`contract.py` or only `ui.py`+`contract.py` before rescan—with 7 shared / ~16 combined revs, `degree = round(200·shared/combined)` needs combined **>28** for **<50%**; tkt-0008’s **≥2** rule fits 53%/5-shared, not this pair. Expect the landing commit to touch `server.py`, `ui.py`, and `contract.py` together (shared **7→8**, degree may spike before divergent history).

## Changes

- **`repo_scan/hub/contract.py`** (new) — `API_*` path constants; `TICKET_ACTION_STATUSES`; `TICKET_STATUS_ORDER`, `TICKET_BADGE_CLS` (from `tickets.STATUSES` / `OPEN_STATUSES`); `HubState`, `TicketRow`, `GateRow`, `RunRow` `TypedDict`s; `HUB_STATE_KEYS` frozenset; `js_contract_block() -> str` (ticket maps + `API_*` for client `fetch`/`EventSource`).
- **`repo_scan/hub/server.py`** — Contract imports for `/api/*` matching and action `statuses`; `build_state` annotated `-> HubState`; no hand-maintained workflow or route strings.
- **`repo_scan/hub/ui.py`** — Template + `js_contract_block()` at `/* __HUB_CONTRACT__ */`; remove duplicate JS literals (ticket constants **and** hardcoded `/api/state`, `/api/events`, `/api/ticket`, etc.); drop stale alignment comment.
- **`tests/test_hub_contract.py`** (new) — Contract parity, import boundaries, coupling-degree fixture.
- **`tests/test_hub_ui.py`** — Replace regex parsing of hand-written constants with assertions on injected `js_contract_block()` vs contract exports; keep behavioral/render-structure tests (update assertions where injection changes HTML assembly, not “unchanged”).
- **Regenerated docs** — After divergent history, `repo-scan` and commit `docs/reports/coupling.md` plus dependent scan artifacts.

## Tests

| Acceptance criterion | Automated test |
|---|---|
| Explicit shared contract (AC1) | `tests/test_hub_contract.py::test_server_imports_contract_for_routes_and_actions` — `server` uses `contract.API_*` and `contract.TICKET_ACTION_STATUSES`, not inline duplicates. |
| Explicit shared contract (AC1) | `tests/test_hub_contract.py::test_ui_imports_contract_for_dashboard_html` — `DASHBOARD_HTML` includes `contract.js_contract_block()`; `ui` does not import `server`. |
| Route parity (AC1) | `tests/test_hub_contract.py::test_dashboard_js_api_paths_match_contract` — every `/api/*` in embedded JS comes from `contract.API_*`, not literals. |
| Contract parity (supports AC1) | `tests/test_hub_ui.py::test_open_ticket_statuses_match_python_contract` — injected `OPEN_TICKET_STATUSES` equals `OPEN_STATUSES`. |
| Contract parity (supports AC1) | `tests/test_hub_contract.py::test_ticket_action_status_map_matches_server_handler` — every dashboard POST action maps to `tickets.STATUSES` member. |
| State shape connascence (supports AC1) | `tests/test_hub_contract.py::test_build_state_keys_match_hub_state_contract` — `build_state()` keys equal `HUB_STATE_KEYS` (extend `tests/test_hub.py::test_build_state_*` if nested fields regress). |
| Coupling degree below threshold (AC2) | `tests/test_hub_contract.py::test_server_ui_degree_below_threshold` — fixture at 7 shared / 88%, landing + **≥12** single-side commits; `analyze_history` omits pair. |
| Coupling degree below threshold (AC2) | Post-rescan: `server.py`↔`ui.py` absent from committed `docs/reports/coupling.md`. |
| No regression | Existing `tests/test_hub.py` and `tests/test_hub_ui.py` behavioral/render tests pass (constant assertions updated for injection). |

## Documentation

- **`repo_scan/hub/contract.py`** — Published hub API/state contract; routes, ticket workflow, `HubState` wire shape for server, UI, and TUI. Distinct from `state.py` (run lifecycle helpers).
- **`repo_scan/hub/ui.py`** — `DASHBOARD_HTML` = template + `contract.js_contract_block()`.
- **`repo_scan/hub/server.py`** — `build_state` docstring references `HubState`; routes reference `contract.API_*`.
- Regenerated `docs/reports/coupling.md` and dependency-graph artifacts after rescan.

## Risks

- Extraction landing commit likely co-touches all three hub files—shared count and degree can worsen before divergent commits accumulate.
- `contract.py` may become a persistent co-change hub for `server.py` and `ui.py`; git coupling can remain high even if direct pair drops off the table.
- `HubState` in `contract.py` vs `state.py` naming; `TypedDict`/`HUB_STATE_KEYS` enforce server Python only—client `S.*` field connascence in inline JS stays untyped until a follow-on.
- Presentation changes (tabs, SSE) may still co-touch `server.py` and `ui.py` until absorbed into contract.
- `tui.py` / `tests/test_hub.py` depend on `build_state()` shape—contract field changes need fixture updates.
- `js_contract_block()` must emit valid JS (quoting, key order); malformed injection breaks the dashboard.

## Out of scope

Import Linter hub layering in CI, consumer-driven pact tooling, frontend bundler/build step, `tui.py` refactor to consume `HubState` types, typing/injecting client `S.*` shape, unrelated hidden seams (`config`↔`daemon`, `radar/cli`↔`gates`), changing `coupling_min_degree` / `coupling_min_shared`, visual/dashboard UX beyond contract injection.
---

## Audit

> [!warning] Audit verdict: revise
> The contract-extraction direction matches analysis and code evidence, but the spec should fix AC2 commit math, align ticket AC1 with connascence (not the existing import), and tighten API-path and TypedDict scope before human review.
> - Ticket/title framing is stale: coupling.md lists server↔ui with import edge yes and the pair is absent from the four hidden_seams entries; durable work is connascence of routes/JSON/status strings, not a missing import. Spec Goal corrects this but ticket AC1 still reads 'shared module or import' while server→ui via DASHBOARD_HTML already exists—AC1 can be misread as already done without contract.py.
> - AC2 math is off-by-one: degree = round(200·shared/(revs[a]+revs[b])) with shared=7 and baseline rev sum ≈16 (88%) needs ≥13 single-side commits for degree <50, not ≥12 (12 yields exactly 50%, which coupling_min_degree still emits). After a landing commit (shared→8, rev sum→18), need ≥15 single-side commits.
> - Approach says '~12–16' divergent commits but the Tests table says '≥12'—internally inconsistent and both understate the post-landing floor (~15).
> - Research analysis recommends '≥2 post-refactor commits' (tkt-0008 precedent); spec rightly notes that does not transfer to 7-shared/88%, but the proposed test_server_ui_degree_below_threshold still encodes the wrong threshold (≥12).
> - Changes claim TICKET_BADGE_CLS is sourced from tickets.STATUSES/OPEN_STATUSES; badge CSS classes are UI-only presentation mappings with no tickets.py equivalent—unsupported by codebase.
> - test_dashboard_js_api_paths_match_contract is underspecified: ui.py uses dynamic fetch('/api/pr/'+op) and api('/api/doc?path='+...), not bare /api/pr/merge-style literals; contract needs a prefix/query pattern or the test cannot pass as written.
> - GateRow TypedDict omits enrich_gate drawer fields (excerpt, analysis_doc, criteria, stale_warning) that the dashboard reads—HubState typing may imply AC1 closure while client connascence on nested shapes remains.
> - AC2 couples an isolated git fixture (good) with committed docs/reports/coupling.md after rescan (manual); no guard that the live repo actually accumulates the ~13+ choreographed single-side commits before rescan—same compliance gap noted in other hidden-seam specs.
> - Missing risk: satisfying AC1 via contract.py does not stop presentation/SSE/PR-workflow edits from co-touching server.py and ui.py; AC2 is primarily a time-dependent git-history exercise decoupled from contract quality.

## Provenance

- analysis: [[2026-06-10-hidden-seam-repo-scan-hub-server-py-repo-analysis]]
