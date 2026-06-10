---
id: "arxiv-2605.02741"
type: "arxiv"
url: "https://arxiv.org/abs/2605.02741"
raw_url: "https://arxiv.org/pdf/2605.02741"
tags: ["ai-agents", "code-quality", "code-smells", "coupling", "llm-generated-code", "maintainability", "paper", "prompt-engineering", "software-architecture", "technical-debt"]
linked_files: []
relevance: "For an LLM- and agent-driven codebase like repo-scan, this supports measuring structural quality (volume, coupling, smells) alongside functional correctness in radar pipelines, gates, and telemetry—not assuming better prompts or passing tests imply maintainable architecture."
ingested_at: "2026-06-10 18:27 UTC"
---

# AI-Generated Smells: An Analysis of Code and Architecture in LLM and Agent-Driven Development

## Summary

This arXiv paper systematically audits technical debt in LLM- and agent-generated software, arguing that AI does not remove flaws but leaves a distinct machine signature of defects. Across single-file tasks and multi-component agent systems, the authors find a Reasoning-Complexity Trade-off: stronger models tend to produce more bloated, tightly coupled code, summarized as a Volume-Quality Inverse Law where size strongly predicts structural degradation. Neither passing functional tests nor richer prompting reliably fixes this decay, so the authors reframe AI software engineering around architectural complexity management rather than raw generation.

## Key claims

- AI-generated software carries a distinct machine signature of defects and technical debt, not just occasional bugs.
- More capable models tend to generate increasingly bloated and coupled code (Reasoning-Complexity Trade-off).
- Code volume is a near-perfect predictor of structural degradation (Volume-Quality Inverse Law).
- Functional correctness and detailed prompting do not meaningfully mitigate architectural decay.
- The central challenge in AI-based software engineering is managing architectural complexity, not merely generating working code.
- Future agent systems need explicit architectural foresight to produce maintainable, not just functional, software.

## Notes

_yours to annotate_
