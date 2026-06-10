---
id: "gh-syrupy-project-syrupy"
type: "github"
url: "https://github.com/syrupy-project/syrupy"
raw_url: "https://github.com/syrupy-project/syrupy"
tags: ["cli", "pytest", "python", "regression-testing", "repo", "serialization", "snapshot-testing", "syrupy", "test-fixtures", "testing"]
linked_files: []
relevance: "Useful for repo-scan or similar Python projects that want maintainable regression tests over structured outputs (reports, scan results, LLM responses) without hand-writing large expected-value assertions."
ingested_at: "2026-06-10 01:50 UTC"
---

# syrupy-project/syrupy — :pancakes: The sweeter pytest snapshot plugin

## Summary

Syrupy is a zero-dependency pytest snapshot plugin for asserting that computed test outputs stay unchanged over time. It uses idiomatic `assert actual == snapshot` syntax, stores snapshots in `__snapshots__` directories, and fails tests when snapshots are missing—not only when they differ. The plugin is extensible via serializers, matchers, include/exclude filters, and multiple CLI flags for updating, diffing, and managing unused snapshots.

## Key claims

- Syrupy is a zero-dependency pytest plugin for snapshot testing with idiomatic `assert x == snapshot` assertions
- Missing snapshots fail the test suite by default, unlike some other snapshot libraries that only fail on mismatches
- Snapshots are stored under `__snapshots__` (configurable via `--snapshot-dirname`) and should be committed with test code
- New snapshots are created with `pytest --snapshot-update`; `--snapshot-update-new-only` writes only missing snapshots without modifying existing ones
- Current Syrupy 5.x requires Python >=3.10 and pytest >=8
- The default serializer supports built-in Python types and custom objects via `__repr__`, with AmberDataSerializer helpers for alternate representations
- Per-assertion options include `matcher`, `include`, and `exclude` filters; matchers can be composed with `compose_matchers` and built-in helpers like `path_type`
- The `snapshot` fixture is not directly usable in `unittest.TestCase` subclasses; workarounds use pytest fixtures or `@pytest.mark.usefixtures`

## Notes

_yours to annotate_
