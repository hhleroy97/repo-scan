---
type: "analysis"
problem: "Hidden seam: repo_scan/hub/server.py <-> repo_scan/hub/ui.py (88% coupled). `repo_scan/hub/server.py` and `repo_scan/hub/ui.py` changed together in 7 commits (88% degree) but share no import edge — an implicit contract the dependency graph can't see. Acceptance criteria: Make the dependency explicit (shared module or import); Coupling degree drops below threshold in coupling.md. Research current best practices and draft a spec for this work."
confidence: "high"
sources: ["url-thoughtbot-com-blog-connascence-as-a-vocabulary-to-discuss-c", "url-peps-python-org-pep-0589", "gh-seddonym-import-linter"]
generated_at: "2026-06-10 17:20 UTC"
linked_files: ["repo_scan/hub/contract.py", "repo_scan/hub/server.py", "tests/test_hub_ui.py"]
---

# Analysis — Hidden seam: repo_scan/hub/server.py <-> repo_scan/hub/ui.py (88% coupled). `repo_scan/hub/server.py` and `repo_scan/hub/ui.py` changed together in 7 commits (88% degree) but share no import edge — an implicit contract the dependency graph can't see. Acceptance criteria: Make the dependency explicit (shared module or import); Coupling degree drops below threshold in coupling.md. Research current best practices and draft a spec for this work.
_Generated 2026-06-10 17:20 UTC — confidence: high_

## Findings

- coupling.md already records an import edge (server.py → ui.py via DASHBOARD_HTML), so the ticket’s ‘no import edge’ premise is partially stale—like tkt-0008/scanner↔writers, the durable problem is connascence the graph still cannot see, not the absence of any import.
- The 88% co-change (7 shared commits, highest in the report) persists because server.py and ui.py share multiple implicit contracts: /api/* route paths and POST bodies, the build_state() JSON shape (tickets, gates, runs, live_runs, activity, prs, usage), and ticket workflow strings (proposed/approved/in-progress, action→status mapping).
- Connascence vocabulary fits this seam precisely: connascence of name on field and route strings, connascence of meaning on ticket status semantics (JS OPEN_TICKET_STATUSES/TICKET_STATUS_ORDER/TICKET_BADGE_CLS vs repo_scan.tickets.OPEN_STATUSES and server POST statuses dict), and connascence of position on nested object shapes the dashboard reads from S.*.
- tests/test_hub_ui.py already encodes the drift risk—it regex-parses DASHBOARD_HTML to assert OPEN_TICKET_STATUSES matches OPEN_STATUSES, proving the contract is real but enforced indirectly rather than through a shared, importable module.
- PEP 589 TypedDict is a zero-runtime-cost fit for formalizing build_state() as HubState (and nested TicketRow, GateRow, RunRow types) in a shared hub module importable by server.py, tui.py, and tests without adding dependencies.
- Import Linter can codify the intended hub layering after extraction (e.g. ui may import hub.contract but must not import server; server may import ui for HTML shell and contract for routes/schema), preventing future back-edges that recreate invisible coupling.
- AC2 requires degree strictly below the 50% coupling_min_degree threshold; per tkt-0008/config-daemon precedent, landing a shared contract module alone is insufficient—≥2 post-refactor commits must touch only server/contract or only ui/contract before rescanned coupling.md drops the pair.
- ui.py’s inline, no-build-step HTML constraint means the practical way to single-source JS constants is Python-side template injection from the shared contract at DASHBOARD_HTML assembly time, not a separate frontend bundle or consumer-driven pact layer.

## Recommendation

Extract repo_scan/hub/contract.py owning API route constants, ticket status/order/badge maps (sourced from repo_scan.tickets.OPEN_STATUSES), POST action→status mapping, and TypedDict types for build_state(); have server.py import it for routes and payload assembly, and have ui.py import it to inject generated JS constant blocks into DASHBOARD_HTML (replacing hand-maintained OPEN_TICKET_STATUSES/TICKET_STATUS_ORDER duplicates). Add contract parity tests (extend test_hub_ui.py to assert injected constants and required state keys), land the refactor, then accumulate ≥2 divergent commits on one side only so rescanned coupling.md reports degree <50%; optionally add an import-linter contract in CI as a follow-on.

## Risks

- Template injection into a 700-line raw HTML string is easy to get wrong; a small builder helper or explicit placeholder markers are needed to avoid breaking the self-contained dashboard.
- Any API or ticket-workflow change may still co-touch server.py and ui.py until the contract module absorbs new fields—extraction reduces connascence strength but does not eliminate co-evolution of presentation logic.
- Historical 88% degree will not fall until new divergent git history accumulates post-merge; the refactor satisfies AC1 immediately but AC2 is time-dependent.
- tui.py and test_hub.py also consume build_state() shape; contract changes ripple beyond server/ui and need snapshot or fixture updates.
- Import-linter is not yet adopted; without it, explicit imports improve graph visibility but do not automatically block future string drift in embedded JS.

## Evidence

- [[url-thoughtbot-com-blog-connascence-as-a-vocabulary-to-discuss-c\|Connascence as a vocabulary to discuss Coupling]]
- [[url-peps-python-org-pep-0589\|PEP 589 – TypedDict: Type Hints for Dictionaries with a Fixed Set of Keys | peps.python.org]]
- [[gh-seddonym-import-linter\|seddonym/import-linter — Lint your Python architecture.]]
- research run: [[2026-06-10-hidden-seam-repo-scan-hub-server-py-repo]]
