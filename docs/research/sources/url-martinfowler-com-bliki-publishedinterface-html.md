---
id: "url-martinfowler-com-bliki-publishedinterface-html"
type: "url"
url: "https://martinfowler.com/bliki/PublishedInterface.html"
raw_url: "https://martinfowler.com/bliki/PublishedInterface.html"
tags: ["api-design", "article", "backward-compatibility", "encapsulation", "interface-contract", "martin-fowler", "published-interface", "refactoring"]
linked_files: []
relevance: "When exposing types, endpoints, or libraries from this project, treat anything external consumers depend on as a published interface and plan versioning, deprecation, and breaking-change policies accordingly rather than assuming internal refactors are safe."
ingested_at: "2026-06-10 17:06 UTC"
---

# bliki: Published Interface

## Summary

Martin Fowler defines a Published Interface as a class interface consumed outside the codebase where it is defined—stricter than language-level visibility like public in Java or C#. He argues that distinguishing published from merely public interfaces matters more than public versus private, because unpublished interfaces can be refactored freely within one codebase while published ones impose compatibility obligations on external callers.

## Key claims

- A Published Interface is any interface used outside the codebase that defines it, not merely one marked public in the source language.
- The published-versus-public distinction is more consequential than the public-versus-private distinction for API design and maintenance.
- Interfaces used only within a single codebase can be changed and renamed easily with modern refactoring tools.
- Published interfaces require more careful, complicated treatment because you cannot update or reach all external calling code.

## Notes

_yours to annotate_
