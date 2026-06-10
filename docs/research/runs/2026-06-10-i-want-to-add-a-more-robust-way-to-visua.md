---
type: "research-run"
question: "I want to add a more robust way to visualize changes out ogther a list of low hanging options we could include in the tickets such as simple visual diagrams as aid or soemthinf. _captured from intent — refine before approving_ Acceptance criteria: Tbd. Research current best practices and draft a spec for this work."
sources: ["gh-adamtornhill-code-maat", "gh-mermaid-js-mermaid", "url-codescene-io-docs-guides-technical-change-coupling-html"]
run_at: "2026-06-10 07:47 UTC"
---

# Research run — I want to add a more robust way to visualize changes out ogther a list of low hanging options we could include in the tickets such as simple visual diagrams as aid or soemthinf. _captured from intent — refine before approving_ Acceptance criteria: Tbd. Research current best practices and draft a spec for this work.
_Run 2026-06-10 07:47 UTC_

**Strategy:** Strategy: build on repo-scan's existing Markdown+Mermaid+Obsidian stack rather than a new renderer—mine git behavior for coupling/hotspot visuals (code-maat), embed focused per-ticket diagrams from the Mermaid catalog, and borrow CodeScene's coupling-graph semantics (hover neighborhoods, trend-colored edges) as the spec for change-over-time views.

## Ingested

- [[sources/gh-adamtornhill-code-maat\|adamtornhill/code-maat — A command line tool to mine and analyze data from version-control systems]] — Canonical open-source forensic git miner for temporal coupling, hotspots, and churn—with reference treemap/coupling visuals that directly extend repo-scan's table-only `coupling.md` into ticket-ready change diagrams.
- [[sources/gh-mermaid-js-mermaid\|mermaid-js/mermaid — Generation of diagrams like flowcharts or sequence diagrams from text in a…]] — Authoritative diagrams-as-code spec for gitGraph, sequence, timeline, and state diagrams that Obsidian/GitHub already render, giving a concrete low-effort palette for per-ticket change narratives without new UI.
- [[sources/url-codescene-io-docs-guides-technical-change-coupling-html\|Change Coupling: Visualize Logical Dependencies¶]] — Documents industry best practice for hierarchical change-coupling graphs with temporal trend encoding (strengthening vs weakening dependencies), a pattern repo-scan can mirror when highlighting affected subgraphs on seam and refactor tickets.
