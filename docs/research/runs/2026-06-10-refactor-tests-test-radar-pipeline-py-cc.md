---
type: "research-run"
question: "Refactor tests/test_radar_pipeline.py (CC 19, 4 commits, untested). `tests/test_radar_pipeline.py` is both high-churn (4 commits) and high-complexity (total CC 19) with no matching test file. Acceptance criteria: Complexity of every function below rank C; Test file exists and passes; Trend delta confirms complexity drop. Research current best practices and draft a spec for this work."
sources: ["gh-JetBrains-Research-PyNose", "arxiv-2409.16739"]
run_at: "2026-06-10 06:59 UTC"
---

# Research run — Refactor tests/test_radar_pipeline.py (CC 19, 4 commits, untested). `tests/test_radar_pipeline.py` is both high-churn (4 commits) and high-complexity (total CC 19) with no matching test file. Acceptance criteria: Complexity of every function below rank C; Test file exists and passes; Trend delta confirms complexity drop. Research current best practices and draft a spec for this work.
_Run 2026-06-10 06:59 UTC_

**Strategy:** Radon shows CC 19 is isolated to `test_loop_happy_path_auto_gates` (Assertion Roulette); the spec should extract artifact/provenance assertion helpers, consolidate shared fake-LLM fixtures already imported by `test_hub.py`, and gate completion on pytest green plus per-function rank ≤ C and scan trend delta.

## Ingested

- [[sources/gh-JetBrains-Research-PyNose\|JetBrains-Research/PyNose — A test smell detector for Python.]] — PyNose catalogs pytest-specific test smells (Assertion Roulette, Eager Test) that explain why `test_loop_happy_path_auto_gates` sits at rank C and what to extract.
- [[sources/arxiv-2409.16739\|Automated Unit Test Refactoring]] — UTRefactor documents systematic, behavior-preserving test refactoring via Extract Method and stepwise smell removal—directly applicable to lowering CC without weakening coverage.

## Failed

- `url:https://martinfowler.com/bliki/CharacterizationTest.html` — fetch failed for https://martinfowler.com/bliki/CharacterizationTest.html: HTTP Error 404: Not Found
