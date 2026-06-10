# Gate decisions

| When | Gate | Decision | Summary |
|------|------|----------|---------|
| 2026-06-09 23:41 UTC | post_analyze | paused | Do not fully replace the composite heuristic with graph-only PageRank; instead upgrade the structural centrality term fr |
| 2026-06-09 23:46 UTC | post_analyze | approved (--approve) | Do not fully replace the composite heuristic with graph-only PageRank. Instead, upgrade the structural centrality term f |
| 2026-06-09 23:48 UTC | post_audit | paused | audit revise: The spec aligns with the approved analysis and zero-deps constraint, but needs clearer edge-mapping rules, |
| 2026-06-09 23:58 UTC | post_audit | approved (human, with implementation) | [[2026-06-09-should-repo-scan-replace-its-heuristic-i-spec]] — approved at Gate 2; audit issues to be addressed in imple |
| 2026-06-10 01:51 UTC | post_analyze | paused | Before any structural refactor, add syrupy characterization snapshots for every write_* artifact using a fixed fixture r |
| 2026-06-10 01:54 UTC | post_analyze | approved (--approve) | Before any structural refactor, add syrupy characterization snapshots for every write_* artifact using a fixed fixture r |
| 2026-06-10 01:57 UTC | post_audit | paused | audit revise: The phased snapshot-then-extract plan matches the codebase hotspots and ticket intent, but the spec needs  |
| 2026-06-10 02:02 UTC | post_audit | approved | human approved with audit corrections folded into implementation — [[2026-06-10-refactor-repo-scan-writers-py-cc-52-7-co |
| 2026-06-10 03:15 UTC | post_analyze | paused | Follow the Feathers change algorithm and the writers spec precedent: Phase 1 adds characterization tests—a fixed fixture |
| 2026-06-10 03:17 UTC | post_analyze | approved (dashboard) | Follow the Feathers change algorithm and the writers spec precedent: Phase 1 adds characterization tests—a fixed fixture |
| 2026-06-10 03:20 UTC | post_audit | paused | audit revise: The phased snapshot-then-extract shape matches the writers precedent and scanner hotspots, but the spec ne |
| 2026-06-10 03:24 UTC | post_analyze | approved (dashboard) | Follow the Feathers change algorithm and the writers spec precedent: Phase 1 adds characterization tests—a fixed fixture |
| 2026-06-10 03:24 UTC | post_audit | approved (dashboard) | audit revise: The phased snapshot-then-extract shape matches the writers precedent and scanner hotspots, but the spec ne |
| 2026-06-10 03:27 UTC | post_analyze | paused | Follow the established two-phase pattern: first add tests/test_graphs.py with fixture repos covering Python import varia |
| 2026-06-10 03:30 UTC | post_analyze | approved (dashboard) | Follow the established two-phase pattern: first add tests/test_graphs.py with fixture repos covering Python import varia |
| 2026-06-10 03:33 UTC | post_audit | paused | audit revise: Phasing, hotspot metrics, and research-backed ast/madge approach are sound, but radon rank wording is wron |
| 2026-06-10 03:49 UTC | pre_implement | paused | implement [[2026-06-10-refactor-repo-scan-scanner-py-cc-27-8-co-spec]] on branch radar/tkt-0002 for tkt-0002 |
| 2026-06-10 03:51 UTC | post_analyze | approved (dashboard) | Follow the established two-phase pattern: first add tests/test_graphs.py with fixture repos covering Python import varia |
| 2026-06-10 03:51 UTC | post_audit | approved (dashboard) | audit revise: Phasing, hotspot metrics, and research-backed ast/madge approach are sound, but radon rank wording is wron |
| 2026-06-10 03:51 UTC | pre_implement | approved (dashboard) | implement [[2026-06-10-refactor-repo-scan-scanner-py-cc-27-8-co-spec]] on branch radar/tkt-0002 for tkt-0002 |
| 2026-06-10 04:00 UTC | pre_implement | approved (dashboard) | implement [[2026-06-10-refactor-repo-scan-scanner-py-cc-27-8-co-spec]] on branch radar/tkt-0002 for tkt-0002 |
| 2026-06-10 04:02 UTC | post_implement | paused | tests passed; 2 files changed, 197 insertions(+), 83 deletions(-) on radar/tkt-0002 — commit? |
| 2026-06-10 04:03 UTC | post_analyze | paused | Follow the repo’s snapshot-then-extract pattern: Phase 1 adds `tests/test_languages.py` with fixture repos, monkeypatche |
| 2026-06-10 04:05 UTC | post_analyze | approved (dashboard) | Follow the repo’s snapshot-then-extract pattern: Phase 1 adds `tests/test_languages.py` with fixture repos, monkeypatche |
| 2026-06-10 04:05 UTC | pre_implement | approved (dashboard) | implement [[2026-06-10-refactor-repo-scan-scanner-py-cc-27-8-co-spec]] on branch radar/tkt-0002 for tkt-0002 |
| 2026-06-10 04:06 UTC | post_implement | approved (dashboard) | tests passed; 2 files changed, 197 insertions(+), 83 deletions(-) on radar/tkt-0002 — commit? |
| 2026-06-10 04:08 UTC | post_audit | paused | audit revise: The phased characterization-then-extract plan, CC targets, skip-flag design, and public API preservation a |
| 2026-06-10 04:11 UTC | post_analyze | approved (dashboard) | Follow the repo’s snapshot-then-extract pattern: Phase 1 adds `tests/test_languages.py` with fixture repos, monkeypatche |
| 2026-06-10 04:11 UTC | post_audit | approved (dashboard) | audit revise: The phased characterization-then-extract plan, CC targets, skip-flag design, and public API preservation a |
| 2026-06-10 04:11 UTC | pre_implement | paused | implement [[2026-06-10-refactor-repo-scan-languages-py-cc-18-3-spec]] on branch radar/tkt-0004 for tkt-0004 |
| 2026-06-10 04:12 UTC | pre_implement | approved (dashboard) | implement [[2026-06-10-refactor-repo-scan-languages-py-cc-18-3-spec]] on branch radar/tkt-0004 for tkt-0004 |
| 2026-06-10 04:15 UTC | post_implement | paused | tests passed; 2 files changed, 78 insertions(+), 37 deletions(-) on radar/tkt-0004 — commit? |
| 2026-06-10 04:20 UTC | pre_implement | approved (dashboard) | implement [[2026-06-10-refactor-repo-scan-languages-py-cc-18-3-spec]] on branch radar/tkt-0004 for tkt-0004 |
| 2026-06-10 04:20 UTC | post_implement | approved (dashboard) | tests passed; 2 files changed, 78 insertions(+), 37 deletions(-) on radar/tkt-0004 — commit? |
| 2026-06-10 05:38 UTC | post_analyze | paused | Add an 'Open tickets' section to `rNow()` immediately after the gates card (or after the stats grid if no gates), filter |
| 2026-06-10 05:39 UTC | post_analyze | approved (dashboard) | Add an 'Open tickets' section to `rNow()` immediately after the gates card (or after the stats grid if no gates), filter |
| 2026-06-10 05:42 UTC | post_audit | paused | audit revise: The functional approach aligns well with codebase facts (`build_state()` fields, `rTickets()` status-order |
| 2026-06-10 05:43 UTC | post_analyze | approved (dashboard) | Add an 'Open tickets' section to `rNow()` immediately after the gates card (or after the stats grid if no gates), filter |
| 2026-06-10 05:43 UTC | post_audit | approved (dashboard) | audit revise: The functional approach aligns well with codebase facts (`build_state()` fields, `rTickets()` status-order |
| 2026-06-10 05:43 UTC | pre_implement | paused | implement [[2026-06-10-add-a-list-for-the-open-tickets-to-the-n-spec]] on branch radar/tkt-0010 for tkt-0010 |
| 2026-06-10 05:44 UTC | pre_implement | approved (dashboard) | implement [[2026-06-10-add-a-list-for-the-open-tickets-to-the-n-spec]] on branch radar/tkt-0010 for tkt-0010 |
| 2026-06-10 05:46 UTC | post_implement | paused | tests passed; 2 files changed, 35 insertions(+), 9 deletions(-) on radar/tkt-0010 — commit? |
| 2026-06-10 05:46 UTC | pre_implement | approved (dashboard) | implement [[2026-06-10-add-a-list-for-the-open-tickets-to-the-n-spec]] on branch radar/tkt-0010 for tkt-0010 |
| 2026-06-10 05:47 UTC | post_implement | approved (dashboard) | tests passed; 2 files changed, 35 insertions(+), 9 deletions(-) on radar/tkt-0010 — commit? |
| 2026-06-10 06:11 UTC | post_analyze | paused | Introduce a derived PM card layer on top of existing tkt-*.md files: parse ground truth into a mobile-first summary (pla |
| 2026-06-10 06:12 UTC | post_analyze | approved (dashboard) | Introduce a derived PM card layer on top of existing tkt-*.md files: parse ground truth into a mobile-first summary (pla |
| 2026-06-10 06:15 UTC | post_analyze | approved (dashboard) | Introduce a derived PM card layer on top of existing tkt-*.md files: parse ground truth into a mobile-first summary (pla |
| 2026-06-10 06:20 UTC | post_audit | paused | audit revise: The spec aligns well with the existing markdown ticket model, scan criteria behavior, and approval-gap fin |
| 2026-06-10 06:26 UTC | post_analyze | approved (dashboard) | Introduce a derived PM card layer on top of existing tkt-*.md files: parse ground truth into a mobile-first summary (pla |
| 2026-06-10 06:26 UTC | post_audit | approved (dashboard) | audit revise: The spec aligns well with the existing markdown ticket model, scan criteria behavior, and approval-gap fin |
| 2026-06-10 06:26 UTC | pre_implement | auto | implement [[2026-06-10-convert-tickets-to-most-human-friendly-t-spec]] on branch radar/tkt-0011 for tkt-0011 |
| 2026-06-10 06:33 UTC | post_implement | paused | tests passed; 10 files changed, 478 insertions(+), 27 deletions(-) on radar/tkt-0011 — commit? |
| 2026-06-10 06:47 UTC | post_analyze | paused | Delete setup.py and treat pyproject.toml as the sole packaging manifest, matching PyPA modernization and sampleproject p |
| 2026-06-10 06:48 UTC | pre_implement | auto | implement [[2026-06-10-convert-tickets-to-most-human-friendly-t-spec]] on branch radar/tkt-0011 for tkt-0011 |
| 2026-06-10 06:48 UTC | post_analyze | approved (dashboard) | Delete setup.py and treat pyproject.toml as the sole packaging manifest, matching PyPA modernization and sampleproject p |
| 2026-06-10 06:49 UTC | post_implement | approved (dashboard) | tests passed; 10 files changed, 478 insertions(+), 27 deletions(-) on radar/tkt-0011 — commit? |
| 2026-06-10 06:53 UTC | post_audit | paused | audit revise: Delete-setup.py is the right PyPA-aligned fix and the fixture-based coupling test is sound, but revise the |
| 2026-06-10 06:55 UTC | post_analyze | approved (dashboard) | Delete setup.py and treat pyproject.toml as the sole packaging manifest, matching PyPA modernization and sampleproject p |
| 2026-06-10 06:55 UTC | post_audit | approved (dashboard) | audit revise: Delete-setup.py is the right PyPA-aligned fix and the fixture-based coupling test is sound, but revise the |
| 2026-06-10 06:55 UTC | pre_implement | auto | implement [[2026-06-10-hidden-seam-pyproject-toml-setup-py-100-spec]] on branch radar/tkt-0007 for tkt-0007 |
| 2026-06-10 06:55 UTC | pre_implement | auto | implement [[2026-06-10-hidden-seam-pyproject-toml-setup-py-100-spec]] on branch radar/tkt-0007 for tkt-0007 |
| 2026-06-10 06:58 UTC | post_implement | paused | tests passed; 2 files changed, 5 insertions(+), 17 deletions(-) on radar/tkt-0007 — commit? |
| 2026-06-10 07:00 UTC | pre_implement | auto | implement [[2026-06-10-hidden-seam-pyproject-toml-setup-py-100-spec]] on branch radar/tkt-0007 for tkt-0007 |
| 2026-06-10 07:01 UTC | post_implement | auto | tests passed; 2 files changed, 5 insertions(+), 17 deletions(-) on radar/tkt-0007 — commit? |
| 2026-06-10 07:01 UTC | post_analyze | paused | Run pytest green as baseline, then lower CC in `test_loop_happy_path_auto_gates` by extracting pure assertion helpers fo |
| 2026-06-10 07:03 UTC | post_analyze | approved (dashboard) | Run pytest green as baseline, then lower CC in `test_loop_happy_path_auto_gates` by extracting pure assertion helpers fo |
| 2026-06-10 07:16 UTC | post_audit | paused | audit revise: The extract-helper plan, radon gate, PyNose/UTRefactor rationale, hub regression surface, provenance sub-s |
| 2026-06-10 07:17 UTC | post_analyze | approved (dashboard) | Run pytest green as baseline, then lower CC in `test_loop_happy_path_auto_gates` by extracting pure assertion helpers fo |
| 2026-06-10 07:17 UTC | post_audit | approved (dashboard) | audit revise: The extract-helper plan, radon gate, PyNose/UTRefactor rationale, hub regression surface, provenance sub-s |
| 2026-06-10 07:17 UTC | pre_implement | auto | implement [[2026-06-10-refactor-tests-test-radar-pipeline-py-cc-spec]] on branch radar/tkt-0009 for tkt-0009 |
| 2026-06-10 07:18 UTC | pre_implement | auto | implement [[2026-06-10-refactor-tests-test-radar-pipeline-py-cc-spec]] on branch radar/tkt-0009 for tkt-0009 |
| 2026-06-10 07:21 UTC | post_implement | auto | tests passed; 1 file changed, 59 insertions(+), 18 deletions(-) on radar/tkt-0009 — commit? |
| 2026-06-10 07:35 UTC | post_analyze | paused | Create `tests/test_sources.py` by migrating and extending existing `test_radar_ingest.py` source tests (add title-trunca |
| 2026-06-10 07:36 UTC | post_analyze | approved (dashboard) | Create `tests/test_sources.py` by migrating and extending existing `test_radar_ingest.py` source tests (add title-trunca |
| 2026-06-10 07:38 UTC | post_analyze | approved (dashboard) | Create `tests/test_sources.py` by migrating and extending existing `test_radar_ingest.py` source tests (add title-trunca |
| 2026-06-10 07:39 UTC | post_analyze | approved (dashboard) | Create `tests/test_sources.py` by migrating and extending existing `test_radar_ingest.py` source tests (add title-trunca |
| 2026-06-10 07:48 UTC | post_analyze | paused | Extend the existing Markdown+Mermaid pipeline with auto-generated, ticket-scoped diagrams sourced from scan.json: add a  |
| 2026-06-10 07:53 UTC | post_analyze | paused | Extract `repo_scan/report_pipeline.py` with a typed `ReportPayload` (or reuse `ScanContext` read-only view) and a single |
| 2026-06-10 07:54 UTC | post_audit | paused | audit revise: Well-aligned with radon findings, tkt-0005 acceptance criteria, and sibling audit fixes (scan.json baselin |
| 2026-06-10 07:59 UTC | post_analyze | paused | Introduce a private `RadarLoopRunner` (Replace Function with Command) that holds `root`, `cfg`, `problem`, `ckpt`, `resu |
| 2026-06-10 13:10 UTC | post_analyze | approved (dashboard) | Create `tests/test_sources.py` by migrating and extending existing `test_radar_ingest.py` source tests (add title-trunca |
| 2026-06-10 13:10 UTC | post_audit | approved (dashboard) | audit revise: Well-aligned with radon findings, tkt-0005 acceptance criteria, and sibling audit fixes (scan.json baselin |
| 2026-06-10 13:10 UTC | pre_implement | auto | implement [[2026-06-10-refactor-repo-scan-radar-sources-py-cc-1-spec]] on branch radar/tkt-0005 for tkt-0005 |
| 2026-06-10 13:11 UTC | post_analyze | approved (dashboard) | Extract `repo_scan/report_pipeline.py` with a typed `ReportPayload` (or reuse `ScanContext` read-only view) and a single |
| 2026-06-10 13:14 UTC | post_implement | auto | tests passed; 2 files changed, 42 insertions(+), 112 deletions(-) on radar/tkt-0005 — commit? |
