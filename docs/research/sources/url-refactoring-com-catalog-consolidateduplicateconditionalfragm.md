---
id: "url-refactoring-com-catalog-consolidateduplicateconditionalfragm"
type: "url"
url: "https://refactoring.com/catalog/consolidateDuplicateConditionalFragments.html"
raw_url: "https://refactoring.com/catalog/consolidateDuplicateConditionalFragments.html"
tags: ["article", "clean-code", "conditionals", "consolidate-duplicate-conditio", "control-flow", "deduplication", "readability", "refactoring", "slide-statements"]
linked_files: ["repo_scan/scanner.py"]
relevance: "Use this when scan or analysis code repeats the same setup or calculations in multiple if/else branches—reorder or slide shared statements first, then consolidate them to simplify control flow and reduce drift between branches."
ingested_at: "2026-06-10 13:15 UTC"
---

# Slide Statements

## Summary

This source documents the Slide Statements refactoring from Martin Fowler's catalog: reorder or relocate statements so duplicated logic inside conditional branches lines up and can be merged. The example shows moving `chargePerUnit` assignment earlier, after `retrievePricingPlan()` and before `retrieveOrder()`. It is a preparatory step for Consolidate Duplicate Conditional Fragments, reducing duplication without changing behavior.

## Key claims

- Duplicate code in both branches of a conditional is a maintainability smell that should be removed.
- Slide Statements reorders or moves statements so identical fragments in conditional branches become adjacent or can be lifted out.
- The technique is often used as a setup step before Consolidate Duplicate Conditional Fragments.
- Statement order can be adjusted when dependencies allow (e.g., assign `chargePerUnit` from `pricingPlan` before other work).
- The refactoring preserves behavior while making later consolidation and readability improvements easier.

## Notes

_yours to annotate_
