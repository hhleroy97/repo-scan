---
id: "gh-XAMPPRocky-tokei"
type: "github"
url: "https://github.com/XAMPPRocky/tokei"
raw_url: "https://github.com/XAMPPRocky/tokei"
tags: ["cli", "cloc", "code-statistics", "gitignore", "json-output", "library", "line-counting", "repo", "rust", "sloc", "static-analysis", "yaml-output"]
linked_files: []
relevance: "repo-scan already documents tokei as an optional line-count tool and drives health/index reports from per-file line metrics, so Tokei's fast accurate counting and JSON output could replace or augment the built-in get_line_counts path in scan.json and size-threshold workflows."
ingested_at: "2026-06-10 04:02 UTC"
---

# XAMPPRocky/tokei — Count your code, quickly.

## Summary

Tokei is a fast, accurate Rust CLI and library that counts source lines by language, reporting files, total lines, code, comments, and blanks. It supports 150+ languages, respects gitignore-style exclusion rules, and can emit machine-readable JSON, YAML, or CBOR for downstream tooling.

## Key claims

- Counts millions of lines in seconds and is positioned as faster than comparable cloc-style tools
- Accurately classifies lines by handling multiline comments, nested comments, and comments inside strings
- Supports 150+ languages defined in languages.json with extensible contribution workflow
- Outputs human-readable terminal tables or structured JSON, YAML, and CBOR via --output
- Can merge prior runs with new scans using --input from file or stdin
- Respects .gitignore, .ignore, and .tokeignore; supports --exclude with gitignore semantics
- Offers per-file statistics with --files and sortable columns (files, lines, code, comments, blanks)
- Ships as both a CLI and a Rust library (docs.rs) for programmatic integration

## Notes

_yours to annotate_
