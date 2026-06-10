---
type: "research-run"
question: "Refactor repo_scan/writers.py (CC 52, 7 commits, untested). `repo_scan/writers.py` is both high-churn (7 commits) and high-complexity (total CC 52) with no matching test file. Research current best practices and draft a spec for this work."
sources: ["url-refactoring-com-catalog-extractfunction-html"]
run_at: "2026-06-10 01:54 UTC"
---

# Research run — Refactor repo_scan/writers.py (CC 52, 7 commits, untested). `repo_scan/writers.py` is both high-churn (7 commits) and high-complexity (total CC 52) with no matching test file. Research current best practices and draft a spec for this work.
_Run 2026-06-10 01:54 UTC_

**Strategy:** Strategy: characterize all write_* artifacts first (syrupy already ingested), then apply Extract Function to the two D-rank assemblers while keeping thin I/O wrappers stable for scanner.py. pytest-json-report fills the gap left by pytest-html on JSON sidecar design; Fowler sources anchor the spec's phased refactor rationale.

## Ingested

- [[sources/url-refactoring-com-catalog-extractfunction-html\|Extract Function]] — Documents Extract Function—the primary mechanical refactor for splitting write_health_report and write_index out of D-rank CC territory.

## Failed

- `url:https://martinfowler.com/bliki/CharacterizationTest.html` — fetch failed for https://martinfowler.com/bliki/CharacterizationTest.html: HTTP Error 404: Not Found
- `github:numirias/pytest-json-report` — fetch failed for https://api.github.com/repos/numirias/pytest-json-report: <urlopen error _ssl.c:990: The handshake operation timed out>
