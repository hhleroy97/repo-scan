---
id: "gh-ThoughtWorksInc-WorkingEffectivelyWithLegacyCode"
type: "github"
url: "https://github.com/ThoughtWorksInc/WorkingEffectivelyWithLegacyCode"
raw_url: "https://github.com/ThoughtWorksInc/WorkingEffectivelyWithLegacyCode"
tags: ["characterization-tests", "dependency-breaking", "java", "legacy-code", "michael-feathers", "refactoring", "repo", "safe-change-algorithm", "seams", "technical-debt", "testability", "testing"]
linked_files: []
relevance: "For a codebase analysis or modernization project, this source provides a practical playbook for where to intervene, how to gain test coverage before risky edits, and which refactoring patterns to apply when dependencies block change."
ingested_at: "2026-06-10 03:14 UTC"
---

# ThoughtWorksInc/WorkingEffectivelyWithLegacyCode — GitHub repository

## Summary

Notes and examples from ThoughtWorks’ WorkingEffectivelyWithLegacyCode repository, distilling Michael Feathers’ approach to changing software safely when tests are missing. It defines legacy code as code without tests, outlines a repeatable change algorithm (identify change points, find test points, break dependencies, write tests, then refactor), and catalogs concrete techniques for introducing seams and characterization tests. The source matters because it turns legacy maintenance from ad hoc edits into a principled workflow that prioritizes detecting behavior changes.

## Key claims

- Legacy code is code without tests (Michael Feathers).
- Changing legacy code creates a dilemma: you need tests to change safely, but you often must change code first to make it testable.
- The legacy code change algorithm is: identify change points, find test points, break dependencies, write tests, then make changes and refactor.
- A seam is a place where behavior can be altered without editing at that exact location.
- Characterization tests document actual current behavior using white-box insight and assertions on real outputs, not intended ideal behavior.
- Dependencies are broken for sensing (observing computed values) and separation (getting code into a test harness without real resources).
- Testability can temporarily trump aesthetics: Testable & Clear > Testable & Muddy > Untestable & Clear > Untestable & Muddy.
- Safe editing rules include hyper-aware editing, single-goal edits, preserving signatures, leaning on the compiler, and pair programming.

## Notes

_yours to annotate_
