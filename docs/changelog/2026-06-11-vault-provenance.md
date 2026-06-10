# Phase 5 — vault provenance scoring

**Date:** 2026-06-11

## What changed

### Provenance scoring (`repo_scan/provenance.py`)

Each vault doc (ticket, spec, analysis, source) scores 0–4 on four signals:

- **evidence** — wikilinks, `analysis:` frontmatter, or `## Evidence` section
- **linked** — `linked_files` or wikilinks resolve to paths in `scan.json`
- **cited** — Python files reference the doc (`# spec:`, `# see docs/…`, etc.)
- **fresh** — doc mtime is within grace of linked code churn (`behavior.age_days`)

`vault_health` in `scan.json` reports coverage %, orphans by kind, and untracked ranked code.

### Hub Graph — Coverage layer

- Toolbar shows healthy/total docs and coverage %
- Nodes render score rings; tap opens provenance chain panel (`GET /api/graph/chain`)
- Citation edges (`cites`) connect code nodes to vault docs

### Trends

`reports/trend.md` tracks `Vault %` and `Δ vault`; health report includes a vault section.

## Tests

- `tests/test_provenance.py`
- `tests/test_citations.py`
- Updates to `tests/test_hub_graph.py`, `tests/test_hub_ui.py`, `tests/test_trends.py`
