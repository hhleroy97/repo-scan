---
id: "gh-blacksmithgu-obsidian-dataview"
type: "github"
url: "https://github.com/blacksmithgu/obsidian-dataview"
raw_url: "https://github.com/blacksmithgu/obsidian-dataview"
tags: ["dataview", "frontmatter", "indexing", "inline-fields", "knowledge-base", "markdown", "metadata", "obsidian", "obsidian-plugin", "query-language", "repo", "tasks", "typescript", "yaml"]
linked_files: []
relevance: "repo-scan already stores tickets, research sources, and radar artifacts as YAML-frontmatter Markdown explicitly designed to be Dataview-queryable, so this project is the canonical reference for how to query, aggregate, and visualize that metadata in Obsidian (boards, filtered lists, task views) without building a custom UI."
ingested_at: "2026-06-10 07:23 UTC"
---

# blacksmithgu/obsidian-dataview — A data index and query language over Markdown files, for https://obsidian.md/.

## Summary

Obsidian Dataview is a popular TypeScript Obsidian plugin (~9k stars) that indexes a vault’s Markdown files and exposes metadata through a pipeline query language (DQL), inline expressions, and a JavaScript API (DataviewJS). It treats YAML frontmatter and inline `Key:: Value` fields as queryable data, enabling tables, lists, task views, grouping, and sorting across notes. It matters as a mature, user-facing reference for metadata-driven knowledge bases built on plain Markdown files.

## Key claims

- Indexes vault Markdown by extracting YAML frontmatter and Dataview inline fields (`Key:: Value`) into a queryable data model
- Provides four query modes: Dataview Query Language (DQL), inline DQL expressions, DataviewJS, and inline JavaScript expressions
- DQL is pipeline-based and SQL-like; regular Dataview queries are sandboxed and read-only relative to the vault
- DataviewJS runs with full Obsidian plugin privileges and can read, write, delete files and make network calls
- Supports common operations: filter (`from`), sort, table/list/task rendering, grouping, and field projection
- Published TypeScript typings on npm (`blacksmithgu/obsidian-dataview`) for third-party plugin integration
- Built with TypeScript, Rollup, and npm; local dev deploys to a test vault with watch-mode rebuild
- Documentation uses MkDocs and auto-deploys to GitHub Pages on merge to main

## Notes

_yours to annotate_
