---
id: "url-refactoring-com-catalog-extractfunction-html"
type: "url"
url: "https://refactoring.com/catalog/extractFunction.html"
raw_url: "https://refactoring.com/catalog/extractFunction.html"
tags: ["article", "code-readability", "extract-function", "extract-method", "inline-function", "martin-fowler", "refactoring", "separation-of-concerns"]
linked_files: []
relevance: "Useful when breaking up long or high-complexity functions in the codebase — such as large writer or radar modules — into smaller, testable helpers without changing behavior."
ingested_at: "2026-06-10 01:53 UTC"
---

# Extract Function

## Summary

This source documents the Extract Function refactoring (also called Extract Method), a technique for improving code clarity by moving a cohesive block of logic out of a larger function into a well-named helper. The before/after example shows detail-printing console.log calls lifted into a printDetails function inside printOwing. It is explicitly described as the inverse of Inline Function.

## Key claims

- Extract Function isolates a logical fragment from a parent function into a separate, named function
- Giving extracted code a descriptive name communicates intent better than inline comments or anonymous blocks
- The technique is the inverse of Inline Function — one moves code out; the other folds a helper back in
- Extract Method is an alias for Extract Function, especially in object-oriented contexts
- Extracted helpers can close over variables from the enclosing scope (e.g., invoice) while taking explicit parameters for values they operate on (e.g., outstanding)

## Notes

_yours to annotate_
