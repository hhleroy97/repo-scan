---
id: "url-peps-python-org-pep-0589"
type: "url"
url: "https://peps.python.org/pep-0589/"
raw_url: "https://peps.python.org/pep-0589/"
tags: ["article", "json", "pep", "pep-589", "python", "standards-track", "static-analysis", "structured-data", "type-hints", "typeddict", "typing"]
linked_files: []
relevance: "repo-scan can use TypedDict to type-check JSON-shaped scan outputs, radar payloads, and LLM response dicts without dataclass overhead, giving precise per-key typing for parsers and report writers while keeping runtime values as plain dicts."
ingested_at: "2026-06-10 17:14 UTC"
---

# PEP 589 – TypedDict: Type Hints for Dictionaries with a Fixed Set of Keys | peps.python.org

## Summary

PEP 589 (Final, Python 3.8) introduces typing.TypedDict for annotating dictionaries with a fixed set of string keys, each with a specific value type—addressing a gap in PEP 484's Dict[K, V] for JSON-like and structured data. TypedDict supports class-based and assignment-based syntax, inheritance, and totality (required vs optional keys). At runtime TypedDict values are plain dicts; type checkers enforce key/value compatibility structurally, but isinstance() is not supported.

## Key claims

- Dict[str, Any] and Dict[str, Union[...]] are too permissive for dictionaries where each key has a distinct value type
- TypedDict represents dict objects with specific string keys and per-key value types, with keys required by default (total=True)
- Class-based syntax uses TypedDict as the sole base class with key: type annotations and no initializers or methods
- total=False makes all keys in that class body optional; inherited keys keep the totality of their defining TypedDict
- TypedDict types use structural compatibility: a more specific TypedDict is compatible with a more general one
- TypedDict supports inheritance and multiple inheritance, but cannot override parent field types or merge conflicting field types
- At runtime TypedDict is not a real class: values are dict, callable as Movie(name='...', year=...), and isinstance(d, Movie) is not supported
- Alternative assignment syntax TypedDict('Name', {...}) exists for backporting but does not support inheritance or mixed required/optional fields

## Notes

_yours to annotate_
