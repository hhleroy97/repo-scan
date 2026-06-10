---
type: "research-run"
question: "Convert tickets to most human friendly/tech leas project manager terms in. The approval/ticket cards . Retain current ticket as ground truth and have these ticket be abstractions of that ground truth. Easier to interact with when making decisions form a mobile device Acceptance criteria: define acceptance criteria before approving. Research current best practices and draft a spec for this work."
sources: ["arxiv-2411.12924", "gh-stackingturtles-linearstories", "url-www-nngroup-com-articles-progressive-disclosure"]
run_at: "2026-06-10 06:10 UTC"
---

# Research run — Convert tickets to most human friendly/tech leas project manager terms in. The approval/ticket cards . Retain current ticket as ground truth and have these ticket be abstractions of that ground truth. Easier to interact with when making decisions form a mobile device Acceptance criteria: define acceptance criteria before approving. Research current best practices and draft a spec for this work.
_Run 2026-06-10 06:10 UTC_

**Strategy:** Strategy: combine a dual-representation data model (detailed ticket file + derived PM card fields), gate UX that blocks approval until testable acceptance criteria exist, and a three-tier card hierarchy (summary → criteria → full doc) optimized for mobile decision-making.

## Ingested

- [[sources/arxiv-2411.12924\|Human-In-the-Loop Software Development Agents]] — HULA documents empirically how engineers review and approve AI-generated plans inside JIRA gates, defining what decision-ready summaries must contain before a human signs off.
- [[sources/gh-stackingturtles-linearstories\|stackingturtles/linearstories — A tool for managing Agent Developer requirements in Linear]] — It enforces markdown tickets as source of truth with structured acceptance-criteria checklists while projecting a separate PM-friendly issue view—direct precedent for ground-truth vs abstraction layers.
- [[sources/url-www-nngroup-com-articles-progressive-disclosure\|Progressive Disclosure]] — NN/g's canonical progressive-disclosure model specifies how to layer glance-level approval cards for mobile with drill-down to full ticket ground truth on demand.
