---
type: "research-run"
question: "Refactor repo_scan/radar/sources.py (CC 14, 3 commits, untested). `repo_scan/radar/sources.py` is both high-churn (3 commits) and high-complexity (total CC 14) with no matching test file. Acceptance criteria: Complexity of every function below rank C; Test file exists and passes; Trend delta confirms complexity drop. Research current best practices and draft a spec for this work."
sources: ["url-refactoring-com-catalog-splitloop-html"]
run_at: "2026-06-10 07:32 UTC"
---

# Research run — Refactor repo_scan/radar/sources.py (CC 14, 3 commits, untested). `repo_scan/radar/sources.py` is both high-churn (3 commits) and high-complexity (total CC 14) with no matching test file. Acceptance criteria: Complexity of every function below rank C; Test file exists and passes; Trend delta confirms complexity drop. Research current best practices and draft a spec for this work.
_Run 2026-06-10 07:32 UTC_

**Strategy:** All file CC 14 is isolated to `rebuild_research_index`; other functions are already rank A/B, and partial coverage lives in `tests/test_radar_ingest.py`—so the spec should follow the repo's snapshot-then-Split-Loop/Extract-Function precedent, split a matching test module, then verify with radon and a self-scan trend delta.

## Ingested

- [[sources/url-refactoring-com-catalog-splitloop-html\|Split Loop]] — Documents Split Loop—the right complement to already-ingested Extract Function—for decomposing `rebuild_research_index`'s nested collect/sort/table and tag-map loops into pure helpers without changing markdown output.

## Failed

- `github:radon-dev/radon` — fetch failed for https://api.github.com/repos/radon-dev/radon: HTTP Error 404: Not Found
- `url:https://martinfowler.com/bliki/CharacterizationTest.html` — fetch failed for https://martinfowler.com/bliki/CharacterizationTest.html: HTTP Error 404: Not Found
