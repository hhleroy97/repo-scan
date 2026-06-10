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
| 2026-06-10 13:14 UTC | post_analyze | approved (dashboard) | Extend the existing Markdown+Mermaid pipeline with auto-generated, ticket-scoped diagrams sourced from scan.json: add a  |
| 2026-06-10 13:15 UTC | post_analyze | approved (dashboard) | Introduce a private `RadarLoopRunner` (Replace Function with Command) that holds `root`, `cfg`, `problem`, `ckpt`, `resu |
| 2026-06-10 13:16 UTC | post_analyze | paused | Follow the repo's characterization-then-extract playbook: snapshot radon output and a copy of `docs/scan.json`, then add |
| 2026-06-10 13:18 UTC | post_analyze | approved (dashboard) | Follow the repo's characterization-then-extract playbook: snapshot radon output and a copy of `docs/scan.json`, then add |
| 2026-06-10 13:20 UTC | post_audit | paused | audit revise: The spec aligns well with existing Mermaid writers, coupling/seam signals, and fingerprinted tickets, but  |
| 2026-06-10 13:21 UTC | post_audit | paused | audit revise: Radon/scan.json baselines (cmd_loop CC 19, write_analysis CC 11, derived cc_by_file 30, churn 10 vs stale  |
| 2026-06-10 13:23 UTC | post_audit | paused | audit revise: The dual-track approach matches the codebase (live 53%/5 shared, relative-import bug, existing snapshot ha |
| 2026-06-10 13:26 UTC | post_audit | paused | audit revise: Radon baselines, test migration inventory, and Fowler decomposition direction match the repo and code, but |
| 2026-06-10 13:31 UTC | post_analyze | approved (dashboard) | Extract `repo_scan/report_pipeline.py` with a typed `ReportPayload` (or reuse `ScanContext` read-only view) and a single |
| 2026-06-10 13:31 UTC | post_audit | approved (dashboard) | audit revise: The dual-track approach matches the codebase (live 53%/5 shared, relative-import bug, existing snapshot ha |
| 2026-06-10 13:32 UTC | pre_implement | auto | implement [[2026-06-10-hidden-seam-repo-scan-scanner-py-repo-sc-spec]] on branch radar/tkt-0008 for tkt-0008 |
| 2026-06-10 13:36 UTC | post_implement | auto | tests passed; 2 files changed, 72 insertions(+), 31 deletions(-) on radar/tkt-0008 — commit? |
| 2026-06-10 13:38 UTC | post_analyze | approved (dashboard) | Follow the repo's characterization-then-extract playbook: snapshot radon output and a copy of `docs/scan.json`, then add |
| 2026-06-10 13:38 UTC | post_audit | approved (dashboard) | audit revise: Radon baselines, test migration inventory, and Fowler decomposition direction match the repo and code, but |
| 2026-06-10 13:38 UTC | pre_implement | auto | implement [[2026-06-10-refactor-repo-scan-hub-daemon-py-cc-38-1-spec]] on branch radar/tkt-0013 for tkt-0013 |
| 2026-06-10 13:43 UTC | post_analyze | approved (dashboard) | Extend the existing Markdown+Mermaid pipeline with auto-generated, ticket-scoped diagrams sourced from scan.json: add a  |
| 2026-06-10 13:43 UTC | post_audit | approved (dashboard) | audit revise: The spec aligns well with existing Mermaid writers, coupling/seam signals, and fingerprinted tickets, but  |
| 2026-06-10 13:43 UTC | pre_implement | auto | implement [[2026-06-10-i-want-to-add-a-more-robust-way-to-visua-spec]] on branch radar/tkt-0012 for tkt-0012 |
| 2026-06-10 13:44 UTC | post_analyze | approved (dashboard) | Introduce a private `RadarLoopRunner` (Replace Function with Command) that holds `root`, `cfg`, `problem`, `ckpt`, `resu |
| 2026-06-10 13:44 UTC | post_audit | approved (dashboard) | audit revise: Radon/scan.json baselines (cmd_loop CC 19, write_analysis CC 11, derived cc_by_file 30, churn 10 vs stale  |
| 2026-06-10 13:44 UTC | post_implement | auto | tests passed; 4 files changed, 184 insertions(+), 382 deletions(-) on radar/tkt-0013 — commit? |
| 2026-06-10 13:44 UTC | pre_implement | auto | implement [[2026-06-10-refactor-repo-scan-radar-pipeline-py-cc-spec]] on branch radar/tkt-0006 for tkt-0006 |
| 2026-06-10 13:47 UTC | post_implement | auto | tests passed; 1 file changed, 252 insertions(+), 152 deletions(-) on radar/tkt-0006 — commit? |
| 2026-06-10 13:49 UTC | post_implement | paused | PROTECTED paths touched (repo_scan/config.py) — tests passed; 12 files changed, 412 insertions(+), 32 deletions(-) on ra |
| 2026-06-10 14:02 UTC | pre_implement | auto | implement [[2026-06-10-i-want-to-add-a-more-robust-way-to-visua-spec]] on branch radar/tkt-0012 for tkt-0012 |
| 2026-06-10 14:02 UTC | post_implement | approved (dashboard) | PROTECTED paths touched (repo_scan/config.py) — tests passed; 12 files changed, 412 insertions(+), 32 deletions(-) on ra |
| 2026-06-10 17:18 UTC | post_analyze | paused | Extract hub-owned defaults and key names into repo_scan/hub/settings.py (HUB_DEFAULTS + HUB_CONFIG_KEYS), have daemon.py |
| 2026-06-10 17:18 UTC | post_analyze | approved (dashboard) | Extract hub-owned defaults and key names into repo_scan/hub/settings.py (HUB_DEFAULTS + HUB_CONFIG_KEYS), have daemon.py |
| 2026-06-10 17:20 UTC | post_analyze | paused | Extract repo_scan/hub/contract.py owning API route constants, ticket status/order/badge maps (sourced from repo_scan.tic |
| 2026-06-10 17:21 UTC | post_analyze | approved (dashboard) | Extract repo_scan/hub/contract.py owning API route constants, ticket status/order/badge maps (sourced from repo_scan.tic |
| 2026-06-10 17:29 UTC | post_audit | paused | audit revise: The contract-extraction direction matches analysis and code evidence, but the spec should fix AC2 commit m |
| 2026-06-10 17:30 UTC | post_analyze | approved (dashboard) | Extract repo_scan/hub/contract.py owning API route constants, ticket status/order/badge maps (sourced from repo_scan.tic |
| 2026-06-10 17:30 UTC | post_audit | approved (dashboard) | audit revise: The contract-extraction direction matches analysis and code evidence, but the spec should fix AC2 commit m |
| 2026-06-10 17:30 UTC | pre_implement | auto | implement [[2026-06-10-hidden-seam-repo-scan-hub-server-py-repo-spec]] on branch radar/tkt-0014 for tkt-0014 |
| 2026-06-10 17:31 UTC | post_audit | paused | audit revise: The shared-module direction, 56%/7-shared baseline, degree formula, and tkt-0008 AC1 reinterpretation matc |
| 2026-06-10 17:31 UTC | post_analyze | approved (dashboard) | Extract hub-owned defaults and key names into repo_scan/hub/settings.py (HUB_DEFAULTS + HUB_CONFIG_KEYS), have daemon.py |
| 2026-06-10 17:31 UTC | post_audit | approved (dashboard) | audit revise: The shared-module direction, 56%/7-shared baseline, degree formula, and tkt-0008 AC1 reinterpretation matc |
| 2026-06-10 17:31 UTC | pre_implement | auto | implement [[2026-06-10-hidden-seam-repo-scan-hub-server-py-repo-spec]] on branch radar/tkt-0014 for tkt-0014 |
| 2026-06-10 17:32 UTC | pre_implement | auto | implement [[2026-06-10-hidden-seam-repo-scan-config-py-repo-sca-spec]] on branch radar/tkt-0016 for tkt-0016 |
| 2026-06-10 17:32 UTC | post_analyze | paused | Add `from .gates import GATE_NAMES` (and a small GATE_MODES or `gate_arg_parser()` helper colocated in gates.py) and ref |
| 2026-06-10 17:34 UTC | post_implement | auto | tests passed; 3 files changed, 74 insertions(+), 64 deletions(-) on radar/tkt-0014 — commit? |
| 2026-06-10 17:35 UTC | post_analyze | approved (dashboard) | Add `from .gates import GATE_NAMES` (and a small GATE_MODES or `gate_arg_parser()` helper colocated in gates.py) and ref |
| 2026-06-10 17:39 UTC | post_implement | paused | PROTECTED paths touched (repo_scan/config.py) — tests passed; 6 files changed, 38 insertions(+), 23 deletions(-) on rada |
| 2026-06-10 17:41 UTC | post_audit | paused | audit revise: The spec is well-grounded in live coupling.md (4 shared, 80%, no edge) and the right remediation (cli→gate |
| 2026-06-10 17:42 UTC | post_analyze | approved (dashboard) | Add `from .gates import GATE_NAMES` (and a small GATE_MODES or `gate_arg_parser()` helper colocated in gates.py) and ref |
| 2026-06-10 17:42 UTC | pre_implement | auto | implement [[2026-06-10-hidden-seam-repo-scan-config-py-repo-sca-spec]] on branch radar/tkt-0016 for tkt-0016 |
| 2026-06-10 17:42 UTC | post_audit | approved (dashboard) | audit revise: The spec is well-grounded in live coupling.md (4 shared, 80%, no edge) and the right remediation (cli→gate |
| 2026-06-10 17:42 UTC | pre_implement | auto | implement [[2026-06-10-hidden-seam-repo-scan-radar-cli-py-repo-spec]] on branch radar/tkt-0015 for tkt-0015 |
| 2026-06-10 17:43 UTC | post_implement | approved (dashboard) | PROTECTED paths touched (repo_scan/config.py) — tests passed; 6 files changed, 38 insertions(+), 23 deletions(-) on rada |
| 2026-06-10 17:45 UTC | post_implement | auto | tests passed; 6 files changed, 142 insertions(+), 17 deletions(-) on radar/tkt-0015 — commit? |
| 2026-06-10 18:28 UTC | post_analyze | paused | Convert `repo_scan/hub/ui.py` into a `repo_scan/hub/ui/` subpackage that exports the same `DASHBOARD_HTML` from `__init_ |
| 2026-06-10 18:29 UTC | post_analyze | approved (dashboard) | Convert `repo_scan/hub/ui.py` into a `repo_scan/hub/ui/` subpackage that exports the same `DASHBOARD_HTML` from `__init_ |
| 2026-06-10 18:33 UTC | post_audit | paused | audit revise: The package/concat/contract-injection approach is sound and line caps are achievable, but fragment boundar |
| 2026-06-10 18:35 UTC | post_analyze | approved (dashboard) | Convert `repo_scan/hub/ui.py` into a `repo_scan/hub/ui/` subpackage that exports the same `DASHBOARD_HTML` from `__init_ |
| 2026-06-10 18:35 UTC | post_audit | approved (dashboard) | audit revise: The package/concat/contract-injection approach is sound and line caps are achievable, but fragment boundar |
| 2026-06-10 18:36 UTC | pre_implement | auto | implement [[2026-06-10-split-repo-scan-hub-ui-py-706-lines-repo-spec]] on branch radar/tkt-0025 for tkt-0025 |
| 2026-06-10 18:39 UTC | post_implement | auto | tests passed; 3 files changed, 31 insertions(+), 713 deletions(-) on radar/tkt-0025 — commit? |
| 2026-06-10 18:50 UTC | post_analyze | paused | Extract daemon's act orchestration from _run_act into repo_scan/hub/act_run.py (run invocation, RC→run-state mapping, va |
| 2026-06-10 18:51 UTC | post_analyze | paused | Convert `repo_scan/tickets.py` into `repo_scan/tickets/` with modules `constants`, `parse`, `evidence`, `propose`, `io`, |
| 2026-06-10 18:51 UTC | post_analyze | approved (dashboard) | Extract daemon's act orchestration from _run_act into repo_scan/hub/act_run.py (run invocation, RC→run-state mapping, va |
| 2026-06-10 18:52 UTC | post_analyze | approved (dashboard) | Convert `repo_scan/tickets.py` into `repo_scan/tickets/` with modules `constants`, `parse`, `evidence`, `propose`, `io`, |
| 2026-06-10 18:55 UTC | post_audit | paused | audit revise: The split boundaries, ≤300 cap feasibility, facade re-export strategy, and lazy-import cycle breaks are so |
| 2026-06-10 19:09 UTC | post_analyze | approved (dashboard) | Convert `repo_scan/tickets.py` into `repo_scan/tickets/` with modules `constants`, `parse`, `evidence`, `propose`, `io`, |
| 2026-06-10 19:09 UTC | post_audit | approved (dashboard) | audit revise: The split boundaries, ≤300 cap feasibility, facade re-export strategy, and lazy-import cycle breaks are so |
| 2026-06-10 19:09 UTC | pre_implement | auto | implement [[2026-06-10-split-repo-scan-tickets-py-654-lines-rep-spec]] on branch radar/tkt-0026 for tkt-0026 |
| 2026-06-10 19:09 UTC | post_analyze | approved (dashboard) | Extract daemon's act orchestration from _run_act into repo_scan/hub/act_run.py (run invocation, RC→run-state mapping, va |
| 2026-06-10 19:10 UTC | pre_implement | auto | implement [[2026-06-10-split-repo-scan-tickets-py-654-lines-rep-spec]] on branch radar/tkt-0026 for tkt-0026 |
| 2026-06-10 19:10 UTC | post_analyze | approved (dashboard) | Extract daemon's act orchestration from _run_act into repo_scan/hub/act_run.py (run invocation, RC→run-state mapping, va |
| 2026-06-10 19:10 UTC | pre_implement | auto | implement [[2026-06-10-split-repo-scan-tickets-py-654-lines-rep-spec]] on branch radar/tkt-0026 for tkt-0026 |
| 2026-06-10 19:11 UTC | post_analyze | approved (dashboard) | Extract daemon's act orchestration from _run_act into repo_scan/hub/act_run.py (run invocation, RC→run-state mapping, va |
| 2026-06-10 19:11 UTC | pre_implement | auto | implement [[2026-06-10-split-repo-scan-tickets-py-654-lines-rep-spec]] on branch radar/tkt-0026 for tkt-0026 |
| 2026-06-10 19:11 UTC | post_analyze | approved (dashboard) | Extract daemon's act orchestration from _run_act into repo_scan/hub/act_run.py (run invocation, RC→run-state mapping, va |
