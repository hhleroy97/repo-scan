---
id: "arxiv-2411.12924"
type: "arxiv"
url: "https://arxiv.org/abs/2411.12924"
raw_url: "https://arxiv.org/pdf/2411.12924"
tags: ["atlassian", "code-quality", "coding-agents", "deployment", "evaluation", "human-in-the-loop", "jira", "llm-agents", "multi-agent", "paper", "planning", "software-engineering"]
linked_files: []
relevance: "repo-scan’s radar loop and ticket gates already pair agent CLIs with human approval, so HULA’s staged human guidance and its finding that agents help most on planning and simple tasks—but not always on quality—can inform when to require human review, how to structure ticket specs, and what to measure in real deployments."
ingested_at: "2026-06-10 06:09 UTC"
---

# Human-In-the-Loop Software Development Agents

## Summary

This arXiv paper introduces HULA, a human-in-the-loop LLM multi-agent framework for software development that lets engineers guide and refine coding plans and generated code. The authors designed, implemented, and deployed HULA in Atlassian JIRA for real internal use, then evaluated it with practicing engineers. It matters because it moves beyond historical benchmarks to study how human feedback at each stage affects practical agent-assisted development.

## Key claims

- Existing LLM-based multi-agent software engineering work is mostly evaluated on historical benchmarks, rarely incorporates human feedback at each development stage, and has seen little real-world deployment.
- HULA embeds human-in-the-loop refinement into plan generation and code generation for a given development task.
- HULA was deployed in production-like use inside Atlassian JIRA for internal software engineering workflows.
- Atlassian engineers reported that HULA can reduce overall development time and effort, especially for initiating coding plans and writing code on straightforward tasks.
- Code quality remains a concern in some cases, indicating human oversight is still needed even when agents accelerate work.
- The authors distill lessons learned and outline future opportunities for advancing LLM-based development agents.

## Notes

_yours to annotate_
