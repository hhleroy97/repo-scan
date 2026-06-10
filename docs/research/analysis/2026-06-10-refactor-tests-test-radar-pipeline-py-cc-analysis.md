---
type: "analysis"
problem: "Refactor tests/test_radar_pipeline.py (CC 19, 4 commits, untested). `tests/test_radar_pipeline.py` is both high-churn (4 commits) and high-complexity (total CC 19) with no matching test file. Acceptance criteria: Complexity of every function below rank C; Test file exists and passes; Trend delta confirms complexity drop. Research current best practices and draft a spec for this work."
confidence: "high"
sources: ["gh-JetBrains-Research-PyNose", "arxiv-2409.16739"]
generated_at: "2026-06-10 07:01 UTC"
linked_files: ["tests/conftest.py", "tests/test_hub.py", "tests/test_radar_pipeline.py"]
---

# Analysis — Refactor tests/test_radar_pipeline.py (CC 19, 4 commits, untested). `tests/test_radar_pipeline.py` is both high-churn (4 commits) and high-complexity (total CC 19) with no matching test file. Acceptance criteria: Complexity of every function below rank C; Test file exists and passes; Trend delta confirms complexity drop. Research current best practices and draft a spec for this work.
_Generated 2026-06-10 07:01 UTC — confidence: high_

## Findings

- All CC 19 is isolated to `test_loop_happy_path_auto_gates` (radon rank C); other functions (`queue_responses`, `loop_env`, `happy_path_responses`, and the four smaller tests) are already rank A/B, so the refactor target is one test body, not the whole module.
- PyNose maps this hotspot to Assertion Roulette: ~15 sequential assertions over spec, analysis, provenance wikilinks, changelog, and decisions with no named sub-behaviors, which inflates cyclomatic complexity without adding branching logic.
- The happy-path test is also an Eager Test in PyNose terms—it validates the full radar artifact graph in one case—so extracting focused assertion helpers (e.g. `assert_approved_spec`, `assert_provenance_cluster`, `assert_loop_outcome`) is the canonical smell fix, not splitting scenarios across new test files.
- `test_hub.py` already imports `FAKE_LLM`, `happy_path_responses`, and `queue_responses` from this module; any fixture relocation must preserve that public test-helper surface or update dependents in the same change.
- UTRefactor’s empirical lesson applies even without LLMs: treat smell removal as stepwise, behavior-preserving Extract Method refactors with a green pytest gate after each step, rather than a one-shot rewrite that risks dropping assertions.
- Ticket wording “no matching test file” is a repo-scan coverage signal (test code not mapped to production under test), not a missing file—the acceptance criterion “test file exists and passes” is already met and must stay green throughout.
- Sibling refactor specs in this repo (scanner, graphs, languages) gate completion on radon per-function rank ≤ C (CC ≤ 10), full pytest, and a self-scan trend delta in `docs/reports/health.md` / `docs/scan.json`; the same verification loop fits this ticket.

## Recommendation

Run pytest green as baseline, then lower CC in `test_loop_happy_path_auto_gates` by extracting pure assertion helpers for each artifact cluster (spec approval, analysis confidence, provenance wikilinks, changelog outcome, decisions rows) while leaving scenario tests and shared fake-LLM queue fixtures behavior-identical. Optionally move shared fixtures to `tests/conftest.py` or a small `tests/radar_fixtures.py` only if imports from `test_hub.py` are updated atomically. Close the ticket only when radon reports every function below rank C, `pytest tests/test_radar_pipeline.py` (and dependent hub tests) pass, and a fresh repo-scan shows reduced CC/trend delta for `tests/test_radar_pipeline.py`.

## Risks

- Extracting helpers without relocating assertions yields higher churn but no CC drop—helpers must absorb the conditional paths currently counted inside the test function.
- Over-abstracting provenance checks into generic helpers can recreate Assertion Roulette at the helper layer or obscure which artifact failed on regression.
- Moving `FAKE_LLM` / `happy_path_responses` / `queue_responses` breaks `tests/test_hub.py` unless import paths are updated in the same commit.
- Aggressive splitting of the happy-path scenario into many micro-tests could satisfy radon while weakening the integration characterization the module is meant to provide.

## Evidence

- [[gh-JetBrains-Research-PyNose\|JetBrains-Research/PyNose — A test smell detector for Python.]]
- [[arxiv-2409.16739\|Automated Unit Test Refactoring]]
- research run: [[2026-06-10-refactor-tests-test-radar-pipeline-py-cc]]
