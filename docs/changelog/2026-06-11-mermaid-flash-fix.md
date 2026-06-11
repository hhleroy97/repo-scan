---
type: changelog
date: 2026-06-11
tags:
  - changelog
  - hub
linked_files: ["[[repo_scan/hub/ui/_graph_loop.py]]", "[[repo_scan/hub/ui/_runtime.py]]"]
---
# Mermaid diagram flash fix

**Date:** 2026-06-11

## Problem

Every poll cycle (3–12 s), `refresh()` → `render()` replaced the entire
`#main` innerHTML, destroying the rendered Mermaid SVG and showing a
spinner while re-rendering from scratch — visible as a full-page flash.

## Fix

1. **Mermaid render cache** — `_lastMermaidSrc` / `_lastMermaidSvg` in
   `_graph_loop.py`. If the source hasn't changed, the cached SVG is
   injected directly without calling `mermaid.render()`.
2. **Skip full DOM rebuild on poll** — `render()` in `_runtime.py` now
   updates just the live banner and calls `mountGraph()` without nuking
   `#main` when graph data already exists.
3. **Banner-only update** — `_updateLoopBanner()` replaces the status
   text inside the loop card, keeping the SVG untouched.
