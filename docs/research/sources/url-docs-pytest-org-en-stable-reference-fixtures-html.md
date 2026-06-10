---
id: "url-docs-pytest-org-en-stable-reference-fixtures-html"
type: "url"
url: "https://docs.pytest.org/en/stable/reference/fixtures.html"
raw_url: "https://docs.pytest.org/en/stable/reference/fixtures.html"
tags: ["article", "conftest", "dependency-injection", "execution-order", "fixtures", "monkeypatch", "plugin-fixtures", "pytest", "test-isolation", "test-scoping", "tmp-path"]
linked_files: ["tests/conftest.py"]
relevance: "Useful when designing or refactoring test suites—especially shared fixtures in conftest.py, session-scoped setup, and ensuring deterministic fixture order for integration or hub/UI tests in this project."
ingested_at: "2026-06-10 21:10 UTC"
---

# Fixtures reference¶

## Summary

Official pytest documentation on fixtures: built-in fixtures (capfd, monkeypatch, tmp_path, etc.), how fixture availability and discovery work from the test's perspective, sharing via conftest.py, and third-party plugin fixtures. It explains that fixture execution order is determined only by scope, dependency graph, and autouse—not by definition order or names—and that ambiguous dependency graphs can yield non-deterministic ordering.

## Key claims

- Fixtures are defined with @pytest.fixture; pytest provides many built-in fixtures for capture, logging, monkeypatching, temp paths, warnings, and configuration.
- Fixture availability is determined from the test's perspective: tests can only request fixtures in their scope, but fixtures can request other fixtures across scopes as long as the test can see all involved fixtures.
- conftest.py shares fixtures across a directory; nested conftest files add fixtures, tests search upward through scopes but never downward, and nearer overrides win.
- Third-party plugin fixtures are discovered last, after searching local scopes from the test outward.
- Fixture instantiation order depends on three factors only: scope (higher scopes first), dependencies (requested fixtures run first), and autouse—not on names, file location, or definition order.
- Ambiguous dependency graphs (e.g., a fixture with no unique position in the chain) can produce undefined ordering; explicit dependencies are required when order affects test behavior.
- pytest --fixtures lists available fixtures for a test or scope; underscore-prefixed fixtures require -v.

## Notes

_yours to annotate_
