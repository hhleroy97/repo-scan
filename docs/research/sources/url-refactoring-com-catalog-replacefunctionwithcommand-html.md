---
id: "url-refactoring-com-catalog-replacefunctionwithcommand-html"
type: "url"
url: "https://refactoring.com/catalog/replaceFunctionWithCommand.html"
raw_url: "https://refactoring.com/catalog/replaceFunctionWithCommand.html"
tags: ["article", "code-organization", "command-pattern", "design-patterns", "extract-class", "method-object", "refactoring"]
linked_files: ["repo_scan/radar/pipeline.py"]
relevance: "Use this when a project has grown complex procedural code—scoring, parsing, or pipeline steps with many locals—and you want clearer structure, easier unit testing, or room to split logic across smaller methods without passing large parameter lists."
ingested_at: "2026-06-10 07:41 UTC"
---

# Replace Function with Command

## Summary

This source documents the Replace Function with Command refactoring (also called Replace Method with Method Object), the inverse of Replace Command with Function. It shows turning a long standalone function with multiple parameters and local state into a class that stores inputs on construction and runs the logic in an execute method. The pattern matters when a function has grown too large or stateful to stay readable as a single procedure.

## Key claims

- A long function with many parameters and local variables can be refactored into a class that holds those values as instance fields.
- The original function body moves into an execute (or similarly named) method on the new object.
- This refactoring is the inverse of Replace Command with Function: it expands a procedure into a command/method object rather than collapsing one into a function.
- The pattern is also known as Replace Method with Method Object when applied to class methods.
- Encapsulating parameters and intermediate state in an object can make complex logic easier to decompose, test, and extend.

## Notes

_yours to annotate_
