---
type: "analysis"
problem: "Add a list for the open tickets to the now page. To track open tickets or feature from the main lage Acceptance criteria: List properly appears with expected tickets and selected fields visible. Research current best practices and draft a spec for this work."
confidence: "high"
sources: ["gh-humanlayer-humanlayer", "gh-makeplane-plane"]
generated_at: "2026-06-10 05:38 UTC"
---

# Analysis — Add a list for the open tickets to the now page. To track open tickets or feature from the main lage Acceptance criteria: List properly appears with expected tickets and selected fields visible. Research current best practices and draft a spec for this work.
_Generated 2026-06-10 05:38 UTC — confidence: high_

## Findings

- The Now tab in `repo_scan/hub/ui.py` already surfaces urgent work (gates card, runs, agent feed) but has no ticket section; open work is only visible on the Tickets tab or via the nav badge, which counts `proposed` tickets only.
- `/api/state` already returns ticket rows with `id`, `status`, `title`, `priority`, `why`, and `kind` (from fingerprint prefix) via `build_state()` — no new API or backend work is required; filter `S.tickets` client-side in `rNow()`.
- The terminal TUI (`actionable_items()` in `repo_scan/hub/tui.py`) already defines a local precedent: gates first, then tickets in `proposed` or `approved` status with compact `[status] id title` rows — the web Now list should align with or slightly extend this (include `in-progress` for full open-work visibility).
- HumanLayer's hub pattern (cited in repo changelog) validates progressive disclosure: pending human decisions belong on the home view; the existing gates warning card is the exact UI pattern to mirror for open tickets (summary card + link to full tab).
- Plane's home/'Your work' view supports exposing status, priority, and title in a compact scannable list while keeping create/edit/actions on a dedicated work-items screen — matching repo-scan's split between Now (glance) and Tickets (full board + composer).
- Ticket statuses are a fixed five-state workflow (`proposed` → `approved` → `in-progress` → `done`/`rejected` in `repo_scan/tickets.py`); 'open' should mean all non-terminal statuses (`proposed`, `approved`, `in-progress`), sorted by the same priority order already used in `rTickets()`.
- Acceptance criteria map cleanly to a UI-only change in `ui.py` plus a focused test asserting `rNow()` output includes expected open tickets and fields; TUI parity is optional follow-up.

## Recommendation

Add an 'Open tickets' section to `rNow()` immediately after the gates card (or after the stats grid if no gates), filtering `S.tickets` to non-terminal statuses and rendering compact `.run`-style rows with status badge, priority, kind, id, and title — reusing the badge color map from `rTickets()`. Include a 'View all' button that calls `setTab('tickets')` and hide the section when the filtered list is empty. No server changes; add a small JS unit test or extend hub UI tests to lock in field visibility and sort order.

## Risks

- Ambiguity over 'open' vs 'actionable': TUI excludes `in-progress` tickets but the feature title says 'open tickets' — including in-progress avoids hiding active work but may differ from TUI semantics unless both surfaces are aligned.
- Nav badge (`ntickets`) only counts `proposed` while the Now list may show more tickets, which could confuse users unless the badge logic is updated or the section header shows its own count.
- Polling every 12s with `formBusy()` guards may cause the new list to feel stale while a user is composing on the Tickets tab — acceptable but worth noting in the spec.
- Long titles and optional `why` text on a mobile-first Now view can clutter the home screen; cap title length (as runs already do at ~90 chars) and omit `why` from the summary row.

## Evidence

- [[gh-humanlayer-humanlayer\|humanlayer/humanlayer — The best way to get AI coding agents to solve hard problems in complex…]]
- [[gh-makeplane-plane\|makeplane/plane — 🔥🔥🔥 Open-source Jira, Linear, Monday, and ClickUp alternative. Plane is a…]]
- research run: [[2026-06-10-add-a-list-for-the-open-tickets-to-the-n]]
