---
id: "gh-github-linguist"
type: "github"
url: "https://github.com/github-linguist/linguist"
raw_url: "https://github.com/github-linguist/linguist"
tags: ["cli", "code-statistics", "generated-code", "git", "gitattributes", "json-output", "language-detection", "repo", "repo-analysis", "ruby", "sloc", "static-analysis", "vendored-files"]
linked_files: []
relevance: "repo-scan could adopt Linguist’s detection strategies, vendored/generated filtering, and JSON language-breakdown output to align repository metrics with GitHub’s canonical language classification or to validate its own heuristics."
ingested_at: "2026-06-10 04:03 UTC"
---

# github/linguist — Language Savant. If your repository's language is being reported incorrectly,…

## Summary

GitHub Linguist is the Ruby library and CLI that powers language detection on GitHub.com, including blob classification, binary/vendored/generated filtering, and repository language breakdown graphs. It analyzes whole Git repos or single files via a layered detection pipeline (filename, extension, heuristics) with `.gitattributes` overrides, and exposes human-readable or JSON output including per-file strategies and SLOC. It is the de facto reference implementation for how GitHub measures and reports repository language composition.

## Key claims

- Powers GitHub.com language detection, diff suppression for generated files, and language breakdown graphs
- Classifies content via ordered strategies—filename, extension, heuristics—with `.gitattributes` able to override or confirm results
- Repository mode aggregates language share by file size (percentage and bytes), optionally per revision via `--rev`
- Single-file mode reports lines, SLOC, MIME type, language, and flags for large, generated, and vendored content
- CLI supports `--breakdown`, `--strategies`, and `--json` for machine-readable downstream tooling
- Built on Ruby with Rugged (libgit2) for Git access and charlock_holmes for encoding detection
- Ships as a gem (`github-linguist`), library API (`Linguist::Repository`), and Docker image for containerized scans

## Notes

_yours to annotate_
