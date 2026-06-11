---
type: "analysis"
problem: "Convert tickets to most human friendly/tech leas project manager terms in. The approval/ticket cards . Retain current ticket as ground truth and have these ticket be abstractions of that ground truth. Easier to interact with when making decisions form a mobile device Acceptance criteria: define acceptance criteria before approving. Research current best practices and draft a spec for this work."
confidence: "high"
sources: ["arxiv-2411.12924", "gh-stackingturtles-linearstories", "url-www-nngroup-com-articles-progressive-disclosure"]
generated_at: "2026-06-10 06:11 UTC"
linked_files: ["repo_scan/tickets/parse.py", "repo_scan/hub/ui/_tickets.py"]
---

# Analysis — Convert tickets to most human friendly/tech leas project manager terms in. The approval/ticket cards . Retain current ticket as ground truth and have these ticket be abstractions of that ground truth. Easier to interact with when making decisions form a mobile device Acceptance criteria: define acceptance criteria before approving. Research current best practices and draft a spec for this work.
_Generated 2026-06-10 06:11 UTC — confidence: high_

## Findings

- repo-scan already has the right ground-truth model: markdown tickets in docs/tickets/ with YAML frontmatter, Why, and checkbox acceptance criteria parsed by repo_scan/tickets.py and surfaced in the mobile hub — the gap is presentation and gating, not storage.
- Current approval cards expose agent/scan-native language (e.g. CC scores, file paths, commit counts) as titles, which is poor for mobile triage; linearstories validates keeping the detailed markdown file canonical while projecting a separate human/PM-facing view derived from it.
- Checkbox acceptance criteria already map cleanly to agent-verifiable scope, but approval is not enforced: tickets can be proposed with placeholder criteria ('define done') and the hub Approve action does not require non-empty, testable criteria before status changes.
- HULA’s real-world JIRA deployment shows human gates work best when each stage presents a decision-ready summary (what, why, risks, confidence) rather than raw agent output — repo-scan’s Gates tab already structures findings/risks/confidence but ticket cards lack an equivalent PM abstraction layer.
- Nielsen Norman progressive disclosure fits the mobile hub constraint: show a glance card (outcome, priority, status, criteria count) on Now/Gates/Tickets, expand to criteria checklist, then full markdown doc on demand — matching the research-run three-tier hierarchy without duplicating source files.
- Dual representation should be derived, not hand-maintained: add optional frontmatter or a ## Card section (title, one-line outcome, user-story framing) generated or suggested at ticket creation and refreshed when ground truth changes, with the markdown file remaining the single write path for agents and humans.

## Recommendation

Introduce a derived PM card layer on top of existing tkt-*.md files: parse ground truth into a mobile-first summary (plain-language title, Why in one sentence, criteria checklist with count, priority/status badges) using progressive disclosure in hub/ui.py, and block Approve until at least one non-placeholder acceptance criterion exists. Keep markdown tickets as the only source of truth; optionally auto-suggest PM-friendly titles from Why + outcome at propose/create time, with drill-down to the full ticket file for agents and auditors.

## Risks

- Derived summaries can drift from ground truth if not regenerated when the markdown file changes — need a single parse path (extend parse_ticket) rather than a parallel editable card file.
- Blocking approval on acceptance criteria may stall auto-proposed scan tickets that arrive with technical titles but empty criteria unless the propose flow auto-drafts testable criteria from scan signals.
- Translating technical refactor tickets into PM language may lose precision agents need unless the full ground-truth title and evidence links remain accessible one tap away.
- Adding frontmatter fields or a Card section increases ticket schema surface area; agents and Obsidian Kanban board.md generation must stay backward-compatible with existing tickets.

## Evidence

- [[arxiv-2411.12924\|Human-In-the-Loop Software Development Agents]]
- [[gh-stackingturtles-linearstories\|stackingturtles/linearstories — A tool for managing Agent Developer requirements in Linear]]
- [[url-www-nngroup-com-articles-progressive-disclosure\|Progressive Disclosure]]
- research run: [[2026-06-10-convert-tickets-to-most-human-friendly-t]]
