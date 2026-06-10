---
id: "gh-JetBrains-Research-PyNose"
type: "github"
url: "https://github.com/JetBrains-Research/PyNose"
raw_url: "https://github.com/JetBrains-Research/PyNose"
tags: ["ide-plugin", "jetbrains", "kotlin", "pycharm", "pytest", "python", "quick-fix", "repo", "static-analysis", "test-smells", "testing", "unittest"]
linked_files: []
relevance: "repo-scan uses pytest as its test harness, so PyNose's pytest-aware inspections could guide test-quality improvements or inform future automated checks for common test anti-patterns in this project's suite."
ingested_at: "2026-06-10 06:58 UTC"
---

# JetBrains-Research/PyNose — A test smell detector for Python.

## Summary

PyNose is a JetBrains Research PyCharm plugin that detects Python test smells through IDE inspections. It adapts to the project's configured test runner (pytest or unittest) and flags issues such as assertion roulette, duplicate asserts, empty tests, and exception-handling anti-patterns. Several inspections include quick fixes, and the tool is under active development with an ASE2021 branch preserving the version described in the original paper.

## Key claims

- PyNose runs as a PyCharm plugin (targeting IDE version 2021.3) to analyze test smells in an opened Python project
- Inspection behavior depends on the configured default test runner, with separate rule sets for pytest and unittest
- Sixteen inspection types cover smells including assertion roulette, conditional test logic, duplicate/redundant assertions, empty tests, exception handling, magic numbers, sleepy tests, and lack of test cohesion
- Quick fixes are available for several smells (e.g., constructor initialization, duplicate assert, empty test, exception handling, redundant assertion, sleepy test, suboptimal assert)
- Some inspections are disabled by default and can be enabled in IDE settings; assertion roulette becomes a weak warning when enabled
- The ASE2021 branch preserves the older tool version described in the paper "PyNose: A Test Smell Detector For Python"
- Suboptimal assert detection references an external list of suboptimal assertion patterns (Zenodo record 5156098)

## Notes

_yours to annotate_
