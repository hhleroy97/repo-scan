---
id: "gh-pytest-dev-pytest"
type: "github"
url: "https://github.com/pytest-dev/pytest"
raw_url: "https://github.com/pytest-dev/pytest"
tags: ["fixtures", "parametrization", "plugins", "python", "repo", "test-discovery", "test-runner", "testing", "unit-testing"]
linked_files: []
relevance: "repo-scan already depends on pytest>=8 as its primary test harness in dev dependencies and CI, so pytest is the core platform for unit tests, snapshot characterization via syrupy, and future test tooling such as HTML or metadata reporting plugins."
ingested_at: "2026-06-10 04:02 UTC"
---

# pytest-dev/pytest — The pytest framework makes it easy to write small tests, yet scales to support…

## Summary

pytest-dev/pytest is the dominant Python testing framework, with a large open-source community (roughly 14k GitHub stars) and broad adoption across the ecosystem. It emphasizes simple test functions and plain assert statements while scaling to large suites through fixtures, parametrization, markers, and a rich plugin architecture. For repo-scan and similar Python projects, it is the foundational test runner that plugins such as syrupy and pytest-html build on.

## Key claims

- pytest is designed to make small tests easy to write while scaling to complex integration and end-to-end suites
- Tests use plain assert statements with detailed failure introspection instead of many custom assertion APIs
- A fixture system provides reusable setup, teardown, and dependency injection across tests and modules
- Automatic test discovery finds test files and functions following conventional naming patterns
- Parametrization, markers, and skip/xfail controls support matrix testing and selective execution
- An extensible hook and plugin system lets tools integrate reporting, snapshots, coverage, and CI workflows
- The project is actively maintained under pytest-dev with strong community adoption (roughly 14k stars, 3k forks)

## Notes

_yours to annotate_
