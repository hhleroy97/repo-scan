---
id: "url-humanlayer-advanced-context-engineering"
type: "url"
url: "https://github.com/humanlayer/humanlayer/blob/main/docs/workshop.mdx"
raw_url: "https://github.com/humanlayer/humanlayer/blob/main/docs/workshop.mdx"
tags: ["context-engineering", "research-plan-implement", "human-in-the-loop", "agents", "repo-scan"]
linked_files: ["repo_scan/radar/pipeline.py", "repo_scan/radar/research.py"]
relevance: "Validates repo-scan's RADAR shape (research → plan/spec → act) and the rule that research must not jump to implementation — informs repo_snapshot freshness before analyze/draft stages."
ingested_at: "2026-06-10 16:00 UTC"
---

# HumanLayer — Advanced Context Engineering workshop

## Summary

HumanLayer's workshop teaches a **research / plan / implement** workflow for coding agents: bootstrap codebase research first (`/cl:research_codebase`), explicitly forbid implementation in the research prompt, then create a plan, then implement. Emphasizes **advanced context engineering** — managing what enters the context window at each stage — as the scaling lever for complex codebases. Repo-scan's RADAR loop already maps to this; the gap is **injecting fresh repo state** at research and analyze boundaries.

## Key claims

- Research prompt magic words: "Do not make an implementation plan or explain how to fix."
- Planning prompt: share open questions and phase outline before writing the full plan.
- Context engineering is the primary skill for hard problems in large codebases (YC talk, Aug 2025).
- 12-Factor Agents principles apply to reliable LLM application design.
- Parallel agents + worktrees align with repo-scan's act fan-out model.

## GitHits provenance

- Indexed via GitHits `search` on `github:humanlayer/humanlayer`, query `context engineering repo map codebase snapshot for agents`
- Primary doc: `docs/workshop.mdx` @ bdea199
- Related existing source: [[gh-humanlayer-humanlayer]]

## Notes

_yours to annotate — Phase 2: pre-act context bundle follows research→plan separation; Phase 1 repo_snapshot is the "research_codebase" equivalent for every loop._
