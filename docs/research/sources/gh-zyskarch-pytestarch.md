---
id: "gh-zyskarch-pytestarch"
type: "github"
url: "https://github.com/zyskarch/pytestarch"
raw_url: "https://github.com/zyskarch/pytestarch"
tags: ["architecture-testing", "archunit-inspired", "dependency-rules", "import-analysis", "module-boundaries", "plantuml", "pytest", "pytestarch", "python", "repo", "static-analysis"]
linked_files: []
relevance: "Useful for repo-scan or similar projects that care about module layering and dependency hygiene, because it can turn import-graph constraints into automated pytest checks that fail CI when architectural boundaries are violated."
ingested_at: "2026-06-10 18:49 UTC"
---

# zyskarch/pytestarch — Test framework for software architecture based on imports between modules.

## Summary

PyTestArch is an open-source Python library for defining and testing architectural rules based on import relationships between modules, inspired by ArchUnit. It scans a project’s Python source, builds an evaluable dependency model, and lets you express constraints with a fluent Rule API that integrates with pytest. The project includes real architecture tests, optional dependency-graph visualization, and support for generating rules from PlantUML diagrams.

## Key claims

- PyTestArch tests software architecture by analyzing imports between Python modules and asserting rules against that graph
- Installation is via PyPI (`pip install pytestarch`), with optional visualization support via `pytestarch[visualization]`
- The workflow is three steps: build an evaluable architecture with `get_evaluable_architecture`, define a `Rule` with a fluent DSL, then call `rule.assert_applies(evaluable)`
- `get_evaluable_architecture` takes a project root (to distinguish internal vs external dependencies) and a source path to scan
- Rules can express constraints such as which modules may import which others, including submodule scoping and named-module targeting
- The library uses pytest fixtures (e.g. session-scoped) to reuse the evaluable architecture across multiple rule checks
- The project’s own `tests/test_architecture.py` enforces internal module boundaries as a reference implementation
- Further capabilities include generating rules from PlantUML diagrams and extensive integration test examples

## Notes

_yours to annotate_
