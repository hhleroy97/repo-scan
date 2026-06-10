---
type: "spec"
problem: "Hidden seam: pyproject.toml <-> setup.py (100% coupled). `pyproject.toml` and `setup.py` changed together in 5 commits (100% degree) but share no import edge — an implicit contract the dependency graph can't see. Acceptance criteria: Make the dependency explicit (shared module or import); Coupling degree drops below threshold in coupling.md. Research current best practices and draft a spec for this work."
status: "approved"
audit_verdict: "revise"
analysis: "[[2026-06-10-hidden-seam-pyproject-toml-setup-py-100-analysis]]"
drafted_at: "2026-06-10 06:55 UTC"
---

# Spec — Hidden seam: pyproject.toml <-> setup.py (100% coupled). `pyproject.toml` and `setup.py` changed together in 5 commits (100% degree) but share no import edge — an implicit contract the dependency graph can't see. Acceptance criteria: Make the dependency explicit (shared module or import); Coupling degree drops below threshold in coupling.md. Research current best practices and draft a spec for this work.
_Drafted 2026-06-10 06:55 UTC by radar — **status: approved**_

I'll pull the current spec, ticket, coupling report, and degree formula so the revision matches real files and tests.
---
type: "spec"
problem: "Hidden seam: pyproject.toml <-> setup.py (100% coupled). Make the dependency explicit; coupling degree drops below threshold in coupling.md."
status: "draft"
analysis: "[[2026-06-10-hidden-seam-pyproject-toml-setup-py-100-analysis]]"
drafted_at: "2026-06-10 07:00 UTC"
---

## Goal

Remove the implicit `pyproject.toml` ↔ `setup.py` packaging contract by deleting redundant `setup.py` and making `pyproject.toml` the sole install manifest, per PyPA modernization guidance. Close tkt-0007: no hidden seam in `docs/reports/coupling.md` (currently 7 shared commits, 100% degree), installs unchanged.

## Approach

`setup.py` mirrors core packaging fields already in `pyproject.toml` (name, version, packages, scripts, python_requires, dev extras) but lacks `[project]` fields such as `description`; metadata is parallel, not byte-identical. CI installs via `pip install -e ".[dev]"` and never invokes `setup.py`. The hidden-seam detector only sees Python import edges, so no refactor can add an import between TOML and Python while both files exist—historical coupling (`degree = round(100 * shared / ((revs[a] + revs[b]) / 2))` per `repo_scan/behavior.py`) would remain 100% even if metadata were frozen. Retaining `setup.py` while single-sourcing into `pyproject.toml` would not satisfy the ticket: the pair would still appear at 100% with no import edge. Deleting `setup.py` removes the file from `analyze_history()`'s tracked set, eliminating the pair. The explicit contract becomes: all packaging metadata lives in `pyproject.toml` under PEP 517 `setuptools.build_meta`.

**AC reinterpretation:** tkt-0007's first criterion ("shared module or import") cannot be met literally for a TOML↔Python seam. Remediation is pyproject-only packaging (delete `setup.py`); amend tkt-0007 AC to "single explicit manifest (`pyproject.toml` only)" so reviewers see the deliberate scope change.

## Changes

- **`setup.py`** — delete.
- **`pyproject.toml`** — no functional change required; confirm `[project]`, `[project.scripts]`, `[project.optional-dependencies]`, and `[tool.setuptools].packages` cover everything formerly in `setup.py`.
- **`tests/test_packaging.py`** (new) — packaging manifest and coupling tests (see Tests).
- **Regenerated scan docs** — after deletion, run `repo-scan` on this repo and commit: `docs/scan.json`, `docs/index.md`, `docs/digest.md`, `docs/reports/coupling.md`, `docs/reports/health.md`.
- **`docs/tickets/tkt-0007.md`** — amend AC wording; check boxes when done.
- **`.github/workflows/ci.yml`** — no change.

Do **not** change `repo_scan/identity.py` manifest detection.

## Tests

| Acceptance criterion | Automated test |
|---|---|
| Single explicit manifest (amended AC; was "shared module or import") | `test_packaging.py::test_packaging_manifest_is_pyproject_only` — assert `setup.py` absent; parse `pyproject.toml` and verify `name`, `version`, `requires-python`, `project.scripts`, `tool.setuptools.packages`, and `optional-dependencies.dev` match prior `setup.py` contract |
| Coupling degree below threshold | `test_packaging.py::test_hidden_seam_absent_after_setup_removal` — temp git fixture with `pyproject.toml` only (no `setup.py`); call `analyze_history` + `hidden_seams` directly; assert no `pyproject.toml` ↔ `setup.py` pair. Do **not** scan the live repo root in pytest (would rewrite committed `docs/`). |
| Install regression | `test_packaging.py::test_console_scripts_registered` — entry points for `repo-scan` and `radar` |

## Documentation

- **`README.md`** — update Install section (drop `setup.py develop` framing; state pyproject-only packaging).
- **`tkt-0007.md`** — note remediation and amended AC.
- Regenerated **`docs/index.md`**, **`docs/digest.md`**, **`docs/scan.json`**, **`docs/reports/coupling.md`**, **`docs/reports/health.md`** after rescan.

## Risks

Legacy `python setup.py` workflows break; version still duplicated in `config.py`; snapshot tests may need refresh.

## Out of scope

Dynamic version from `repo_scan.config.VERSION`, the scanner↔writers seam, coupling-threshold changes, and removing `setup.py` detection for other repos.

## Provenance

- Live baseline: `docs/reports/coupling.md` — 7 shared commits, 100% degree (not tkt-0007's stale "5 commits").
- analysis: [[2026-06-10-hidden-seam-pyproject-toml-setup-py-100-analysis]] — metadata parallel, not duplicate; single-sourcing with `setup.py` retained does not remove the seam.
- ticket: [[tkt-0007]]

## Audit

> [!warning] Audit verdict: revise
> Delete-setup.py is the right PyPA-aligned fix and the fixture-based coupling test is sound, but revise the false freezing/degree claim, reconcile AC wording with the approved ticket, and tighten AC2 verification before human review.
> - Approach claims freezing metadata keeps coupling at 100%, but behavior.py uses degree = round(100 * shared / ((revs[a] + revs[b]) / 2)); if setup.py stops changing while pyproject.toml keeps accruing commits, shared stays fixed and degree falls — eventual drop below the 50% threshold is possible without deletion.
> - Approach says setup.py metadata is 'parallel, not byte-identical,' but the linked analysis states 'byte-for-byte duplicate'; the spec should correct or qualify the analysis finding (different syntax: entry_points vs project.scripts, no description in setup.py).
> - AC1 remediation (delete setup.py) does not satisfy the literal ticket criterion 'shared module or import'; the proposed AC reinterpretation is reasonable but conflicts with unchanged tkt-0007 wording, spec frontmatter problem text, and tickets.py's auto-generated criteria template — call out explicit human reviewer approval for the AC scope change.
> - AC2 is only exercised indirectly: test_hidden_seam_absent_after_setup_removal uses a temp fixture (good), but no test asserts the committed docs/reports/coupling.md artifact after rescan — compliance depends entirely on the manual regen commit listed under Changes.
> - Goal states 'installs unchanged' while Risks admit python setup.py workflows break; narrow to 'pip install -e .[dev] unchanged' to avoid overstating parity.
> - Risks cite snapshot refresh (test_scanner_snapshots, test_writers_snapshots) for setup.py paths, but current syrupy snapshots contain no setup.py references — low-probability risk should be dropped or demoted.
> - Provenance correctly notes 7 shared commits in coupling.md vs ticket's stale '5 commits,' but the spec should also note that post-rescan generate_tickets() will mark tkt-0007 fingerprint seam:pyproject.toml+setup.py as metrics-resolved on the board — closing workflow should be explicit.

## Provenance

- analysis: [[2026-06-10-hidden-seam-pyproject-toml-setup-py-100-analysis]]
