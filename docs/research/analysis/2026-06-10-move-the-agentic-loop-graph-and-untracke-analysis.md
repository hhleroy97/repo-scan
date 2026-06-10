---
type: "analysis"
problem: "Move the agentic loop graph and untracked code section to above the graph controls so filter graph and pancake graph options are just above +\- controls. _captured from intent — refine before approving_ Acceptance criteria: controls dispaly in stacked scetion together without break. Research current best practices and draft a spec for this work."
confidence: "high"
sources: ["url-www-nngroup-com-articles-gestalt-proximity", "url-www-w3-org-wai-aria-apg-patterns-toolbar", "gh-cytoscape-cytoscape.js"]
generated_at: "2026-06-10 21:20 UTC"
linked_files: ["tests/test_hub_ui.py"]
---

# Analysis — Move the agentic loop graph and untracked code section to above the graph controls so filter graph and pancake graph options are just above +\- controls. _captured from intent — refine before approving_ Acceptance criteria: controls dispaly in stacked scetion together without break. Research current best practices and draft a spec for this work.
_Generated 2026-06-10 21:20 UTC — confidence: high_

## Findings

- Current render order in rGraph() splits graph-manipulation UI: miss filters and untracked code live inside rGraphDashboard() (Vault audit), while layer tabs, agentic loop (rGraphPipeline), and zoom toolbar (+/−/Fit/Re-layout) are interleaved in the Provenance graph block — filters are ~200px+ away from the canvas they affect.
- “Pancake graph” maps to the horizontal layer tabs (All / Coverage / Vault / Code) in graph-tabs — pill-shaped toggles that reshape the canvas; they currently sit above the agentic loop, not adjacent to zoom controls.
- Gestalt proximity: filter buttons, layer tabs, and pan/zoom actions are one functional group (view configuration) and should share tight vertical spacing; informational panels (loop diagram, untracked queue) belong above that group, separated by a section break or card margin.
- WAI-ARIA toolbar pattern supports wrapping filter chips, layer toggles, and zoom actions in a single role="toolbar" container with aria-label="Graph controls" — one Tab stop, optional roving arrow focus — without changing the canvas implementation.
- Cytoscape.js and similar graph viewers conventionally place filter/layer chrome immediately above the viewport; the proposed stack (context panels → controls → canvas → legend) matches industry layout.
- setGraphMissFilter() re-renders via el.innerHTML=rGraph() then mountGraph(), so DOM order changes must preserve element IDs (agentic-loop-host, graph-wrap, graph-canvas) and .loop-card for _updateLoopBanner() live refresh.
- Acceptance criterion “stacked section together without break” implies a new .graph-controls-stack wrapper: filter row → layer tabs → toolbar with 4–6px internal gap, zero .section headings or card borders between rows, and margin-bottom:0 on child rows so flex-wrap does not insert phantom whitespace before the canvas.

## Recommendation

Refactor rGraph() to keep summary/matrix/histogram (and optionally thin-links/trend) in Vault audit; move rGraphPipeline() and rDashUntracked() into a new block between Vault audit and Provenance graph; extract rDashMissFilters() from rGraphDashboard() into a contiguous .graph-controls-stack containing miss filters, graph-tabs, and graph-toolbar in that order, directly above graph-wrap. Style the stack as one card or bordered panel with tight internal spacing and a single toolbar landmark; bump tests/test_hub_ui.py _DASHBOARD_HTML_SHA256 after CSS/HTML changes.

## Risks

- Untracked code panel moves away from the summary metric card that shows untracked count — users may not associate the list with the headline number without a scroll.
- Agentic loop Mermaid block is tall; placing it above controls pushes zoom/filter chrome down on mobile, partially defeating the goal of quicker access to +/−.
- flex-wrap on narrow viewports can visually break the “no break” stack if filter chips and tabs wrap to multiple lines — may need a vertical toolbar orientation on small screens.
- setGraphMissFilter’s full re-mount may flash the loop diagram and reset scroll position unless render is optimized to skip Mermaid when source unchanged.
- Filter row is empty when no orphan signals exist — stack may collapse to tabs+toolbar only; document as acceptable or show a dim placeholder for layout stability.

## Evidence

- [[url-www-nngroup-com-articles-gestalt-proximity\|Proximity Principle in Visual Design]]
- [[url-www-w3-org-wai-aria-apg-patterns-toolbar\|Toolbar Pattern]]
- [[gh-cytoscape-cytoscape.js\|cytoscape/cytoscape.js — Graph theory (network) library for visualisation and analysis]]
- research run: [[2026-06-10-move-the-agentic-loop-graph-and-untracke]]
