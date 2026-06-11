# Stage 0 — Boundary hardening (import contracts + scan.json schema)

**Date:** 2026-06-11

## Summary

Enforced the five-cluster architecture (`hub → radar → {tickets, vault} → core`)
inside the existing single package using machine-checked import contracts and a
versioned `scan.json` schema. No module moves, no distribution split, no CLI
behavior changes.

## Changes

### Task 1 — Frontmatter extraction
- Created `repo_scan/frontmatter.py` with `parse_frontmatter`, `frontmatter`,
  `slugify` (moved from `radar/sources.py`).
- Re-exports preserved in `radar/sources.py` for backward compatibility.
- `tickets/` now imports from `repo_scan.frontmatter` (zero radar imports).

### Task 2 — Import layer contracts
- Added `import-linter>=2.0` to `[dev]` extras.
- Three `[tool.importlinter.contracts]` in `pyproject.toml` enforce:
  - core must not import vault, tickets, radar, or hub
  - vault must not import tickets, radar, or hub
  - tickets must not import radar or hub
- `lint-imports` runs in CI (`.github/workflows/ci.yml`) before pytest.
- `config.py` now defines `HUB_CONFIG_KEYS`, `HUB_DEFAULTS`, `cfg_hub`
  directly (was importing from `hub.settings`, a layer violation).
  `hub/settings.py` re-exports from config.

### Task 3 — scan.json versioned schema
- `scan.json` carries `"schema_version": 1` as first key.
- `repo_scan/schemas/scan.schema.json` committed and ships as package data.
- `jsonschema>=4` added to `[dev]` extras (validation is test-only).
- `tests/test_scan_schema.py` validates real scan output against the schema.
- Consumers (`hub/server.py`, `radar/pipeline.py`, `radar/research.py`,
  `tickets/generation.py`, `tickets/merge.py`) check `schema_version` at load
  and degrade gracefully on mismatch via `utils.check_scan_schema_version`.
- README documents the contract and bump policy.

### Task 4 — Install extras and lazy imports
- Optional extras declared: `vault`, `tickets`, `radar`, `hub`, `all`.
- `scanner.py` imports `tickets` and `citations` lazily (inside functions).
- `import repo_scan.scanner` no longer eagerly loads radar, hub, or tickets
  (verified by `tests/test_lazy_imports.py`).

## Known seam (filed, not fixed)

`radar → hub`: radar.act, radar.pipeline, radar.gates, radar.llm, and
radar.research all import hub.progress/state/telemetry for live monitoring.
radar.cli is composition-layer (launches hub.server/daemon/tui). Fixing
requires extracting abstract callbacks into core — a future stage.

## Composition-layer modules

The following modules import across cluster boundaries by design (they
orchestrate the full scan/report pipeline):
- `cli.py`, `scanner.py`, `report_pipeline.py`, `writers.py`, `__init__.py`

## Metrics

- 449 tests pass, 10 snapshots unchanged
- 3 import contracts enforced, 0 broken
- 0 runtime dependencies added
