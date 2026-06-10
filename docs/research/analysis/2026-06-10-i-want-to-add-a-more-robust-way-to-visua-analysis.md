---
type: "analysis"
problem: "I want to add a more robust way to visualize changes out ogther a list of low hanging options we could include in the tickets such as simple visual diagrams as aid or soemthinf. _captured from intent — refine before approving_ Acceptance criteria: Tbd. Research current best practices and draft a spec for this work."
confidence: "high"
sources: ["gh-adamtornhill-code-maat", "gh-mermaid-js-mermaid", "url-codescene-io-docs-guides-technical-change-coupling-html"]
generated_at: "2026-06-10 07:48 UTC"
---

# Analysis — I want to add a more robust way to visualize changes out ogther a list of low hanging options we could include in the tickets such as simple visual diagrams as aid or soemthinf. _captured from intent — refine before approving_ Acceptance criteria: Tbd. Research current best practices and draft a spec for this work.
_Generated 2026-06-10 07:48 UTC — confidence: high_

## Findings

- repo-scan already mines git history in a code-maat style (change coupling, ownership, age) and emits Mermaid for static graphs plus churn/complexity quadrants and bar charts — but coupling.md is table-only and tickets are prose with report links, not contextual diagrams.
- The largest visualization gap is behavioral: coupled pairs and hidden seams are computed and drive ticket proposals, yet never rendered as a graph; CodeScene and code-maat both treat change-coupling networks as first-class visuals, not tabular dumps.
- Mermaid is the right extension surface: repo-scan already commits diagrams-as-code for GitHub and Obsidian, and the catalog (flowchart subgraphs, sequence, timeline/gitGraph, quadrant) covers low-effort per-ticket aids without a new renderer or UI.
- Industry practice (CodeScene) layers temporal semantics on coupling — edge strength, strengthening vs weakening over windows, neighborhood focus around a module — which maps cleanly onto repo-scan's scan.json + trend delta model but is not implemented today.
- Low-hanging ticket enrichments: (1) Mermaid coupling graph with seam edges styled differently from import edges, (2) focused dependency/call subgraph for the files named in a ticket, (3) churn×complexity quadrant point highlight for refactor tickets, (4) optional gitGraph/timeline of recent touches on affected files.
- Tickets already carry structured fingerprints (refactor, seam, size) and evidence paths — diagram generation can be deterministic from scan.json at ticket-write time rather than hand-authored in each note.
- code-maat validates thresholds and co-change degree semantics already mirrored in config (coupling_min_shared, coupling_min_degree, coupling_max_changeset); no external Clojure dependency is needed for v1 visuals.
- Risk of over-building: full CodeScene-style interactive hover graphs and team-topology overlays exceed Markdown+Mermaid; a scoped subgraph-per-ticket approach delivers most ticket comprehension gain at lowest cost.

## Recommendation

Extend the existing Markdown+Mermaid pipeline with auto-generated, ticket-scoped diagrams sourced from scan.json: add a coupling network graph to reports/coupling.md, then embed a small “Evidence” Mermaid block in each auto-ticket (subgraph for seams/refactors, highlighted quadrant point for hotspots). Defer temporal trend coloring on coupling edges to a follow-up that windows git log the way CodeScene describes, reusing behavior.py rather than adopting code-maat as a runtime dependency.

## Risks

- Mermaid flowcharts degrade on large repos — subgraph capping and basename labels are required to keep ticket diagrams readable.
- GitHub vs Obsidian Mermaid feature parity differs (e.g. xychart-beta, quadrantChart); ticket aids should prefer widely supported graph TD subgraphs.
- Temporal coupling trends need an additional sliding-window pass over git history; mis-implementing could add scan latency or misleading trend arrows.
- Auto-embedded diagrams can stale if tickets are not regenerated on scan; tie diagram blocks to scan timestamps or regenerate on ticket sync.
- gitGraph/timeline diagrams narrate file touch order, not logical coupling — using them for seam tickets could confuse cause (co-change) with chronology.

## Evidence

- [[gh-adamtornhill-code-maat\|adamtornhill/code-maat — A command line tool to mine and analyze data from version-control systems]]
- [[gh-mermaid-js-mermaid\|mermaid-js/mermaid — Generation of diagrams like flowcharts or sequence diagrams from text in a…]]
- [[url-codescene-io-docs-guides-technical-change-coupling-html\|Change Coupling: Visualize Logical Dependencies¶]]
- research run: [[2026-06-10-i-want-to-add-a-more-robust-way-to-visua]]
