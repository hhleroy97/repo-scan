---
id: "url-refactoring-com-catalog-movefunction-html"
type: "url"
url: "https://refactoring.com/catalog/moveFunction.html"
raw_url: "https://refactoring.com/catalog/moveFunction.html"
tags: ["article", "code-organization", "coupling", "encapsulation", "martin-fowler", "move-function", "move-method", "object-oriented-design", "refactoring"]
linked_files: []
relevance: "Useful when repo-scan modules grow misplaced helpers or methods that reach into other components—relocate those functions to the owning module (hub, radar, telemetry, etc.) to simplify dependencies and make the architecture easier to scan and maintain."
ingested_at: "2026-06-10 18:49 UTC"
---

# Move Function

## Summary

This is Martin Fowler’s Refactoring catalog entry for Move Function (alias Move Method) on refactoring.com. It describes relocating a function to the class or module whose data and behavior it depends on most, using the classic overdraftCharge example moved from Account to AccountType. The pattern matters because it keeps related logic together, improves encapsulation, and reduces awkward cross-object coupling.

## Key claims

- Move a function when it references elements in other contexts more than the one where it currently lives.
- Place behavior with the type that has the most knowledge about that behavior (e.g., overdraft charging belongs on AccountType, not Account).
- The refactor typically copies the function to the target, adapts it to the new context, then replaces the original with a delegation (or inlines the call).
- Moving features improves cohesion, clarifies responsibilities, and lowers coupling between classes.
- Also documented under the alias Move Method in Fowler’s catalog.

## Notes

_yours to annotate_
