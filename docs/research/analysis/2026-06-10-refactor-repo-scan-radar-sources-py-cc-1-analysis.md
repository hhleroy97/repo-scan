---
type: "analysis"
problem: "Refactor repo_scan/radar/sources.py (CC 14, 3 commits, untested). `repo_scan/radar/sources.py` is both high-churn (3 commits) and high-complexity (total CC 14) with no matching test file. Acceptance criteria: Complexity of every function below rank C; Test file exists and passes; Trend delta confirms complexity drop. Research current best practices and draft a spec for this work."
confidence: "high"
sources: ["url-refactoring-com-catalog-splitloop-html"]
generated_at: "2026-06-10 07:35 UTC"
---

# Analysis — Refactor repo_scan/radar/sources.py (CC 14, 3 commits, untested). `repo_scan/radar/sources.py` is both high-churn (3 commits) and high-complexity (total CC 14) with no matching test file. Acceptance criteria: Complexity of every function below rank C; Test file exists and passes; Trend delta confirms complexity drop. Research current best practices and draft a spec for this work.
_Generated 2026-06-10 07:35 UTC — confidence: high_

## Findings

- Radon confirms all file CC 14 is isolated to `rebuild_research_index` (rank C, CC 14); every other function is rank B or better, with `write_source` at the B ceiling (CC 10) and the rest at rank A.
- The ticket's 'untested' flag is a `tests_map.py` stem heuristic (`sources` not in `test_radar_ingest`); seven behavioral tests already live in `tests/test_radar_ingest.py` (frontmatter roundtrip, write/parse source, notes preservation, index/tags rebuild), so Phase 1 is extend-and-rename, not greenfield characterization.
- `rebuild_research_index` is a Split Loop candidate: one function collects entries, sorts, renders the index table (with title truncation), builds a tag map (nested entry→tag loop), and renders `tags.md` (nested tag→entry loop)—four independent passes over the same collection that Fowler's Split Loop pattern says should become named helpers.
- Repo precedent (languages, scanner, writers, test_radar_pipeline specs) is snapshot/characterization tests first, then Extract Method one helper per commit, `radon cc -s -a` after each step, and trend verification against a pre-edit `docs/scan.json` baseline—not a post-hoc re-scan alone.
- Acceptance 'every function below rank C' means CC ≤ 10 (rank B or better); only `rebuild_research_index` must change for complexity, though `write_source` should not gain branches during the refactor.
- Coverage gaps to close in a dedicated `tests/test_sources.py`: long-title truncation in the index table (>90 chars), tag grouping when one source has multiple tags, and `parse_frontmatter` edge cases (missing block, malformed lines)—happy-path rebuild is covered but not these branches.
- Downstream contracts are narrow and stable: `rebuild_research_index` is called from `radar/cli.py` and `radar/research.py`; markdown must preserve Obsidian wikilink escaping (`[[sources/{id}\|{title}]]`), slugified tags, and `write_source` notes preservation above `## Notes`.
- Performance tradeoff of Split Loop is negligible here—source counts are small (tens of files), so extra traversals buy clarity without measurable cost.

## Recommendation

Create `tests/test_sources.py` by migrating and extending existing `test_radar_ingest.py` source tests (add title-truncation and multi-tag cases), then refactor `rebuild_research_index` via Split Loop into pure private helpers—e.g. `_collect_source_entries`, `_render_index_markdown`, `_build_tag_map`, `_render_tags_markdown`—leaving a thin coordinator. Capture pre-refactor radon output and `docs/scan.json` complexity rows for `repo_scan/radar/sources.py`, extract one helper per commit with full pytest green, and close with `radon cc -s -a` showing no function at rank C or worse plus a self-scan trend delta (derived `cc_by_file` drops from 14, health hotspot row for `rebuild_research_index` clears).

## Risks

- Extracting helpers without relocating the branches radon counts inside `rebuild_research_index` yields churn but no CC drop—each helper must absorb the conditional paths (empty entries, title truncation, per-tag iteration).
- Obsidian markdown escaping in index/tags output is brittle; any helper split that reformats wikilinks or tag sections will fail existing ingest tests or break Obsidian graph links.
- Moving tests from `test_radar_ingest.py` to `test_sources.py` satisfies the ticket heuristic but may leave fetch-parser tests orphaned unless imports are updated deliberately.
- `write_source` at CC 10 is one branch from rank C; incidental edits during the same PR could create a second hotspot.
- Trend verification must compare against a Phase 1 baseline snapshot; re-scanning only after edits mutates `docs/scan.json` and can obscure the before/after delta the ticket requires.

## Evidence

- [[url-refactoring-com-catalog-splitloop-html\|Split Loop]]
- research run: [[2026-06-10-refactor-repo-scan-radar-sources-py-cc-1]]
