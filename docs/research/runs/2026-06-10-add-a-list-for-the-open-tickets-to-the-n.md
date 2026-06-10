---
type: "research-run"
question: "Add a list for the open tickets to the now page. To track open tickets or feature from the main lage Acceptance criteria: List properly appears with expected tickets and selected fields visible. Research current best practices and draft a spec for this work."
sources: ["gh-humanlayer-humanlayer", "gh-makeplane-plane"]
run_at: "2026-06-10 05:35 UTC"
---

# Research run — Add a list for the open tickets to the now page. To track open tickets or feature from the main lage Acceptance criteria: List properly appears with expected tickets and selected fields visible. Research current best practices and draft a spec for this work.
_Run 2026-06-10 05:35 UTC_

**Strategy:** Anchor the spec on the existing gates card in `rNow()` as the local precedent, then borrow Plane's open-work list field choices and NN/g's progressive-disclosure hierarchy to decide which non-terminal ticket statuses appear on Now and which actions stay on the Tickets tab. No new API surface is needed—filter `S.tickets` client-side by open statuses.

## Ingested

- [[sources/gh-humanlayer-humanlayer\|humanlayer/humanlayer — The best way to get AI coding agents to solve hard problems in complex…]] — The project's hub changelog already cites HumanLayer's daemon-plus-dashboard pattern, and its WUI surfaces pending approvals on the main view—the same progressive-disclosure model needed for an open-tickets summary on the Now tab.
- [[sources/gh-makeplane-plane\|makeplane/plane — 🔥🔥🔥 Open-source Jira, Linear, Monday, and ClickUp alternative. Plane is a…]] — Plane's 'Your work' home dashboard shows filtered open issues with status, priority, and title in a compact list, providing a concrete open-source reference for which ticket fields to expose at a glance versus in a detail tab.

## Failed

- `url:https://www.nngroup.com/articles/dashboards-preattentive/` — fetch failed for https://www.nngroup.com/articles/dashboards-preattentive/: <urlopen error [SSL: UNEXPECTED_EOF_WHILE_READING] EOF occurred in violation of protocol (_ssl.c:1007)>
