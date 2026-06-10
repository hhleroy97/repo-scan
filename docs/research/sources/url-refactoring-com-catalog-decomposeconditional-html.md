---
id: "url-refactoring-com-catalog-decomposeconditional-html"
type: "url"
url: "https://refactoring.com/catalog/decomposeConditional.html"
raw_url: "https://refactoring.com/catalog/decomposeConditional.html"
tags: ["article", "clean-code", "conditionals", "decompose-conditional", "extract-method", "readability", "refactoring", "self-documenting-code"]
linked_files: []
relevance: "Use this when scan or analysis code accumulates nested if/else rules (pricing, eligibility, date windows, policy checks) so you can replace opaque boolean expressions with named predicates and branch helpers that are easier to test, reuse, and explain."
ingested_at: "2026-06-10 13:14 UTC"
---

# Decompose Conditional

## Summary

This source illustrates the "Decompose Conditional" refactoring: replace a hard-to-read compound conditional and its branches with small, well-named functions. The before example uses negated date-range checks and inline arithmetic; the after version reads as intent (`summer()`, `summerCharge()`, `regularCharge()`). It matters because it turns low-level logic into self-documenting structure without changing behavior.

## Key claims

- Complex conditionals with multiple negations and inline calculations are difficult to read and reason about.
- A conditional can be decomposed by extracting the condition into a predicate function (e.g., `summer()`).
- Each branch of an if/else can be extracted into its own function (e.g., `summerCharge()`, `regularCharge()`).
- After decomposition, control flow expresses business intent at a higher level of abstraction.
- The refactoring preserves behavior while improving readability and maintainability.

## Notes

_yours to annotate_
