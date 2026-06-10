---
id: "url-docs-python-org-3-tutorial-modules-html-packages"
type: "url"
url: "https://docs.python.org/3/tutorial/modules.html#packages"
raw_url: "https://docs.python.org/3/tutorial/modules.html#packages"
tags: ["article", "bytecode-cache", "cpython", "imports", "language-fundamentals", "main-guard", "modules", "namespaces", "python", "standard-library", "sys-path"]
linked_files: []
relevance: "Directly informs how repo-scan should structure its `repo_scan` package, organize imports between hub, radar, and analysis modules, and reason about import side effects, reload behavior, and module discovery when scanning Python projects."
ingested_at: "2026-06-10 18:27 UTC"
---

# 6. Modules

## Summary

Official Python tutorial section on modules: how to split code into reusable `.py` files, import them into scripts or the REPL, and control what names enter the namespace. It covers import variants, module initialization, the `__name__ == "__main__"` script pattern, `sys.path` search order, bytecode caching in `__pycache__`, standard library modules, and the `dir()` introspection helper.

## Key claims

- A module is a `.py` file whose definitions can be imported into other modules or the main script namespace.
- `import mod` adds only the module name to the current namespace; members are accessed as `mod.item`, and `mod.__name__` is the module's string name.
- Module-level executable statements run once on first import (and again when the file is run as a script) to initialize the module.
- Each module has its own global namespace, so module globals do not clash with the importer's globals unless explicitly accessed.
- `from mod import name` and `from mod import *` pull names into the importer's namespace; star-import skips leading-underscore names and is discouraged outside interactive use.
- `import mod as alias` and `from mod import name as alias` rename bindings without changing import semantics.
- Each module is imported at most once per interpreter session; after editing a module, restart the interpreter or call `importlib.reload()`.
- Running `python mod.py` sets `__name__` to `"__main__"`, enabling dual-purpose modules via `if __name__ == "__main__":`.

## Notes

_yours to annotate_
