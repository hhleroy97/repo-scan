---
id: "url-realpython-com-python-all-attribute"
type: "url"
url: "https://realpython.com/python-all-attribute/"
raw_url: "https://realpython.com/python-all-attribute/"
tags: ["api-design", "article", "dunder-all", "imports", "modules", "naming-conventions", "packages", "pep-8", "public-api", "python", "wildcard-imports"]
linked_files: []
relevance: "Informs how repo-scan should define and document the public surface of its `repo_scan` package—using `__all__` in `__init__.py` files and avoiding star-imports—to keep import graphs analyzable and module boundaries explicit when scanning Python projects."
ingested_at: "2026-06-10 18:49 UTC"
---

# Python's __all__: Packages, Modules, and Wildcard Imports – Real Python

## Summary

Real Python tutorial on Python wildcard imports (`from module import *`) and the `__all__` attribute for controlling public APIs in modules and packages. It explains explicit vs wildcard imports, PEP 8 guidance against star-imports, underscore naming for non-public symbols, and how package `__init__.py` must define `__all__` for wildcard imports to expose anything.

## Key claims

- Wildcard imports (`from module import *`) import all public names from a module into the current namespace in one statement.
- PEP 8 discourages wildcard imports because they obscure which names are in scope and confuse readers and static tools; a defensible exception is republishing an internal interface as a public API.
- Names with a leading underscore are treated as non-public and are excluded from wildcard imports.
- For packages, `from package import *` does nothing unless `__init__.py` defines `__all__`; when present, only the names listed in `__all__` are imported.
- Python uses `__all__` on packages to avoid expensive filesystem scans and unintended import side effects from loading every submodule.
- `__all__` is a list of strings naming variables, functions, classes, or modules to expose to wildcard imports.
- Explicit imports (`import module`, `from module import name`) are preferred in production code because they make dependencies clear and reduce namespace clutter.

## Notes

_yours to annotate_
