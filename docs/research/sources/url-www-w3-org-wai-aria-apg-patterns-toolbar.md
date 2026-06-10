---
id: "url-www-w3-org-wai-aria-apg-patterns-toolbar"
type: "url"
url: "https://www.w3.org/WAI/ARIA/apg/patterns/toolbar/"
raw_url: "https://www.w3.org/WAI/ARIA/apg/patterns/toolbar/"
tags: ["accessibility", "article", "focus-management", "keyboard-navigation", "roving-tabindex", "screen-readers", "toolbar", "ui-patterns", "wai-aria"]
linked_files: []
relevance: "Applies when building grouped action bars or editor toolbars in the hub UI so controls are accessible, use a single tab stop with arrow-key traversal, and follow correct ARIA roles, labels, and orientation."
ingested_at: "2026-06-10 21:08 UTC"
---

# Toolbar Pattern

## Summary

This source documents the WAI-ARIA toolbar pattern: a container role for grouping related controls (buttons, menubuttons, checkboxes) so screen readers understand the grouping and keyboard users encounter fewer tab stops. It specifies roving-focus keyboard interaction (Tab enters/exits; arrow keys move within), orientation rules, and when toolbars are appropriate.

## Key claims

- Use role="toolbar" on the container to communicate grouped controls to assistive technologies.
- Optimize keyboard UX with one Tab stop per toolbar and arrow-key navigation among controls (roving tabindex).
- In horizontal toolbars, Left/Right Arrow navigate; Up/Down may mirror navigation or operate controls like spin buttons.
- In vertical toolbars, Up/Down Arrow navigate; Left/Right may mirror navigation or operate controls like sliders.
- Avoid controls that need the same arrow keys used for toolbar navigation; if unavoidable, include only one such control and place it last.
- Use toolbar grouping only when the group contains three or more controls.
- On Tab into the toolbar, focus the first non-disabled control, or optionally restore the last focused control.
- Label toolbars with aria-labelledby (visible label) or aria-label; set aria-orientation="vertical" when arranged vertically.

## Notes

_yours to annotate_
