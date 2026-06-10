---
type: "spec"
problem: "Refactor repo_scan/radar/sources.py (CC 14, 3 commits, untested). `repo_scan/radar/sources.py` is both high-churn (3 commits) and high-complexity (total CC 14) with no matching test file. Acceptance criteria: Complexity of every function below rank C; Test file exists and passes; Trend delta confirms complexity drop. Research current best practices and draft a spec for this work."
status: "approved"
audit_verdict: "revise"
analysis: "[[2026-06-10-refactor-repo-scan-radar-sources-py-cc-1-analysis]]"
drafted_at: "2026-06-10 13:10 UTC"
linked_files: ["repo_scan/radar/__init__.py", "repo_scan/radar/cli.py", "repo_scan/radar/research.py", "repo_scan/radar/sources.py", "tests/test_radar_ingest.py"]
---

# Spec — Refactor repo_scan/radar/sources.py (CC 14, 3 commits, untested). `repo_scan/radar/sources.py` is both high-churn (3 commits) and high-complexity (total CC 14) with no matching test file. Acceptance criteria: Complexity of every function below rank C; Test file exists and passes; Trend delta confirms complexity drop. Research current best practices and draft a spec for this work.
_Drafted 2026-06-10 13:10 UTC by radar — **status: approved**_

Reviewing the codebase so the revised spec matches repo conventions and addresses every audit issue.
Drafting the revised spec with all audit fixes, keeping it under 80 lines.
## Goal

Lower cyclomatic complexity in `repo_scan/radar/sources.py` so every function is radon rank B or better (CC ≤ 10). The sole rank-C hotspot is `rebuild_research_index` (CC 14); `write_source` is at the B ceiling (CC 10) and must not regress. Preserve public signatures and downstream contracts: `radar/cli.py` and `radar/research.py` call `write_source` / `rebuild_research_index` unchanged; markdown must keep Obsidian wikilink escaping (`[[sources/{id}\|{title}]]`), slugified tags, and `## Notes` preservation in `write_source`.

## Approach

Follow the repo's characterization-then-extract precedent (writers, scanner, languages, `test_radar_pipeline`): baseline first, extend coverage, then Fowler Split Loop on `rebuild_research_index` into pure private helpers with a thin coordinator.

**Phase 0 — Baseline (before any edits).** Run `radon cc -s -a repo_scan/radar/sources.py`. Copy `docs/scan.json` to a safe path outside `docs/` (e.g. `/tmp/sources-cc-baseline.json`). From that copy, derive `cc_by_file` for `repo_scan/radar/sources.py` by summing `complexity[]` rows (currently 14; sums rank-C+ only—`write_source` at CC 10 is excluded). Snapshot `docs/reports/health.md` hotspot row for `rebuild_research_index`. Avoid dogfood re-scans until Phase 3.

**Phase 1 — Tests (no production refactor).** Create `tests/test_sources.py` by migrating seven source-related tests from `tests/test_radar_ingest.py` and adding branch coverage for title truncation (>90 chars), multi-tag grouping, and `parse_frontmatter` edge cases. Leave fetch-parser tests in `test_radar_ingest.py`. Commit green against current code.

**Phase 2 — Split Loop.** Extract one helper per commit; full pytest after each. Each helper must own the branches radon counts (not cosmetic loop moves). If any helper still ranks C, sub-split before proceeding—`_render_tags_markdown` is the likely candidate (nested tag/source loops); same contingency as languages/graphs specs.

1. `_collect_source_entries(sources_dir: Path) -> list[dict]` — `sorted(glob("*.md"))`, parse, stable sort by `ingested_at` desc (equal timestamps retain filename order).
2. `_render_index_markdown(entries: list[dict]) -> str` — `# Research index` + `now_iso()` count line; table rows with `[[sources/{id}\|{title}]]` and >90-char truncation; empty `| _none yet … |` row.
3. `_build_tag_map(entries: list[dict]) -> dict[str, list[dict]]` — comma-split tags, group by tag.
4. `_render_tags_markdown(tag_map: dict[str, list[dict]]) -> str` — `# Research tags` + `now_iso()`; sorted `##` sections with wikilink bullets; `_no tagged sources yet_` when empty.

`rebuild_research_index`: mkdir → collect → write `research/index.md` → build map → write `research/tags.md`. No signature or observable output changes; do not touch `write_source` unless CC gate forces it (not expected).

**Phase 3 — Verify.** Restore the Phase 0 `scan.json` copy to `docs/scan.json` immediately before the verification dogfood re-scan (`index.md` `cc_movers` diffs prior vs current via `summarize_metrics` on on-disk `docs/scan.json`). Then re-scan. Compare derived `cc_by_file`, `health.md` hotspot row, and `index.md` `cc_movers` against Phase 0—not post-hoc trend alone.

## Changes

- **`tests/test_sources.py`** (new) — Migrated source tests plus truncation, multi-tag, and `parse_frontmatter` edge cases; uses `tmp_repo` from `conftest.py`.
- **`tests/test_radar_ingest.py`** — Remove migrated source imports/tests; retain arxiv/github/file fetch-parser tests only.
- **`repo_scan/radar/sources.py`** — Phase 2 only: four `_`-prefixed helpers; slim `rebuild_research_index`; no signature or observable behavior changes.
- **`repo_scan/radar/cli.py`**, **`repo_scan/radar/research.py`**, **`repo_scan/radar/__init__.py`** — No import or call-site changes expected.
- **`docs/scan.json`**, **`docs/reports/health.md`**, **`docs/index.md`** — Updated by Phase 3 self-scan after baseline restore, not hand-edited.

## Tests

| Acceptance criterion | Automated verification |
|----------------------|------------------------|
| Complexity of every function below rank C | `radon cc -s -a repo_scan/radar/sources.py` — no function rank C+; `rebuild_research_index` and each `_`-helper CC ≤ 10; `write_source` must stay ≤ 10. |
| Test file exists and passes | `pytest tests/test_sources.py` — all tests green (migrated + new). |
| Trend delta confirms complexity drop | Phase 0: derived `cc_by_file` = 14 (rank-C+ sum), `health.md` cites `rebuild_research_index`. Phase 3: after baseline restore + re-scan, derived `cc_by_file` is 0 (no rank-C+ functions remain—accidental `write_source` regression would block this), hotspot row cleared, `index.md` `cc_movers` shows drop vs Phase 0. |

**`tests/test_sources.py` inventory:** Migrated: `test_frontmatter_roundtrip_with_colons_and_lists`, `test_write_source_emits_obsidian_frontmatter`, `test_source_id_for`, `test_write_source_preserves_human_notes`, `test_parse_source_file_roundtrip`, `test_rebuild_research_index`, `test_rebuild_research_index_empty`. New: `test_rebuild_research_index_truncates_long_title`, `test_rebuild_research_index_one_source_multiple_tags`, `test_parse_frontmatter_missing_block`, `test_parse_frontmatter_skips_malformed_lines`.

**Regression surface (green throughout):** `pytest tests/test_sources.py tests/test_radar_ingest.py tests/test_radar_llm.py tests/test_radar_pipeline.py` — direct source contracts (`test_sources`, ingest fetch parsers), `test_run_research_ingests_proposed_file`, and full-loop file ingest via `cmd_loop`.

## Documentation

- **`repo_scan/radar/sources.py` module docstring** — One line on index/tags rebuild helpers if the coordinator is no longer self-explanatory.
- **`rebuild_research_index` docstring** — Note delegated helpers and unchanged output paths.
- **Private helper docstrings** — Brief purpose + inputs/outputs; no README change unless `tests_map` heuristic is documented elsewhere.

## Risks

- **Cosmetic extraction** — Conditionals left in `rebuild_research_index` (headers, wikilinks, empty states) leave rank C; each helper must own its branches.
- **`write_source` regression** — At CC 10; incidental edits could create a second hotspot and prevent `cc_by_file` → 0.
- **Test migration churn** — `sources` ∉ `test_radar_ingest` tokens; update imports deliberately or coverage orphans.
- **Baseline loss** — Mid-refactor re-scans overwrite `docs/scan.json`; Phase 0 copy + Phase 3 restore required for `cc_movers`.
- **Wikilink escaping** — Index/tags assertions must keep `\\|` in expected strings.

## Out of scope

- Replacing stdlib YAML frontmatter with `python-frontmatter` or nested YAML/TOML.
- Refactoring `write_source` (already rank B) or other rank-A/B functions unless CC gate forces it.
- Changing `Source` dataclass fields, `slugify` limits, or `source_id_for` rules.
- Fetch-parser tests in `test_radar_ingest.py` or network/LLM ingest paths beyond listed regression set.
- Performance optimization (source counts are tens of files; extra passes are negligible).
- `scanner.py` / `tests_map.py` heuristic changes beyond natural resolution via `test_sources.py`.

## Audit

> [!warning] Audit verdict: revise
> Well-aligned with radon findings, tkt-0005 acceptance criteria, and sibling audit fixes (scan.json baseline copy, cc_by_file derivation, index.md cc_movers); remaining gaps are helper contracts, precedent wording, and regression/verification completeness rather than goal or scope problems.
> - Phase 3 omits the concrete dogfood scan command (e.g. repo-scan / python -m repo_scan.cli scan) that sibling refactor specs require for reproducible trend verification.
> - _collect_source_entries contract is underspecified: it must return [] when sources_dir is missing or not a directory and must skip files where parse_source_file returns empty meta—behavior currently embedded in rebuild_research_index that a naive Split Loop extraction could drop.
> - Approach cites writers, scanner, languages, and test_radar_pipeline as a uniform characterization-then-extract precedent, but only languages closely matches unit-test-first migration; writers used syrupy snapshots and test_radar_pipeline refactored test code, not production—wording overstates executable precedent.
> - Regression surface lists test_run_research_ingests_proposed_file but omits test_cmd_research_writes_run_log, which also exercises write_source and rebuild_research_index via cmd_research.
> - Changes section does not include updating tests/test_radar_ingest.py module docstring after migrating seven source tests (it still describes source/index coverage the file will no longer own).
> - New test_rebuild_research_index_truncates_long_title should pin expected output for single-token titles >90 chars (current rsplit logic has no word boundary); leaving behavior implicit risks a brittle or ambiguous assertion.
> - Phase 3 baseline-restore assumes no intervening scan.json mutations on the branch beyond this work; the spec warns against mid-refactor scans but does not note that a stale or partially updated baseline confounds cc_movers if other hotspots change concurrently.

## Provenance

- analysis: [[2026-06-10-refactor-repo-scan-radar-sources-py-cc-1-analysis]]
