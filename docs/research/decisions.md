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
