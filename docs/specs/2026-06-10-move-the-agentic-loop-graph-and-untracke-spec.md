---
type: "spec"
problem: "Move the agentic loop graph and untracked code section to above the graph controls so filter graph and pancake graph options are just above +\- controls. _captured from intent — refine before approving_ Acceptance criteria: controls dispaly in stacked scetion together without break. Research current best practices and draft a spec for this work."
status: "approved"
audit_verdict: "revise"
analysis: "[[2026-06-10-move-the-agentic-loop-graph-and-untracke-analysis]]"
drafted_at: "2026-06-10 21:37 UTC"
---

# Spec — Move the agentic loop graph and untracked code section to above the graph controls so filter graph and pancake graph options are just above +\- controls. _captured from intent — refine before approving_ Acceptance criteria: controls dispaly in stacked scetion together without break. Research current best practices and draft a spec for this work.
_Drafted 2026-06-10 21:37 UTC by radar — **status: approved**_

Reviewing the graph UI structure so the revised spec matches the codebase.
## Goal

Reorganize the Knowledge dashboard tab so **view-configuration controls** (miss filters, layer tabs, zoom toolbar) form one contiguous stack directly above the provenance canvas, while **informational panels** (agentic loop Mermaid, untracked code queue) sit above that stack. Filters and layer tabs (`graph-tabs`, ticket “pancake” toggles) should be immediately adjacent to +/−/Fit/Re-layout — not separated by audit metrics, the loop diagram, or a section heading.

## Approach

Refactor `rGraph()` render order to: **Vault audit metrics → context panels (loop then untracked) → unified controls stack → canvas → legend/hint**. **Remove** the standalone `<div class="section">Provenance graph</div>` divider (or relocate it above context panels only); it must not sit between context panels and the controls stack or between the stack and canvas.

Extract miss filters from `rGraphDashboard()` into `rGraphControlsStack()` wrapping filter row, `graph-tabs`, and `graph-toolbar` in `.graph-controls-stack` with `role="group"` and `aria-label="Graph controls"` (landmark label only — no roving tabindex; full toolbar keyboard model is out of scope).

“Contiguous” means **no `.section` / `.dash-section` / card borders between stack rows and `graph-wrap`**; row-level `flex-wrap` within filters/tabs/toolbar is acceptable at default widths. CSS uses a vertical flex column (`flex-direction: column`, `gap: 4–6px`); optional `@media (max-width: 640px)` stacks toolbar rows vertically.

Preserve stable IDs (`agentic-loop-host`, `graph-wrap`, `graph-canvas`) and `.loop-card` structure for live banner refresh. `.graph-context-panels` wraps **whole** `.loop-card` and untracked `<details>` — no extra `div` inside `.loop-card` before its banner child (`_updateLoopBanner()` targets `.loop-card>div:first-of-type`).

Target layout:

```
Vault audit (summary, matrix, histogram, thin-links, trend)
Agentic loop → Untracked code
┌─ Graph controls (one panel) ─────────────┐
│ Filter graph chips (when orphans exist)  │
│ All / Coverage / Vault / Code tabs       │
│ + − Fit Re-layout · node count           │
└──────────────────────────────────────────┘
[ canvas ]
legend · hint
```

## Changes

- **`repo_scan/hub/ui/_graph.py`**
  - Rewrite `rGraph()`: `rGraphDashboard()` → `rGraphContextPanels()` → `rGraphControlsStack()` → `graph-wrap` → legend/hint; delete inline `graph-tabs` / `graph-toolbar` / `rGraphPipeline()` and the Provenance graph `.section` between panels and controls.
  - `rGraphContextPanels()`: `rGraphPipeline()` then `rDashUntracked()` inside `.graph-context-panels`.
  - `rGraphControlsStack()`: `rDashMissFilters()` + layer tabs + zoom toolbar inside `.graph-controls-stack`.

- **`repo_scan/hub/ui/_graph_dashboard.py`**
  - Remove `rDashMissFilters()` and `rDashUntracked()` from `rGraphDashboard()`; Vault audit = summary, matrix, histogram, thin-links, trend only.
  - In `rDashSummary()`, add clickable affordance (anchor/`onclick`) scrolling or opening untracked `<details>` when count &gt; 0.

- **`repo_scan/hub/ui/_css.py`**
  - `.graph-controls-stack` (single bordered card, column flex, `gap: 4–6px`, `margin-bottom: 8px`).
  - Zero `margin-bottom` on `.dash-filters`, `.graph-tabs`, `.graph-toolbar` when nested in stack.
  - `.graph-context-panels` (`margin-bottom: 12px`).

- **`tests/test_hub_ui.py`** — DOM-order via `DASHBOARD_HTML` composed sources (see Tests); bump `_DASHBOARD_HTML_SHA256`.

- **`docs/research/decisions.md`** — **update in-place** the existing 2026-06-10 21:26 UTC approved row (no duplicate).

## Tests

| Acceptance criterion | Automated test |
|---|---|
| No section divider between controls and canvas | **`test_graph_controls_stack_contiguous`** — in `rGraph()` source, assert call order `rGraphControlsStack` before `graph-wrap`; assert no `Provenance graph` `.section` between `rGraphContextPanels` and `rGraphControlsStack` or between stack and canvas. |
| Stack rows adjacent in markup | **`test_graph_controls_stack_markup`** — slice `rGraphControlsStack()` body from `DASHBOARD_HTML`; assert substring order `dash-filters` (or stack open when empty) → `graph-tabs` → `graph-toolbar`. |
| Context above controls | **`test_graph_context_panels_above_controls`** — slice `rGraph()` for call order `rGraphContextPanels` before `rGraphControlsStack`; in `rGraphContextPanels()` body assert `agentic-loop-host` before `Untracked code`. |
| CSS stack contract | **`test_graph_controls_stack_css`** — `.graph-controls-stack` rule exists; nested row margins zeroed; column gap set. |
| Regression / live refresh | **`test_dashboard_html_byte_parity`**, **`test_dashboard_has_mermaid_agentic_loop`** — unchanged intent; bump SHA256. |

Manual UAT: matrix cell → filter chip → highlights; layer tab → reshape; +/− during live run → loop banner updates.

## Documentation

- **`docs/architecture/graph-viewer-roadmap.md`** — Phase-2 layout: context-panels → controls-stack → canvas.
- **`_graph.py` / `_graph_dashboard.py` docstrings** — render-order contract and audit vs control ownership.
- **`.cursor/rules/dashboard-ground-truth.mdc`** — add `rGraphControlsStack()` / `.graph-controls-stack` to surfaces table.

## Risks

- **Scroll distance**: tall loop on small viewports — optional compact/collapsed loop follow-up.
- **Re-render flash**: `setGraphMissFilter()` sets `innerHTML=rGraph()` then `mountGraph()` re-fetches `API_GRAPH` and calls `rGraph()` again — verify scroll/Mermaid stability beyond `_lastMermaidSrc`; consider skipping redundant `mountGraph()` fetch when `graphData` already loaded (optional micro-fix).
- **Loop banner**: context wrapper must not break `.loop-card>div:first-of-type` selector.
- **Empty filter row**: tabs + toolbar only when no orphans — acceptable.
- **SHA256 brittleness**: expected on whitespace changes.

## Out of scope

- Canvas rendering, force layout, Cytoscape migration.
- Roving keyboard focus / single Tab-stop toolbar behavior.
- Moving thin-links / trend out of Vault audit.
- Partial DOM patch for `setGraphMissFilter()`.
- Obsidian graph view, CDN Mermaid.
- Dashboard-only metrics without `scan.json` / `vault_health` backing.
- Re-scoping “pancake graph” if ticket author meant a control other than `graph-tabs`.

## Audit

> [!warning] Audit verdict: revise
> The spec correctly diagnoses current `rGraph()` interleaving and proposes a coherent target order aligned with the codebase, but it needs tighter wording, CSS margin details, poll/re-render risks, and traceability to research before human review.
> - Changes section says to delete inline `rGraphPipeline()` but Approach relocates it into `rGraphContextPanels()` — contradictory wording that will confuse implementers.
> - Analysis recommends `role="toolbar"` (APG); spec switches to `role="group"` without documenting that intentional deviation from the cited best-practice source.
> - Ticket asks to research best practices in the spec; rationale/citations live only in the sibling analysis doc, not in the spec body — the spec itself does not trace layout decisions to evidence.
> - `rDashSummary()` click-to-untracked affordance is specified but no stable target (`id` on the untracked `<details>`) or helper (e.g. `openUntrackedPanel()`) is defined, and no test covers it.
> - CSS changes omit nested `.loop-card` / `.dash-panel` margins inside `.graph-context-panels`, risking double vertical gap before the controls stack despite the contiguous-stack goal.
> - Missing risk: signal-matrix cells stay in Vault audit while filter chips move below context panels, increasing scroll distance for matrix → filter feedback (inverse of the summary/untracked association risk already listed).
> - Under-scoped risk: `render()` dashboard fast-path (`graphData` set) already calls `mountGraph()`, which re-fetches `API_GRAPH` and sets `innerHTML=rGraph()` on every poll — layout churn/Mermaid flash is wider than `setGraphMissFilter()` alone.
> - `decisions.md` in-place row mutation can erase audit history; process should say append vs amend explicitly.
> - `test_graph_controls_stack_contiguous` substring guard on `Provenance graph` is brittle and conflicts with Goal option to relocate that heading above context panels (still valid per spec).
> - Scope beyond ticket AC (summary affordance, `.cursor/rules` table row, roadmap edit) is reasonable but should be labeled compensating UX / ground-truth sync, not implied as required by the single AC checkbox.

## Provenance

- analysis: [[2026-06-10-move-the-agentic-loop-graph-and-untracke-analysis]]
