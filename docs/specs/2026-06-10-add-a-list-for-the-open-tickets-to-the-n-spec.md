---
type: "spec"
problem: "Add a list for the open tickets to the now page. To track open tickets or feature from the main lage Acceptance criteria: List properly appears with expected tickets and selected fields visible. Research current best practices and draft a spec for this work."
status: "approved"
audit_verdict: "revise"
analysis: "[[2026-06-10-add-a-list-for-the-open-tickets-to-the-n-analysis]]"
drafted_at: "2026-06-10 05:43 UTC"
linked_files: ["tests/test_hub_ui.py"]
---

# Spec — Add a list for the open tickets to the now page. To track open tickets or feature from the main lage Acceptance criteria: List properly appears with expected tickets and selected fields visible. Research current best practices and draft a spec for this work.
_Drafted 2026-06-10 05:43 UTC by radar — **status: approved**_

## Goal

Surface open ticket work on the **Now** tab so users can see pending features and fixes at a glance without switching to Tickets. Open means non-terminal statuses (`proposed`, `approved`, `in-progress`). Acceptance: the list shows the correct tickets with status, priority, kind, id, and title visible.

## Approach

Client-only change in `rNow()`. Reuse `S.tickets` from `/api/state` (fields already provided by `build_state()`). Hoist shared ticket helpers (`OPEN_TICKET_STATUSES`, `TICKET_STATUS_ORDER`, `TICKET_BADGE_CLS`, `filterOpenTickets()`, `sortTickets()`) so `rNow()` and `rTickets()` stay consistent.

Add an **Open tickets** block when the filtered list is non-empty:
- **Placement:** immediately after the gates warning card when gates exist; otherwise immediately after the stats grid (mirrors gates progressive-disclosure pattern).
- **Layout:** section header with count; `.card` of compact `.run` rows (denser than `rTickets()` full `.card` rows; same `.run` density as Runs / Agent feed).
- **Row fields:** status badge (color map from `rTickets()`), optional kind + priority badges, `id`, title (truncate ~90 chars; omit `why`). Same-status ties keep current `rTickets()` order (array index; not stabilized).
- **Actions:** read-only on Now; **View all** button calls `setTab('tickets')`.
- **Empty:** omit the section entirely (no placeholder).

Sort by status workflow order (`proposed` → `approved` → `in-progress`), matching `rTickets()`. Include `in-progress` (broader than TUI `actionable_items()`, which only lists `proposed`/`approved`).

## Changes

- **`repo_scan/hub/ui.py`**
  - Extract shared ticket constants and `filterOpenTickets` / `sortTickets` helpers; refactor `rTickets()` to use them.
  - Add `rOpenTickets()` (or inline block) called from `rNow()` with placement rules above.
  - Update module docstring: Now tab includes open tickets summary.

## Tests

Acceptance criteria → automated tests in new **`tests/test_hub_ui.py`**. Inspect `DASHBOARD_HTML` / `ui.py` source with Python (`re` or literal substring checks on hoisted helper definitions)—no Node `<script>` extraction; no new CI tooling.

| Criterion | Test |
|-----------|------|
| List shows expected open tickets | `test_open_tickets_filter_includes_only_non_terminal` — fixture tickets across all five statuses; assert `filterOpenTickets()` returns exactly `proposed`, `approved`, `in-progress` and excludes `done`/`rejected`. |
| List shows expected open tickets | `test_open_tickets_sort_follows_workflow_order` — mixed open statuses; assert sort order is `proposed` → `approved` → `in-progress`. |
| Selected fields visible | `test_rnow_open_tickets_renders_rows_for_fixture` — call render path with non-empty open-ticket fixture; assert output includes status badge, priority, kind, id, and title per row (not grep-only on unconditional template strings). |
| Section hidden when nothing open | `test_open_tickets_section_omitted_when_empty` — empty / all-terminal fixture yields no `Open tickets` markup from the same render path used when non-empty. |

Do not extend `test_dashboard_html_served` with a static `Open tickets` marker check—the default hub fixture has no open tickets, which contradicts the empty-state rule.

## Documentation

- **`repo_scan/hub/ui.py`** — module docstring: Now tab lists open tickets (summary) plus stats, runs, feed.
- **`README.md`** — "The hub" section: Now tab shows open tickets with link to full Tickets tab; approve/create actions remain on Tickets (and TUI for terminal).

## Risks

- **Nav badge mismatch:** `ntickets` still counts only `proposed`; Now may list more — mitigate with section header count, not badge change (unless follow-up).
- **Backend/JS drift:** `repo_scan/tickets.py` already defines `OPEN_STATUSES` with the same three values; hoisted JS constants are not tied to that contract — document parity intent; consider a comment cross-reference in `ui.py`.
- **Stale list while composing:** 12s polling and `formBusy()` skipping main re-render on Tickets can leave the Now tab list stale until navigation or form clear.
- **TUI semantics:** web includes `in-progress`; TUI `actionable_items()` does not — document intentional difference.
- **Mobile clutter:** cap title length; no `why` on Now rows; same-status order may feel arbitrary.
- **Drift:** shared JS helpers must stay the single source for filter/sort; tests lock the contract.

## Out of scope

- `build_state()` / API changes.
- Ticket actions, composer, or editing on Now.
- Nav badge logic change to count all open tickets.
- TUI `actionable_items()` parity (optional follow-up).
- Priority-based sort (status workflow only, as `rTickets()` today).
- New dependencies or frontend build tooling.
- Python `OPEN_STATUSES` ↔ JS constant codegen or shared test fixture (optional follow-up).

## Audit

> [!warning] Audit verdict: revise
> The functional approach aligns well with codebase facts (`build_state()` fields, `rTickets()` status-order sort, `OPEN_STATUSES`, gates-card precedent, nav-badge mismatch), but the test strategy must be rewritten to match client-only rendering constraints before human review.
> - Test plan is internally inconsistent and largely infeasible as written: `filterOpenTickets()`, `sortTickets()`, and `rNow()` live inside embedded client-side JS in `DASHBOARD_HTML`, so Python cannot call them or assert per-fixture rendered markup without a JS runtime; static `re`/substring checks on `ui.py` only prove source presence, not behavior, which conflicts with tests that assert function return values and fixture-specific HTML output while also forbidding Node and new CI tooling.
> - `test_rnow_open_tickets_renders_rows_for_fixture` and `test_open_tickets_section_omitted_when_empty` cannot be satisfied via the existing `hub_server`/`test_dashboard_html_served` pattern because the served HTML shell is filled by browser JS after `/api/state` fetch—fixture tickets never appear in the initial response.
> - When gates exist, placement puts open tickets before the stats grid (gates → open tickets → stats → runs), materially reordering the Now tab; the spec does not note the UX tradeoff of pushing scan stats below the ticket list.
> - Stale-UI risk is understated: pre-existing `formBusy()` causes `render()` to skip all tab updates while the Tickets composer has draft text, so switching to Now can leave the new list stale or stale content visible—not only 12s polling lag on Tickets.
> - Minor inaccuracy: same-status ordering is stabilized in modern JS `Array.prototype.sort`, so 'not stabilized' misstates current `rTickets()` tie behavior (original `S.tickets` order is preserved).

## Provenance

- analysis: [[2026-06-10-add-a-list-for-the-open-tickets-to-the-n-analysis]]
