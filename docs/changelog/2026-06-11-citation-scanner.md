# Code → vault citation scanner

**Date:** 2026-06-11

## What changed

`repo_scan/citations.py` scans `.py` files (excluding `tests/` by default) for:

- `# see docs/...` and `# docs/...` path references
- `[[wikilinks]]` in comments and docstrings
- `# spec: stem` and `# ticket: stem` tags

Unresolved references are dropped. Results are stored in `scan.json` as `citations`
and indexed for provenance scoring and graph `cites` edges.

## Tests

- `tests/test_citations.py`
