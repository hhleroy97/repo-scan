---
type: "spec"
problem: "Refactor tests/test_radar_pipeline.py (CC 19, 4 commits, untested)"
status: "draft"
analysis: "[[2026-06-10-refactor-tests-test-radar-pipeline-py-cc-analysis]]"
drafted_at: "2026-06-10 07:30 UTC"
---

## Goal

Lower cyclomatic complexity in `tests/test_radar_pipeline.py` so every function is below radon rank C (CC ≤ 10), without changing radar loop behavior under test. The sole hotspot is `test_loop_happy_path_auto_gates` (CC 19, rank C); helpers and the four sibling scenario tests are already rank A/B. Preserve the module’s role as an offline, deterministic characterization of the full radar artifact graph.

## Approach

Follow PyNose smell guidance (Assertion Roulette, Eager Test) and UTRefactor’s stepwise Extract Method pattern—behavior-preserving refactors with a green pytest gate after each helper extraction, not a one-shot rewrite.

**Phase 1 — Baseline.** Record pre-refactor radon output for `tests/test_radar_pipeline.py` and `docs/scan.json` → `complexity.cc_by_file["tests/test_radar_pipeline.py"]` (currently 19). Run `pytest tests/test_radar_pipeline.py tests/test_hub.py` green.

**Phase 2 — Extract assertion helpers.** In `test_loop_happy_path_auto_gates`, replace inline assertion clusters with private module-level helpers (one commit per helper or small group):

- `assert_approved_spec(docs: Path) -> Path` — single spec file, `status: approved`, goal text, audit pass banner.
- `assert_analysis_confidence(docs: Path) -> Path` — single analysis file, `confidence: high`.
- `assert_provenance_cluster(docs: Path, spec_stem: str, analysis_stem: str)` — wikilinks among spec, analysis, run log, decisions; evidence link to source; stem disambiguation.
- `assert_loop_changelog(docs: Path)` — one loop log, approved outcome, gate pass lines.
- `assert_decisions_auto_rows(docs: Path, count: int = 2)` — decisions table auto rows.

The test body becomes: run `cmd_loop`, assert `rc == 0`, then call helpers in order. Do not split the happy-path into new test files or weaken integration coverage.

**Phase 3 — Verify.** Radon per-function gate, full pytest (including hub import surface), dogfood re-scan with trend delta vs Phase 1 baseline.

## Changes

- **`tests/test_radar_pipeline.py`** — Add private `assert_*` helpers above `test_loop_happy_path_auto_gates`; slim the test to orchestration + helper calls. Leave `FAKE_LLM`, `queue_responses`, `loop_env`, `happy_path_responses`, and the four other tests unchanged unless CC gate requires a trivial trim.
- **`tests/test_hub.py`** — No changes expected; continues importing `FAKE_LLM`, `happy_path_responses`, `queue_responses` from `tests.test_radar_pipeline`.
- **`tests/conftest.py` / `tests/radar_fixtures.py`** — Out of scope unless fixture relocation is needed; if moved, update `test_hub.py` imports in the same commit.
- **`docs/reports/health.md`, `docs/scan.json`** — Updated by post-refactor self-scan (Phase 3), not hand-edited.

## Tests

Acceptance criteria map to automated verification as follows:

| Criterion | Verification |
|-----------|--------------|
| Complexity of every function below rank C | `radon cc -s -a tests/test_radar_pipeline.py` — no function at rank C or worse; specifically `test_loop_happy_path_auto_gates` CC ≤ 10. |
| Test file exists and passes | `pytest tests/test_radar_pipeline.py` — all five tests green: `test_loop_happy_path_auto_gates`, `test_loop_pauses_at_gate1_noninteractive`, `test_loop_resumes_with_approve`, `test_loop_revision_round`, `test_loop_fails_cleanly_without_backend`. |
| Trend delta confirms complexity drop | Capture baseline `complexity.cc_by_file["tests/test_radar_pipeline.py"]` (19) and `reports/health.md` hotspot row before edits; after refactor run `repo-scan` on this repo and assert `cc_by_file` for `tests/test_radar_pipeline.py` is 0 (no rank-C+ functions) and health hotspot list no longer cites `test_loop_happy_path_auto_gates`. |

**Regression surface (must stay green throughout):** `pytest tests/test_hub.py` — hub tests depend on shared fake-LLM helpers imported from this module.

## Documentation

- **`tests/test_radar_pipeline.py` module docstring** — Add one line noting assertion helpers exist to keep the happy-path integration test readable (PyNose Assertion Roulette fix); no README change required.
- **Helper docstrings** — One-line purpose per `assert_*` helper (which artifact cluster it validates); no user-facing docs changes.

## Risks

- Extracting helpers without moving assertions yields churn but no CC drop—each helper must absorb the paths radon counts inside the test body.
- Over-generic provenance helpers can recreate Assertion Roulette and obscure which artifact failed.
- Relocating `FAKE_LLM` / `queue_responses` / `happy_path_responses` breaks `tests/test_hub.py` unless imports are updated atomically.
- Splitting the happy path into many micro-tests could satisfy radon while weakening the integration characterization this module provides.
- Re-scanning after edits mutates `docs/scan.json`; compare against Phase 1 baseline, not post-hoc trend alone.

## Out of scope

- New production code or changes to `repo_scan/radar/pipeline.py`.
- Fixing the repo-scan “untested” mapping (test file exercising production without a paired `test_*.py` mirror)—ticket wording is a coverage signal, not a missing file.
- Moving fixtures to `conftest.py` unless required for CC (prefer in-module helpers).
- Rank-B optimization of already-compliant helpers (`queue_responses`, `loop_env`, etc.).
- New syrupy snapshots or duplicate characterization in a separate test module.

## Provenance

- analysis: [[2026-06-10-refactor-tests-test-radar-pipeline-py-cc-analysis]]
