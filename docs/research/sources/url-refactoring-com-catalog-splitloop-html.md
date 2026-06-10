---
id: "url-refactoring-com-catalog-splitloop-html"
type: "url"
url: "https://refactoring.com/catalog/splitLoop.html"
raw_url: "https://refactoring.com/catalog/splitLoop.html"
tags: ["aggregation", "article", "code-readability", "loop-optimization", "martin-fowler", "performance-tradeoff", "refactoring", "separation-of-concerns", "split-loop"]
linked_files: []
relevance: "Useful when repo-scan pipeline or radar code mixes unrelated per-item work in one loop—split or combine loops deliberately to balance clarity and single-pass efficiency."
ingested_at: "2026-06-10 07:32 UTC"
---

# Split Loop

## Summary

Split Loop is a refactoring pattern for when one loop aggregates several independent values over the same collection. The example contrasts a single pass that updates both averageAge and totalSalary with two separate loops, each focused on one metric. Splitting can clarify intent and make later extractions easier, at the cost of extra iterations over the data.

## Key claims

- One loop can compute multiple independent aggregates (e.g., sum of ages and sum of salaries) in a single pass over the collection
- Split Loop separates a multi-purpose loop into distinct loops, each responsible for one calculation
- After splitting, each loop is easier to read, name, and refactor further (e.g., into its own function)
- Splitting trades performance (multiple traversals) for separation of concerns and maintainability
- Average age still requires a final division by collection length after the age-summing loop completes

## Notes

_yours to annotate_
