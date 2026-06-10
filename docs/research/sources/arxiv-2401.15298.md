---
id: "arxiv-2401.15298"
type: "arxiv"
url: "https://arxiv.org/abs/2401.15298"
raw_url: "https://arxiv.org/pdf/2401.15298"
tags: ["arxiv", "code-quality", "empirical-evaluation", "extract-method", "hallucination-filtering", "intellij-plugin", "llm", "long-methods", "paper", "program-slicing", "refactoring", "static-analysis"]
linked_files: []
relevance: "For a repo-scanning or refactoring-assist tool, this supports pairing LLM extract-method suggestions with static analysis and slicing to validate candidates before recommending changes to high-complexity, long methods."
ingested_at: "2026-06-10 03:14 UTC"
---

# Together We Go Further: LLMs and IDE Static Analysis for Extract Method Refactoring

## Summary

This arXiv paper presents EM-Assist, an IntelliJ IDEA plugin that combines LLM-generated Extract Method refactoring suggestions with IDE static analysis to filter hallucinations, rank candidates via program slicing, and execute refactorings safely. A formative study on 1,752 scenarios found LLMs give strong expert-like suggestions but up to 76.3% are hallucinations. EM-Assist outperforms prior tools on a replication corpus and earned strong agreement from industrial developers.

## Key claims

- LLMs are effective at suggesting Extract Method refactorings that resemble expert developer choices, but up to 76.3% of their suggestions are hallucinations.
- Combining LLM suggestions with static analysis—hallucination removal, program-slicing-based enhancement and ranking, and IDE-backed execution—produces more reliable Extract Method refactorings.
- EM-Assist matches developer-performed refactorings in 53.4% of 1,752 replicated open-source cases, beating the previous best recall of 39.4%.
- In firehouse surveys with 16 industrial developers on recent commits, 81.3% agreed with EM-Assist recommendations.
- Traditional automated Extract Method tools often fail to align with developer preferences and acceptance criteria despite steady research progress.

## Notes

_yours to annotate_
