---
type: "research-run"
question: "Move the agentic loop graph and untracked code section to above the graph controls so filter graph and pancake graph options are just above +\- controls. _captured from intent — refine before approving_ Acceptance criteria: controls dispaly in stacked scetion together without break. Research current best practices and draft a spec for this work."
sources: ["url-www-nngroup-com-articles-gestalt-proximity", "url-www-w3-org-wai-aria-apg-patterns-toolbar", "gh-cytoscape-cytoscape.js"]
run_at: "2026-06-10 21:09 UTC"
---

# Research run — Move the agentic loop graph and untracked code section to above the graph controls so filter graph and pancake graph options are just above +\- controls. _captured from intent — refine before approving_ Acceptance criteria: controls dispaly in stacked scetion together without break. Research current best practices and draft a spec for this work.
_Run 2026-06-10 21:09 UTC_

**Strategy:** Mapped current render order in `rGraph()` (`_graph.py`, `_graph_dashboard.py`, `_graph_loop.py`): miss filters and untracked live in Vault audit, agentic loop sits between layer tabs and the +/- toolbar. Spec: keep summary/matrix/histogram in Vault audit; move agentic loop + untracked above a new `.graph-controls-stack` card containing filter row → layer tabs → zoom toolbar with zero section breaks, then canvas/legend; treat “pancake graph” as layer tabs (All/Coverage/Vault/Code). Cross-check proximity grouping and toolbar semantics against the three proposed sources before implementation.

## Ingested

- [[sources/url-www-nngroup-com-articles-gestalt-proximity\|Proximity Principle in Visual Design]] — NN/g’s proximity principle is the primary UX basis for colocating graph filters, layer tabs, and zoom controls in one uninterrupted stack directly above the canvas they manipulate.
- [[sources/url-www-w3-org-wai-aria-apg-patterns-toolbar\|Toolbar Pattern]] — W3C’s toolbar pattern defines how to semantically and visually group multiple related controls (filters, toggles, actions) into a single cohesive unit with predictable focus and keyboard behavior.
- [[sources/gh-cytoscape-cytoscape.js\|cytoscape/cytoscape.js — Graph theory (network) library for visualisation and analysis]] — Cytoscape.js is a widely adopted interactive graph viewer whose demo UIs place layer/filter and pan-zoom chrome immediately above the graph viewport—a concrete reference for stacked graph control placement.
