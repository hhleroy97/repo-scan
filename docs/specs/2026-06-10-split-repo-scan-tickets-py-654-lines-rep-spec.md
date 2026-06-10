---
type: "spec"
problem: "Split repo_scan/tickets.py (654 lines). `repo_scan/tickets.py` is 654 lines — past the 600-line critical threshold where files become hard to navigate and review. Acceptance criteria: No resulting file above 300 lines; All tests still pass. Research current best practices and draft a spec for this work."
status: "draft"
audit_verdict: "revise"
analysis: "[[2026-06-10-split-repo-scan-tickets-py-654-lines-rep-analysis]]"
drafted_at: "2026-06-10 18:55 UTC"
---

# Spec — Split repo_scan/tickets.py (654 lines). `repo_scan/tickets.py` is 654 lines — past the 600-line critical threshold where files become hard to navigate and review. Acceptance criteria: No resulting file above 300 lines; All tests still pass. Research current best practices and draft a spec for this work.
_Drafted 2026-06-10 18:55 UTC by radar — **status: draft**_

I'll inspect `tickets.py`, its imports, tests, and the prior UI split so the spec matches the repo.
## Goal

Split `repo_scan/tickets.py` (748 lines, past the 600-line critical threshold) into a `repo_scan/tickets/` package where every module stays ≤300 lines. Preserve the existing public API (`from repo_scan.tickets import …`) so hub, radar, scanner, CLI, and 15+ test call sites need no import changes.

## Approach

Apply Fowler *Move Function* along behavior ownership: each submodule owns one concern; shared constants and path helpers sit in a leaf module with no upward imports. Replace the monolith with a thin `__init__.py` facade that re-exports every public symbol via explicit `__all__` (PEP 8 / Real Python package pattern). **Land order:** create `repo_scan/tickets/` package, verify imports, then **delete** `repo_scan/tickets.py` and remove `repo_scan/__pycache__/tickets*.pyc` so the module file cannot shadow the package. Keep `record_merge_verification`'s lazy `scanner`/`trends` imports in isolated `merge.py` to avoid the `scanner → generate_tickets → scanner` cycle. Keep `new_ticket`'s lazy `radar.sources.slugify` import inside `workflow.py`.

**Date-bearing write paths** (`write_ticket`, board refresh callers) must resolve `now_date` through the package namespace (`from .. import tickets` / `tickets.now_date()`), never `from ..utils import now_date`, so `monkeypatch.setattr("repo_scan.tickets.now_date", …)` keeps working.

## Changes

- **`repo_scan/tickets/constants.py`** — `STATUSES`, `BOARD_COLUMNS`, `OPEN_STATUSES`, `PLACEHOLDER_CRITERIA`, `METRIC_FINGERPRINT_PREFIXES`, `_SCAN_PROPOSAL_KEYS`, `tickets_dir`.
- **`repo_scan/tickets/parse.py`** — `criteria_ready`, `derive_card`, `parse_ticket`, and private card/criterion helpers.
- **`repo_scan/tickets/evidence.py`** — `ticket_evidence_diagrams` (depends on `graphs`, `constants`).
- **`repo_scan/tickets/propose.py`** — `propose_from_scan` only (pure: `cfg` + signal dicts).
- **`repo_scan/tickets/board.py`** — `write_board` (shared leaf: `constants`, `utils.write_doc`).
- **`repo_scan/tickets/io.py`** — `load_tickets`, `write_ticket`, `next_ticket_num`; `write_ticket` calls `evidence`; timestamps via package-level `now_date`.
- **`repo_scan/tickets/workflow.py`** — `new_ticket` (lazy `slugify`), `set_ticket_status`, `append_ticket_note`, `update_ticket_criteria`, `approved_tickets`, `pick_approved_ticket`; status/criteria paths call `board.write_board`.
- **`repo_scan/tickets/generation.py`** — `generate_tickets`, `auto_close_resolved_proposed`, `is_metric_fingerprint`, `signals_from_scan_json`, `fingerprint_still_triggers` (imports `propose`, `io`, `board`; `fingerprint_still_triggers` → `propose_from_scan`).
- **`repo_scan/tickets/merge.py`** — `record_merge_verification` with existing lazy imports retained.
- **`repo_scan/tickets/cli.py`** — `tickets_main`.
- **`repo_scan/tickets/__init__.py`** — Package docstring + re-export full public surface. Explicit `__all__`: `STATUSES`, `BOARD_COLUMNS`, `OPEN_STATUSES`, `PLACEHOLDER_CRITERIA`, `METRIC_FINGERPRINT_PREFIXES`, `tickets_dir`, `criteria_ready`, `derive_card`, `parse_ticket`, `load_tickets`, `next_ticket_num`, `ticket_evidence_diagrams`, `write_ticket`, `propose_from_scan`, `new_ticket`, `set_ticket_status`, `append_ticket_note`, `update_ticket_criteria`, `approved_tickets`, `pick_approved_ticket`, `generate_tickets`, `is_metric_fingerprint`, `auto_close_resolved_proposed`, `signals_from_scan_json`, `fingerprint_still_triggers`, `record_merge_verification`, `write_board`, `tickets_main`, `now_date`.
- **Delete** `repo_scan/tickets.py` after package lands.
- **`tests/test_tickets_package_size.py`** (new) — Parametrized line-count guard for every `repo_scan/tickets/*.py`.

Import DAG (no cycles): `constants` → `parse` → `evidence` → `propose`; `board` is a shared leaf; `io` → `evidence`; `workflow` → `io`, `board`; `generation` → `propose`, `io`, `board`; `merge` → `generation`, `workflow` (+ lazy `scanner`/`trends`); `cli` imports siblings; `__init__` re-exports only.

## Tests

| Acceptance criterion | Automated test |
|---|---|
| No resulting file above 300 lines | `tests/test_tickets_package_size.py::test_tickets_module_line_cap` — parametrized over `repo_scan/tickets/*.py`; assert physical line count ≤ 300 (count all lines, including blanks; first line-cap guard in repo) |
| All tests still pass | Full suite: `pytest` (existing coverage in `tests/test_tickets.py`, `tests/test_tickets_workflow.py`, `tests/test_phase2_freshness.py::test_note_merged_calls_record_verification`, `tests/test_scanner_snapshots.py` monkeypatch paths, hub/radar/daemon/prs tests) |

No consumer import edits; monkeypatch targets `repo_scan.tickets.record_merge_verification` and `repo_scan.tickets.now_date` must resolve through `__init__.py`.

## Documentation

- Move the module-level docstring from `tickets.py` to `repo_scan/tickets/__init__.py` (package overview: vault-as-tracker, card derivation, criteria gate, fingerprint dedup).
- Add one-line module docstrings to each new submodule describing its ownership boundary.
- README: no structural change (paths `docs/tickets/`, CLI `repo-scan tickets` unchanged); optional one-line note that the engine lives in `repo_scan/tickets/` if an architecture section exists.

## Risks

- **Module/package coexistence** — leaving `tickets.py` alongside `tickets/` or stale `.pyc` can shadow the package; delete module file and cache before verifying imports.
- **Circular imports** if `merge.py` or `generation.py` promote lazy imports to module level (`scanner` already imports `generate_tickets` at import time).
- **Incomplete facade** — any missing `__all__` entry (e.g. `propose_from_scan`, `write_board`, `approved_tickets`, `auto_close_resolved_proposed`) breaks hub/radar imports or test monkeypatch paths without consumer edits.
- **Broken `now_date` monkeypatch** if `io.py` binds `now_date` directly from `utils`.
- **Cross-module tangles** if `workflow` and `io` both grow write-path logic; keep `write_board` refresh in `workflow`/`generation`, not duplicated in `io`.
- **Metric hotspot persists** — line split may not drop cyclomatic rank on `propose_from_scan` until a follow-up decomposes proposal kinds.

## Out of scope

- Changing ticket semantics, fingerprint rules, criteria gates, or board/Kanban format.
- Updating consumer imports to submodule paths (`from repo_scan.tickets.workflow import …`).
- Further splitting `propose_from_scan` into per-signal-kind functions.
- Hub UI split (tkt-0025 is spec-only; `hub/ui.py` still monolith) or import-linter CI contracts.
- Rescan-driven ticket auto-close for this refactor (merge + rescan is post-PR verification).

## Audit

> [!warning] Audit verdict: revise
> The split boundaries, ≤300 cap feasibility, facade re-export strategy, and lazy-import cycle breaks are sound, but the spec needs corrected line counts, a complete import graph, fixable `now_date` binding guidance, and explicit `__init__.py` import-order risk before human review.
> - Stale line count: the problem statement says 654 lines but the spec Goal and the file on disk are 748 lines (`wc -l repo_scan/tickets.py`).
> - Import DAG is incomplete: `generation.auto_close_resolved_proposed` calls `set_ticket_status` and `append_ticket_note`, so `generation → workflow` is required but omitted; `merge.record_merge_verification` also needs `io` (`load_tickets`) in addition to `generation` and `workflow`.
> - `now_date` monkeypatch guidance is wrong for in-package submodules: `from .. import tickets` from `repo_scan/tickets/io.py` resolves `repo_scan.tickets`, not the package itself — use `import repo_scan.tickets as tickets_pkg` and call `tickets_pkg.now_date()` at runtime (or equivalent deferred lookup).
> - Missing risk: eager `__init__.py` re-exports can load `merge` (and the full submodule graph) on `from repo_scan.tickets import generate_tickets` from `scanner.py`; spec should require import order (e.g. bind `now_date` first) or lazy merge re-export to avoid init-time surprises.
> - Missing risk: adding `now_date` to `__all__` expands the documented public surface beyond today's module (it is only imported from `utils`, not re-exported today); justify explicitly or confirm no downstream `from repo_scan.tickets import now_date` consumers beyond monkeypatch.
> - Unjustified precedent claim in linked research analysis: tkt-0025 UI split is spec-only on main (`hub/ui.py` is still ~784 lines; no `hub/ui/` package, no line-cap test landed) — do not cite it as validated in-repo precedent for this work.
> - Minor sizing inflation in research (~175 lines for parse/card vs ~120 lines at lines 57–176); not blocking but understates how much headroom `parse.py` actually has.

## Provenance

- analysis: [[2026-06-10-split-repo-scan-tickets-py-654-lines-rep-analysis]]
