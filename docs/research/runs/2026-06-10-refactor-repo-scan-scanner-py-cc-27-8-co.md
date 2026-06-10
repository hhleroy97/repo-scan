---
type: "research-run"
question: "Refactor repo_scan/scanner.py (CC 27, 8 commits, untested). `repo_scan/scanner.py` is both high-churn (8 commits) and high-complexity (total CC 27) with no matching test file. Research current best practices and draft a spec for this work."
sources: ["gh-ThoughtWorksInc-WorkingEffectivelyWithLegacyCode", "arxiv-2401.15298", "url-www-socratopia-app-library-software-engineering-craft-en-cha"]
run_at: "2026-06-10 03:15 UTC"
---

# Research run — Refactor repo_scan/scanner.py (CC 27, 8 commits, untested). `repo_scan/scanner.py` is both high-churn (8 commits) and high-complexity (total CC 27) with no matching test file. Research current best practices and draft a spec for this work.
_Run 2026-06-10 03:15 UTC_

**Strategy:** `scanner.py` is already partially guarded by integration tests in `test_scan.py` and writer snapshots, but its CC-27 `scan()` monolith lacks stage-level characterization; the spec should map extractions to existing `step()` boundaries, introduce a shared context object, and require one behavior-neutral extract commit per stage before any structural redesign.

## Ingested

- [[sources/gh-ThoughtWorksInc-WorkingEffectivelyWithLegacyCode\|ThoughtWorksInc/WorkingEffectivelyWithLegacyCode — GitHub repository]] — Canonical Feathers playbook for the legacy-code change algorithm—characterization tests, seams, and dependency-breaking—that directly addresses refactoring untested orchestration code like `scan()`.
- [[sources/arxiv-2401.15298\|Together We Go Further: LLMs and IDE Static Analysis for Extract Method Refactoring]] — Empirical extract-method research on decomposing long, multi-responsibility procedures into valid, behavior-preserving stage functions—the core mechanical refactor `scanner.py` needs.
- [[sources/url-www-socratopia-app-library-software-engineering-craft-en-cha\|Refactoring Under Test — The Safety Net Story | Software Engineering Craft]] — Practitioner guide to the bootstrap sequence (mechanical extract → characterize → substantive refactor) and commit discipline for keeping characterization tests as an unchanged oracle during refactors.
