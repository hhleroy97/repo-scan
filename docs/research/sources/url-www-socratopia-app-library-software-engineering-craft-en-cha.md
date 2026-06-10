---
id: "url-www-socratopia-app-library-software-engineering-craft-en-cha"
type: "url"
url: "https://www.socratopia.app/library/software-engineering-craft-en/chapter-10"
raw_url: "https://www.socratopia.app/library/software-engineering-craft-en/chapter-10"
tags: ["ai-assisted-refactoring", "article", "behavior-preservation", "characterization-tests", "legacy-code", "mutation-testing", "refactoring", "safety-net", "technical-debt", "test-coverage", "test-then-refactor"]
linked_files: []
relevance: "For a codebase analysis project, this source supports flagging low-coverage, high-churn modules as refactor candidates and recommending characterization tests before structural changes to risky areas."
ingested_at: "2026-06-10 03:15 UTC"
---

# Refactoring Under Test — The Safety Net Story | Software Engineering Craft

## Summary

Chapter 10 from Software Engineering Craft on refactoring legacy code under test, centered on a case study where characterization tests were written before refactoring a 2,400-line OrderProcessor. It argues that tests are a prerequisite for safe refactoring—not a byproduct—and defines characterization tests, the test-then-refactor loop, and a bootstrap pattern for initially untestable code. It also covers AI-assisted refactoring workflows and the economics of investing in a safety net upfront.

## Key claims

- Good tests are a prerequisite for good refactoring, not a result of it; without tests, refactoring is a leap of faith.
- Refactoring under test means restructuring code while a test suite continuously verifies behavior is preserved; failing tests mean the refactor was not behavior-preserving.
- Characterization tests lock in what code currently does—without judging correctness—so refactoring can proceed safely and bugs can be filed separately.
- During characterization, resist fixing surprising behavior; mixing fixes into characterization turns the work into a risky rewrite.
- The legacy refactor loop is test-then-refactor: characterize, apply one refactoring, run tests, commit on green, and default to fixing the refactor when tests go red.
- Untestable code can be bootstrapped with small mechanical refactorings (rename, extract function) to expose surfaces, then characterization tests, then substantive refactors.
- AI can speed mechanical refactoring, but humans must own characterization tests, verify test runs, check that tests were not modified to pass, and review structural diffs.
- Passing tests alone do not guarantee a safe refactor; coverage, mutation testing, and human review are additional trust signals.

## Notes

_yours to annotate_
