---
id: "url-githits-mermaid-coupling-subgraph"
type: "url"
url: "https://app.githits.com/solutions/96d85ef8-6e73-4c34-be5b-71359ca1f63b"
raw_url: "https://github.com/maskati/bicep-dependency-diagram"
tags: ["mermaid", "coupling", "subgraph", "tickets", "visualization"]
linked_files: ["repo_scan/graphs.py", "repo_scan/tickets/__init__.py", "docs/tickets/tkt-0012.md"]
relevance: "Validates tkt-0012 spec approach: graph LR with subgraphs for coupled components, directed edges for dependencies — matches coupling_to_mermaid and ticket Evidence diagrams in the approved spec."
ingested_at: "2026-06-10 16:00 UTC"
---

# GitHits — Mermaid subgraph coupling diagrams

## Summary

GitHits example for documenting component coupling in Markdown: `graph LR` with named `subgraph` blocks (Frontend, Backend, Data) and directed edges between groups. Repo-scan's tkt-0012 spec uses the same mental model at file-level (`graph TD`, dashed red for seam edges, solid gray for import-backed). Complements existing source [[gh-mermaid-js-mermaid]].

## Key claims

- Subgraphs group tightly coupled modules; edges show cross-group dependencies.
- `graph LR` vs `graph TD` — tkt-0012 spec chose TD for ticket Evidence (mobile vertical scroll).
- Diagrams-as-code stay in version control beside tickets and reports.
- GitHub and Obsidian render Mermaid natively — hub can link to vault docs, not render inline (out of scope per spec).

## GitHits provenance

- `get_example` query: "Mermaid flowchart subgraph coupling dependency diagram in markdown documentation"
- solution_id: `96d85ef8-6e73-4c34-be5b-71359ca1f63b`
- Reference: [maskati/bicep-dependency-diagram](https://github.com/maskati/bicep-dependency-diagram) (MIT)

## Notes

_yours to annotate — Phase 1 task 1.1 merges PR #11 implementing this spec; hub Phase 3 could show rendered diagram thumbnails._
