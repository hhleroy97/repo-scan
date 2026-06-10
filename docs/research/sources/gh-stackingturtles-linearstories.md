---
id: "gh-stackingturtles-linearstories"
type: "github"
url: "https://github.com/stackingturtles/linearstories"
raw_url: "https://github.com/stackingturtles/linearstories"
tags: ["acceptance-criteria", "agentic-development", "cli", "coding-agents", "linear", "markdown", "project-management", "repo", "sync", "typescript", "user-stories"]
linked_files: ["repo_scan/tickets/__init__.py"]
relevance: "repo-scan already uses markdown tickets with checkbox acceptance criteria in its RADAR loop, so linearstories offers a concrete pattern—and optional Linear sync—for keeping agent-readable specs in-repo while exposing human-friendly views to project managers."
ingested_at: "2026-06-10 06:09 UTC"
---

# stackingturtles/linearstories — A tool for managing Agent Developer requirements in Linear

## Summary

linearstories is a TypeScript CLI that syncs markdown user stories with Linear issues, designed for AI agent-driven development. It enforces structured user stories with explicit, checkbox-based acceptance criteria so agents get deterministic, testable scope boundaries. Markdown files in the repo act as the source of truth while import/export keeps Linear boards current without duplicate issues.

## Key claims

- AI coding agents perform dramatically better when given precise, testable acceptance criteria rather than vague tickets
- Acceptance criteria written as markdown checkboxes map directly to test cases agents can implement and verify
- Markdown user stories in the repository serve as the source of truth agents can read without project-management API access
- Two-way sync with Linear lets engineering managers keep boards current while agents keep specs current in the repo
- The import command creates new Linear issues or updates existing ones based on whether linear_id is present in story metadata
- Story files support YAML frontmatter defaults, per-story metadata blocks (priority, labels, estimate, assignee, status), and multiple stories per file via H2 headings
- Configuration supports .linearrc.json, LINEAR_API_KEY environment variable (which takes precedence), and named multi-context configs for multiple Linear organizations

## Notes

_yours to annotate_
