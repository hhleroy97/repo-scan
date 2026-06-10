---
id: "arxiv-2409.16739"
type: "arxiv"
url: "https://arxiv.org/abs/2409.16739"
raw_url: "https://arxiv.org/pdf/2409.16739"
tags: ["arxiv", "automated-refactoring", "chain-of-thought", "empirical-evaluation", "java", "llm", "paper", "refactoring", "test-smells", "testing", "unit-testing"]
linked_files: []
relevance: "For a repo-scanning or code-quality tool, this supports LLM-assisted test smell detection and refactoring pipelines that pair extracted test context with structured smell catalogs and validation checkpoints rather than one-shot generation."
ingested_at: "2026-06-10 06:59 UTC"
---

# Automated Unit Test Refactoring

## Summary

This arXiv paper introduces UTRefactor, a context-enhanced, LLM-based framework for automatically refactoring unit tests in Java projects. It combines extracted test context with an external knowledge base of test smell definitions and DSL-based refactoring rules, using chain-of-thought prompting and checkpoints to handle multiple smells systematically. On 879 tests across six open-source Java projects, it reduced test smells from 2,375 to 265 (89% reduction), outperforming both direct LLM refactoring and rule-based tools.

## Key claims

- Test smells from poor design and weak domain knowledge degrade test maintainability; manual refactoring is slow and error-prone.
- Rule-based test smell refactoring struggles outside predefined rules and lacks flexibility for diverse cases.
- UTRefactor guides an LLM through step-by-step smell elimination by simulating manual refactoring with chain-of-thought and enriched context.
- A checkpoint mechanism supports comprehensive refactoring when multiple test smells appear in the same test.
- On 879 tests from six Java projects, UTRefactor cut smells from 2,375 to 265 (89% reduction).
- UTRefactor beat direct LLM refactoring by 61.82% in smell elimination and significantly outperformed a rule-based refactoring tool.

## Notes

_yours to annotate_
