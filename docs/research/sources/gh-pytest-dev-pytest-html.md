---
id: "gh-pytest-dev-pytest-html"
type: "github"
url: "https://github.com/pytest-dev/pytest-html"
raw_url: "https://github.com/pytest-dev/pytest-html"
tags: ["ci-artifacts", "html", "pytest", "pytest-plugin", "python", "repo", "reporting", "test-results", "testing"]
linked_files: ["tests/conftest.py"]
relevance: "For repo-scan or similar pytest-based projects, pytest-html offers a ready-made way to publish human-readable test run artifacts alongside existing markdown scan reports in CI or local workflows."
ingested_at: "2026-06-10 01:50 UTC"
---

# pytest-dev/pytest-html — Plugin for generating HTML reports for pytest results

## Summary

pytest-html is an official pytest-dev plugin that turns pytest run results into browsable HTML reports. It is widely adopted (roughly 23M PyPI downloads per month), licensed under MPL-2.0, and integrates via standard pytest CLI flags and hooks. It matters as a low-friction way to share test outcomes with summaries, per-test detail, and optional styling without building a custom reporter.

## Key claims

- pytest-html is a pytest plugin whose primary interface is `pytest --html=report.html` to emit an HTML report of test results
- The `--self-contained-html` flag produces a single shareable HTML file by inlining CSS and other assets (external images may still be linked)
- Reports can stream incrementally via the `generate_report_on_test` ini option instead of waiting for the full suite to finish
- Appearance and content are customizable through pytest hooks (e.g. `pytest_html_report_title`, `pytest_html_results_summary`) and `--css` for custom stylesheets
- The Environment section is provided by the separate pytest-metadata plugin and can be modified via `pytest_configure` / `pytest_sessionfinish` hooks
- ANSI terminal output in reports depends on the optional ansi2html package, which is not bundled due to licensing
- Current release is 4.2.0 (Jan 2026); the GitHub repo has ~770 stars, ~254 forks, and active maintenance

## Notes

_yours to annotate_
