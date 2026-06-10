---
id: "gh-eyeseast-python-frontmatter"
type: "github"
url: "https://github.com/eyeseast/python-frontmatter"
raw_url: "https://github.com/eyeseast/python-frontmatter"
tags: ["document-parsing", "frontmatter", "markdown", "metadata", "pypi", "python", "repo", "round-trip", "static-site", "yaml"]
linked_files: ["repo_scan/radar/sources.py"]
relevance: "repo-scan already writes and parses YAML frontmatter for tickets, research sources, and radar artifacts via a stdlib-only helper in repo_scan/radar/sources.py, so python-frontmatter is a reference implementation for richer parsing (JSON/TOML, nested structures) or a potential optional dependency if the custom writer/parser hits edge cases—without adding a dependency today."
ingested_at: "2026-06-10 07:21 UTC"
---

# eyeseast/python-frontmatter — Parse and manage posts with YAML (or other) frontmatter

## Summary

python-frontmatter is a small, mature Python library (416 GitHub stars) for reading and writing text documents with delimited metadata blocks—YAML by default, with support for JSON, TOML, and custom parsers. It exposes load/loads/parse for ingestion and dump/dumps for round-tripping, returning a Post object whose metadata is dict-like and whose body is available as .content. It is widely used for static-site generators, note tools, and any workflow that treats markdown-plus-metadata as a first-class document format.

## Key claims

- Parses frontmatter-delimited documents from a file path, file-like object, or raw string via frontmatter.load, frontmatter.loads, and frontmatter.parse
- Returns a Post object combining metadata and body content, with metadata accessible as post['key'] and post.metadata
- Serializes posts back to text with frontmatter.dump and frontmatter.dumps, preserving --- delimiters and metadata ordering
- Supports YAML, JSON, TOML, and other formats through pluggable parsers (customizable in examples/)
- Documents UTF-8 BOM handling via encoding='utf-8-sig' when reading files that may include a byte-order mark
- Test suite includes sample files with matching .result.json expected outputs for regression coverage
- Published on PyPI as python-frontmatter with Read the Docs documentation

## Notes

_yours to annotate_
