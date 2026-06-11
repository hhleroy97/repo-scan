# HANDOFF — Stage 0: Boundary hardening (import contracts + scan.json schema)

> **Scope:** Enforce the five-cluster architecture *inside* the existing single
> package. No distribution split, no repo restructure, no module moves except
> one small extraction (Task 1). When this handoff is complete, the dependency
> DAG `hub → radar → {tickets, vault} → core` is machine-enforced in CI, and
> `scan.json` carries a versioned, schema-validated contract.
>
> **Out of scope:** splitting into multiple pip packages, renaming/moving
> modules into `core/` / `vault/` subpackages, changing any CLI behavior,
> changing any report output other than `scan.json` gaining one field.

---

## Context

repo-scan (v0.2.0, ~11k lines, 77 modules) has five logical clusters:

| Cluster | Modules (current layout) |
|---------|--------------------------|
| **core** | `scanner.py`, `report_pipeline.py`, `writers.py`, `languages.py`, `graphs.py`, `ranking.py`, `complexity.py`, `churn.py`, `behavior.py`, `identity.py`, `tests_map.py`, `digest.py`, `handoff.py`, `trends.py`, `config.py`, `utils.py`, `cli.py` |
| **vault** | `citations.py`, `provenance.py`, `provenance_lint.py`, `provenance_audit.py` |
| **tickets** | `tickets/` package (11 modules) |
| **radar** | `radar/` package |
| **hub** | `hub/` package (incl. `hub/ui/`) |

Intended dependency direction (lower layers must never import higher ones):

```
hub  →  radar  →  tickets
                  vault     →  core
```

One known violation exists today: `tickets/parse.py` imports
`parse_frontmatter` / `frontmatter` from `radar/sources.py` (a lower layer
importing a higher one). Task 1 removes it; the linter in Task 2 then locks
the DAG. Task 3 versions the `scan.json` file contract that clusters use to
communicate instead of imports.

**Standing constraints — do not violate:**

- **Zero runtime dependencies.** stdlib only at runtime. Anything added here
  (`import-linter`, `jsonschema`) is dev/CI tooling only — it goes in the
  `[dev]` extra, never in `dependencies`.
- **Docs as ground truth.** The schema file lives in the repo, committed.
- Writer output is pinned by syrupy snapshots. `scan.json` gains a
  `schema_version` field, which **will invalidate snapshot baselines** — see
  Task 3 step 5 for the controlled refresh.

---

## Task 1 — Extract frontmatter parsing into core

**Why:** `parse_frontmatter` is generic YAML-frontmatter parsing, not
radar-specific. It is the only upward import in the codebase and blocks the
layer contract.

**Steps:**

1. Create `repo_scan/frontmatter.py` (core layer, stdlib only). Move
   `parse_frontmatter` and the `frontmatter` helper (and any private helpers
   they exclusively use) out of `radar/sources.py` verbatim — behavior-preserving
   move, no rewrites.
2. In `radar/sources.py`, replace the moved code with
   `from repo_scan.frontmatter import parse_frontmatter, frontmatter`
   (re-export) so any existing external callers of `radar.sources` keep working.
3. Update `tickets/parse.py` to import from `repo_scan.frontmatter` directly.
4. Grep the whole repo for other imports of these symbols from `radar.sources`
   (hub, vault modules, tests) and repoint them to `repo_scan.frontmatter`.
   Leave the `radar/sources.py` re-export in place regardless.
5. Run the full test suite. This is a pure move; **zero snapshot changes are
   expected.** If a snapshot changes, the move was not behavior-preserving — stop
   and fix.

**Acceptance criteria:**

- [x] `repo_scan/frontmatter.py` exists, stdlib-only, no imports from
      `radar/`, `tickets/`, `hub/`, or vault modules
- [x] `tickets/` has zero imports from `repo_scan.radar`
- [x] `from repo_scan.radar.sources import parse_frontmatter` still works
      (re-export preserved)
- [x] Full pytest suite green with **no snapshot updates**

---

## Task 2 — Enforce the layer DAG with import-linter

**Why:** This is the mechanical guarantee that the five clusters stay
separable. Violations fail loudly in CI instead of silently accumulating.

**Steps:**

1. Add `import-linter>=2.0` to the `[dev]` optional dependencies in
   `pyproject.toml`.
2. Add the contract config to `pyproject.toml`. Because core/vault modules are
   currently top-level (not subpackages), use **forbidden contracts** keyed to
   the real module names rather than a layers contract:

```toml
[tool.importlinter]
root_package = "repo_scan"

# ── Upward-import bans, lowest layer first ──────────────────────────────

[[tool.importlinter.contracts]]
name = "core must not import vault, tickets, radar, or hub"
type = "forbidden"
source_modules = [
    "repo_scan.scanner",
    "repo_scan.report_pipeline",
    "repo_scan.writers",
    "repo_scan.languages",
    "repo_scan.graphs",
    "repo_scan.ranking",
    "repo_scan.complexity",
    "repo_scan.churn",
    "repo_scan.behavior",
    "repo_scan.identity",
    "repo_scan.tests_map",
    "repo_scan.digest",
    "repo_scan.handoff",
    "repo_scan.trends",
    "repo_scan.config",
    "repo_scan.utils",
    "repo_scan.frontmatter",
]
forbidden_modules = [
    "repo_scan.citations",
    "repo_scan.provenance",
    "repo_scan.provenance_lint",
    "repo_scan.provenance_audit",
    "repo_scan.tickets",
    "repo_scan.radar",
    "repo_scan.hub",
]

[[tool.importlinter.contracts]]
name = "vault must not import tickets, radar, or hub"
type = "forbidden"
source_modules = [
    "repo_scan.citations",
    "repo_scan.provenance",
    "repo_scan.provenance_lint",
    "repo_scan.provenance_audit",
]
forbidden_modules = [
    "repo_scan.tickets",
    "repo_scan.radar",
    "repo_scan.hub",
]

[[tool.importlinter.contracts]]
name = "tickets must not import radar or hub"
type = "forbidden"
source_modules = ["repo_scan.tickets"]
forbidden_modules = ["repo_scan.radar", "repo_scan.hub"]

[[tool.importlinter.contracts]]
name = "radar must not import hub"
type = "forbidden"
source_modules = ["repo_scan.radar"]
forbidden_modules = ["repo_scan.hub"]
```

   **Adjust the core/scanner module lists to match the actual top-level
   modules in the repo** — the lists above are from the project checkpoint and
   may be incomplete. Any top-level module not listed should be classified
   (core or vault) and added; do not leave modules uncovered.

   Note on `cli.py`: the `repo-scan tickets` subcommands mean `cli.py` likely
   imports `repo_scan.tickets`. If `lint-imports` flags it, **remove `cli.py`
   from the core source list** and document it as a composition-layer module
   (entry points are allowed to import downward into any cluster). Do not
   silence the violation with `ignore_imports` — reclassify instead.

3. Run `lint-imports` locally. Expected result after Task 1: **all contracts
   pass.** If anything else fails, list each violation in the PR description
   with a one-line judgment: (a) trivial fix (move the import, use the
   `scan.json` contract instead), or (b) a genuine seam problem — fix (a)
   inline, file (b) as a note, do not restructure modules in this pass.
4. Wire into CI: add a `lint-imports` step to
   `.github/workflows/ci.yml` after install, before pytest. It must fail the
   build on contract violation.
5. Optional, if cheap: add `lint-imports` to the pre-commit hook installed by
   `repo-scan --install-hook`, guarded by an availability check (the hook must
   not break for users without the dev extra installed).

**Acceptance criteria:**

- [x] `lint-imports` passes locally and runs in CI as a required step
- [x] Every top-level module and subpackage of `repo_scan` is covered by at
      least one contract (as source or explicitly documented as composition
      layer: `cli.py`, `scanner.py`, `report_pipeline.py`, `writers.py`, `__init__.py`)
- [x] No `ignore_imports` entries in the config (reclassify, don't suppress)
- [x] A deliberate test violation (temporarily add `from repo_scan import hub`
      to `utils.py`) makes `lint-imports` fail; revert after confirming
- **Note:** `radar → hub` contract deferred — genuine seam (progress/state/telemetry).
  Documented in `pyproject.toml` and changelog.

---

## Task 3 — Version and schema-validate scan.json

**Why:** `scan.json` is the inter-cluster contract (hub, tickets, radar all
read it). File-convention contracts fail silently; a schema plus a version
field makes drift loud.

**Steps:**

1. **Add `schema_version` to scan.json output.** In the writer that emits
   `scan.json` (in `writers.py` / `report_pipeline.py`), add a top-level
   integer field `"schema_version": 1` as the *first* key.
2. **Create `repo_scan/schemas/scan.schema.json`** (committed, shipped via
   package data). Start from the stub below, then **complete it by reading the
   actual scan.json writer code** — every key the writer emits must appear in
   `properties`. Where the writer's structure is dynamic (per-language maps,
   per-file entries), use `additionalProperties` with a typed value schema
   rather than enumerating keys.

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://raw.githubusercontent.com/hhleroy97/repo-scan/main/repo_scan/schemas/scan.schema.json",
  "title": "repo-scan scan.json contract",
  "description": "Machine-readable sidecar emitted by repo-scan. Consumed by tickets, radar (repo_snapshot), and hub. Bump schema_version on any breaking shape change; additive optional fields do not require a bump.",
  "type": "object",
  "required": ["schema_version", "generated_at"],
  "properties": {
    "schema_version": { "type": "integer", "const": 1 },
    "generated_at": { "type": "string" },

    "identity": { "type": "object" },
    "languages": { "type": "object" },
    "ranking": { "type": "array", "items": { "type": "object" } },
    "complexity": { "type": "object" },
    "churn": { "type": "object" },
    "coupling": { "type": "object" },

    "vault_health": {
      "type": "object",
      "properties": {
        "score_histogram": { "type": "object" },
        "knowledge_debt": { "type": "number" }
      }
    },
    "citations": { "type": "object" },
    "tickets": { "type": "object" },
    "trend": { "type": "object" }
  },
  "additionalProperties": true
}
```

   The keys above are a **stub from the project checkpoint** — treat the
   writer code as ground truth and replace/extend every placeholder
   `{ "type": "object" }` with the real shape, including `required` arrays for
   fields that downstream consumers (`hub/server.py`, `radar` repo_snapshot,
   `tickets/` proposal logic) actually read. Grep those consumers for
   `scan.json` key accesses and mark exactly those keys `required` — the
   schema's `required` set *is* the compatibility contract.
3. **Validation is dev/test-only** (zero-runtime-deps constraint). Add
   `jsonschema>=4` to the `[dev]` extra. Do **not** import it anywhere under
   `repo_scan/` runtime code paths.
4. **Add `tests/test_scan_schema.py`:**
   - Run a scan against a small fixture repo (or the repo itself if existing
     tests already do this) and validate the emitted `scan.json` against
     `repo_scan/schemas/scan.schema.json` with `jsonschema.validate`.
   - Assert `schema_version == 1`.
   - Assert every key marked `required` in the schema is present.
5. **Runtime guard (stdlib only):** in each consumer that loads `scan.json`
   (hub, radar snapshot, tickets), add a single check after `json.load`:
   if `data.get("schema_version") != 1`, log/emit a clear warning event
   ("scan.json schema_version X != expected 1 — re-run repo-scan") and degrade
   gracefully (skip the dependent feature rather than rendering wrong data).
   Keep this to a tiny shared helper in core (e.g. `repo_scan/utils.py`:
   `check_scan_schema_version(data) -> bool`).
6. **Snapshot refresh:** the new `schema_version` key will change pinned
   `scan.json` goldens. Run `pytest --snapshot-update`, then **diff the
   snapshot changes and confirm the only delta is the added
   `schema_version` field.** Any other delta is a regression — stop.
7. Document the contract: add a short "scan.json contract" subsection to the
   README's Output section — one paragraph: where the schema lives, what
   `schema_version` means, bump policy (breaking shape change → bump;
   additive optional field → no bump).

**Acceptance criteria:**

- [x] Emitted `scan.json` begins with `"schema_version": 1`
- [x] `repo_scan/schemas/scan.schema.json` committed, ships as package data,
      and validates real scan output in a pytest test
- [x] Keys read by hub/radar/tickets consumers are listed in `required`
- [x] `jsonschema` appears only in `[dev]` extras; `grep -r "import jsonschema" repo_scan/` returns nothing
- [x] All consumers warn-and-degrade on a `schema_version` mismatch
      (`hub/server.py`, `radar/pipeline.py`, `radar/research.py`,
      `tickets/generation.py`, `tickets/merge.py`)
- [x] Snapshot diff contains only the `schema_version` addition
- [x] README documents the contract and bump policy

---

## Task 4 (optional, do only if Tasks 1–3 land green) — Install extras for rotation

**Why:** Lets pieces rotate in/out at install time without a package split.

**Steps:**

1. In `pyproject.toml`, define extras: `tickets`, `radar`, `hub`, `vault`,
   `all`. Since runtime is stdlib-only, these extras carry no dependencies
   today — they exist as **forward-compatible markers** and to gate optional
   tool hints.
2. The real rotation mechanism is lazy imports: confirm `cli.py` and the
   `radar` entry point import `tickets`/`radar`/`hub` lazily (inside command
   functions, not at module top), so `repo-scan` core commands work even if a
   future split removes a cluster. Fix any eager imports found.

**Acceptance criteria:**

- [x] `python -c "import repo_scan.scanner"` succeeds without importing
      `radar`, `hub`, or `tickets` (verified by `tests/test_lazy_imports.py`)
- [x] Extras declared; `pip install -e ".[all,dev]"` works

---

## Definition of done (whole handoff)

- [x] All Task 1–3 acceptance criteria checked (Task 4 also completed)
- [x] Full pytest suite green (449 passed); snapshot delta = zero (schema_version
      was already present from a prior pass)
- [x] CI runs `lint-imports` + pytest and is green
- [x] No new runtime dependencies (`dependencies = []` unchanged)
- [x] Changelog entry added: `docs/changelog/2026-06-11-boundary-hardening.md`
- [x] Genuine seam violation documented: `radar → hub` (progress/state/telemetry
      coupling). Filed in changelog and as a `pyproject.toml` comment for future stage.

## Risks / watch-fors

- **Hidden upward imports in hub/ui fragments** — 17 fragment files; grep them
  all, not just `hub/server.py`.
- **`cli.py` classification** — expected to be composition-layer; reclassify,
  don't suppress.
- **Schema too strict** — if the writer emits keys conditionally (optional
  tools absent → sections missing), those keys must not be in `required`.
  Test with optional tools unavailable (the existing offline test harness
  should cover this).
- **Do not restructure modules** into `core/`/`vault/` subpackages in this
  pass, even though the contract config would get prettier. That's a separate,
  later handoff — this one must stay a low-risk, behavior-preserving change.
