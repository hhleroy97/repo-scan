---
type: "spec"
problem: "Hidden seam: repo_scan/radar/cli.py <-> repo_scan/radar/gates.py (80% coupled). `repo_scan/radar/cli.py` and `repo_scan/radar/gates.py` changed together in 4 commits (80% degree) but share no import edge — an implicit contract the dependency graph can't see. Acceptance criteria: Make the dependency explicit (shared module or import); Coupling degree drops below threshold in coupling.md. Research current best practices and draft a spec for this work."
status: "approved"
audit_verdict: "revise"
analysis: "[[2026-06-10-hidden-seam-repo-scan-radar-cli-py-repo-analysis]]"
drafted_at: "2026-06-10 17:42 UTC"
linked_files: ["repo_scan/radar/cli.py", "repo_scan/radar/gates.py", "tests/test_behavior.py", "tests/test_radar_cli_gates.py", "tests/test_radar_full.py"]
---

# Spec — Hidden seam: repo_scan/radar/cli.py <-> repo_scan/radar/gates.py (80% coupled). `repo_scan/radar/cli.py` and `repo_scan/radar/gates.py` changed together in 4 commits (80% degree) but share no import edge — an implicit contract the dependency graph can't see. Acceptance criteria: Make the dependency explicit (shared module or import); Coupling degree drops below threshold in coupling.md. Research current best practices and draft a spec for this work.
_Drafted 2026-06-10 17:42 UTC by radar — **status: approved**_

Grounding the revision in the codebase and the audit findings.
## Goal

Close tkt-0015: eliminate connascence of meaning between `repo_scan/radar/cli.py` and `repo_scan/radar/gates.py` by making the gate vocabulary a single named source. **Baseline (live scan):** 4 shared commits, 80% degree, import edge **none**. **AC1 (merge-gated):** `cli` imports `gates` (visible in dep graph); argparse surface derives from exported constants; hidden-seam warning clears for this pair. **AC2 (history-gated):** change-coupling degree strictly below `coupling_min_degree` (50%) — pair **absent** from `coupling.md` / `analyze_history` output, not “listed below 50%”. **Human reviewer:** amend ticket AC wording per tkt-0016 precedent — AC2 may remain open post-merge until divergent history + rescan.

## Approach

Vocabulary coupling, not missing runtime logic. `pipeline.py` and `act.py` already import `gates`; `cli.py` hard-codes gate names in `--approve` help and mode literals in `--gates choices`. Weaken meaning coupling to **connascence of name** via shared symbols. Deduplicate argparse via `parents=[...]` built from those symbols. **`act` has no `--gates` today and `cmd_act` accepts no `gates_override`** — do not add `--gates` to `act` in this ticket.

1. **Extend `gates.py`** — export `GATE_MODES = ("prompt", "auto", "deny")`; derive `LOOP_GATE_NAMES` / `ACT_GATE_NAMES` as named slices of `GATE_NAMES`; refactor `gate_mode()` to validate against `GATE_MODES`. Add `gate_cli_parent(*, approve_help: str | None = None, include_gates: bool = True) -> argparse.ArgumentParser` that returns a **new** `ArgumentParser` per call (reuse across subparsers breaks argparse) and registers `--approve` plus optional `--gates` from tuples only.
2. **Refactor `cli.py`** — eager `from .gates import ...` at module load (all radar subcommands); attach fresh `parents=[gate_cli_parent(...)]` per gate-bearing subcommand: `loop` — `approve_help` cites `LOOP_GATE_NAMES`, `include_gates=True`; `full` — `approve_help=None` (preserve today’s generic metavar, no gate names in help), `include_gates=True`; `act` — `approve_help` cites `ACT_GATE_NAMES`, `include_gates=False`. Remove inline gate/mode literals.
3. **Rescan** — after merge, run `repo-scan`; commit regenerated artifacts when ready. AC2 on live repo needs post-refactor commits touching **only** `cli.py` or **only** `gates.py` — co-touch refactor adds shared history; plan solo-side volume per fixture math below, not “≥2” commits.

## Changes

- **`repo_scan/radar/gates.py`** — `GATE_MODES`; `LOOP_GATE_NAMES`, `ACT_GATE_NAMES`; `gate_mode()` uses `GATE_MODES`; `gate_cli_parent(approve_help, include_gates)`.
- **`repo_scan/radar/cli.py`** — import gate vocabulary; shared parent on `loop`, `full`, `act` with per-subcommand flags above; no `--gates` on `act`.
- **`tests/test_radar_gates.py`** — `GATE_MODES`, slices, `gate_cli_parent` choices / `include_gates=False` omits `--gates`.
- **`tests/test_radar_cli_gates.py`** (new) — import-edge and argparse contract tests only.
- **`tests/test_report_pipeline.py`** — `test_cli_gates_degree_below_threshold` (sole owner for degree fixture).
- **Regenerated docs** — `docs/reports/coupling.md`, `docs/scan.json`, dependency-graph artifacts after rescan.
- **`docs/tickets/tkt-0015.md`** — baseline 80%/4 shared; AC1 merge-gated / AC2 history-gated; reviewer sign-off that AC2 may stay open post-merge.

Do **not** move `gate()` into `cli.py`; do **not** wire `gates_override` through `act.py`; do **not** add `gate_schema` unless tkt-0017 needs it.

## Tests

| Acceptance criterion | Automated test |
|---|---|
| Explicit import | `tests/test_radar_cli_gates.py::test_cli_imports_gates_resolves_dep_edge` — fixture tree with `from .gates import ...`; `get_python_dep_edges` yields `(repo_scan.radar.cli, repo_scan.radar.gates)`. |
| Shared vocabulary | `tests/test_radar_cli_gates.py::test_gate_cli_parent_choices_match_gate_modes` — `--gates` choices = `GATE_MODES`; loop/act `approve_help` contains only `LOOP_GATE_NAMES` / `ACT_GATE_NAMES`; `include_gates=False` has no `--gates` action; each parent is a distinct parser instance. |
| Hidden seam cleared | `tests/test_behavior.py::test_hidden_seams_excludes_imported_pairs` — extend/assert `cli.py`↔`gates.py` excluded when dotted import edge present. |
| Degree below threshold | `tests/test_report_pipeline.py::test_cli_gates_degree_below_threshold` — mirror `test_scanner_writers_degree_below_threshold`: **4** pair commits (~80%), then **≥3** gates-only + **≥6** cli-only (solo-side only); `analyze_history` → pair absent. No live-repo root. |
| Degree below threshold | Post-rescan (manual, after sufficient live solo-side history): `cli.py`↔`gates.py` **absent** from coupling table and hidden-seam warning; import edge **yes** in dep graph. |
| No regression | `tests/test_radar_full.py::test_radar_cli_e2e_loop` — unchanged pass with auto gates. |

## Documentation

- **`repo_scan/radar/gates.py` docstring** — `GATE_NAMES`, `GATE_MODES`, `LOOP_GATE_NAMES`, `ACT_GATE_NAMES`, `gate_cli_parent` are canonical CLI vocabulary; `cli.py` must not duplicate literals.
- **`repo_scan/radar/cli.py` docstring** — argparse façade; gate flags sourced from `gates`.
- **`README.md`** — only if radar CLI section quotes gate names literally.
- **`docs/tickets/tkt-0015.md`** — AC split + post-merge AC2 note.
- Regenerated **`docs/reports/coupling.md`** after rescan.

## Risks

- Eager `gates` import in `cli.py` loads the gate module for **every** radar subcommand (`ingest`, `serve`, `daemon`, …), not only `loop`/`full`/`act` — `hub.state` stays lazy inside `gate()`, but startup surface is wider than gate commands alone.
- `gate_cli_parent` in `gates.py` mixes CLI argparse with runtime gate logic — keep to constants + `add_argument` only.
- Landing refactor co-touches `cli`+`gates`, worsening AC2 math until sufficient solo-side commits land.
- Exactly 50% degree still emits the pair — fixture must prove **strictly** &lt; 50%.
- Parallel tkt-0017 (`gates`↔`pipeline`) may later share `GATE_MODES`; keep this ticket scoped to `cli`↔`gates` only.

## Out of scope

`--gates` on `act` / `gates_override` in `cmd_act`, gate execution semantics, `pipeline.py` / `act.py` refactors, hub/dashboard gate UX, tkt-0017, changing `coupling_min_degree` / `coupling_min_shared`, other hidden seams, standalone `gate_schema` module.

## Audit

> [!warning] Audit verdict: revise
> The spec is well-grounded in live coupling.md (4 shared, 80%, no edge) and the right remediation (cli→gates import + shared vocabulary), but AC1/AC2 timing, post-refactor degree math, and argparse-parent details need tightening before human review.
> - AC2 solo-side volume is understated after the landing co-touch: fixture math (4 pair + ≥3 gates-only + ≥6 cli-only → 47%) omits the refactor commit that raises shared to 5 and degree to ~53%; post-merge live history needs roughly ≥2 additional solo-side commits beyond the cited ≥3/≥6 (per tkt-0016/hub-server precedent), but the spec only flags this generically in Risks.
> - AC1 says the hidden-seam warning clears at merge, but that warning lives in generated coupling.md; an import edge alone does not update committed artifacts until rescan—clarify whether AC1 requires a rescan commit or only that the next scan will drop cli↔gates from the hidden-seam block while the pair may still appear in the table at high degree.
> - Manual post-rescan AC2 row bundles 'absent from coupling table and hidden-seam warning'; after AC1/rescan with an import edge, hidden-seam clearance and sub-50% coupling absence are independent metrics (cf. scanner↔writers at 50% with import yes still in the table).
> - git fixture section does not state whether the landing refactor co-touch commit is included; scanner↔writers fixture uses a different decouple pattern—reviewers cannot tell if test_cli_gates_degree_below_threshold models pre-refactor theory only or post-landing history.
> - gate_cli_parent() spec omits argparse parent requirements (typically add_help=False on the parent parser); without this, loop/full/act subparsers risk duplicate -h handling—missing implementation risk for a core approach item.
> - Regenerated-docs list (coupling.md, scan.json, dependency-graph) is narrower than sibling hidden-seam specs (tkt-0016 also names health.md, dependencies.md, index/digest); unclear whether a full repo-scan artifact set is in scope.
> - LOOP_GATE_NAMES / ACT_GATE_NAMES as positional slices of GATE_NAMES inherit reorder risk if GATE_NAMES ever changes—worth a one-line risk; analysis incorrectly groups full with loop on gate help, though the spec's approve_help=None for full matches current cli.py.

## Provenance

- analysis: [[2026-06-10-hidden-seam-repo-scan-radar-cli-py-repo-analysis]]
