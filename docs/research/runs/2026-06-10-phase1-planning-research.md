---
type: research-run
question: "Phase 1 planning: repo_snapshot patterns, Mermaid ticket diagrams, live dashboard UX"
strategy: "GitHits search + get_example on aider repomap, humanlayer ACE workshop, SSE stdlib, Mermaid coupling subgraphs, token-budget injection; synthesize into docs/planning/phase-1-week1.md"
ingested_at: "2026-06-10 16:05 UTC"
---

# Research run — Phase 1 planning (2026-06-10)

## Question

What do industry patterns say about (1) ranked repo snapshots for coding agents,
(2) Mermaid coupling diagrams on tickets, and (3) live ops dashboard updates —
and how do they map to repo-scan's Week 1 tasks?

## Sources ingested this run

| Ref | Why |
|-----|-----|
| [[url-aider-chat-docs-repomap]] | Graph-ranked map + token budget → `repo_snapshot()` design |
| [[url-humanlayer-advanced-context-engineering]] | Research/plan/implement separation → injection at research boundary |
| [[url-githits-repo-snapshot-token-budget]] | Digest dedup across parallel LLM calls |
| [[url-githits-mermaid-coupling-subgraph]] | Validates tkt-0012 Evidence diagram shape |
| [[url-githits-sse-stdlib-dashboard]] | Deferred SSE reference for Phase 3 |

## Findings

1. **Do not dump the repo.** Aider's repo map and repo-scan's existing PageRank
   ranking converge on the same idea: send ranked structural context, let the
   agent pull files. `repo_snapshot()` should extend `scan.json` + tickets, not
   replace selective file reads.

2. **Freshness is a stage boundary concern.** HumanLayer's workshop treats
   codebase research as a explicit pre-plan step. Repo-scan should inject
   snapshot at `PROPOSE` and `ANALYZE` minimum; digest dedup prevents parallel
   loops from multiplying tokens.

3. **Diagrams belong in the vault first, hub second.** tkt-0012 spec correctly
   scopes Mermaid to markdown artifacts; phone UI should link/open docs, not
   render Mermaid inline in Phase 1.

4. **Live UX can ship before SSE.** Adaptive 3s polling on active runs delivers
   most of the perceived latency win; SSE is Phase 3 per stdlib example research.

## Output

Plan written: [[phase-1-week1]] (ready for human review and build).

## Failed / skipped

- `docs_read` on aider/humanlayer via MCP required `page_id` param — recovered
  via search hits + manual read equivalent content.
