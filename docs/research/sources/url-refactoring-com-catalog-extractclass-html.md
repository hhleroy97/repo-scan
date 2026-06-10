---
id: "url-refactoring-com-catalog-extractclass-html"
type: "url"
url: "https://refactoring.com/catalog/extractClass.html"
raw_url: "https://refactoring.com/catalog/extractClass.html"
tags: ["article", "class-design", "cohesion", "delegation", "extract-class", "inline-class", "martin-fowler", "refactoring", "single-responsibility"]
linked_files: ["repo_scan/writers.py"]
relevance: "Useful when scan or hub modules accumulate unrelated state and accessors—such as telemetry, progress, and UI concerns on one type—so cohesive sub-concepts can be split into smaller classes without changing outward behavior."
ingested_at: "2026-06-10 18:27 UTC"
---

# Extract Class

## Summary

This source documents the Extract Class refactoring from Martin Fowler's catalog: move a cohesive subset of fields and accessors from one class into a new class, then have the original class hold or delegate to that object. The example extracts office area code and number from Person into TelephoneNumber. It is the inverse of Inline Class and improves cohesion by grouping data and behavior that belong together.

## Key claims

- Extract Class moves related fields and methods from an overloaded class into a new, focused class.
- The original class typically keeps a reference to the extracted object and may delegate accessors (e.g., Person delegates to TelephoneNumber for area code and number).
- Fields that change together or represent a distinct concept are strong candidates for extraction.
- Extract Class is explicitly the inverse of Inline Class—one splits a class apart; the other merges a class back in.
- The refactoring preserves behavior while reducing class size and clarifying responsibilities.

## Notes

_yours to annotate_
