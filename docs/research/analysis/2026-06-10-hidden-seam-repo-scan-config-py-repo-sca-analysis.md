---
type: "analysis"
problem: "Hidden seam: repo_scan/config.py <-> repo_scan/hub/daemon.py (58% coupled). `repo_scan/config.py` and `repo_scan/hub/daemon.py` changed together in 7 commits (58% degree) but share no import edge — an implicit contract the dependency graph can't see. Acceptance criteria: Make the dependency explicit (shared module or import); Coupling degree drops below threshold in coupling.md. Research current best practices and draft a spec for this work."
confidence: "high"
sources: ["gh-seddonym-import-linter", "url-wiki-apidesign-org-wiki-configurationobject", "gh-xlab-uiuc-cdep-fse-ae"]
generated_at: "2026-06-10 17:18 UTC"
linked_files: ["repo_scan/config.py", "repo_scan/hub/daemon.py", "repo_scan/hub/settings.py"]
---

# Analysis — Hidden seam: repo_scan/config.py <-> repo_scan/hub/daemon.py (58% coupled). `repo_scan/config.py` and `repo_scan/hub/daemon.py` changed together in 7 commits (58% degree) but share no import edge — an implicit contract the dependency graph can't see. Acceptance criteria: Make the dependency explicit (shared module or import); Coupling degree drops below threshold in coupling.md. Research current best practices and draft a spec for this work.
_Generated 2026-06-10 17:18 UTC — confidence: high_

## Findings

- The hidden seam is a configuration contract, not a missing runtime import: daemon.py receives a plain dict from load_config() and reads hub keys (serve_host, daemon_poll_seconds, daemon_scan_hours, vault_autocommit, max_parallel_acts, etc.) via scattered cfg.get() calls with inline magic defaults (20, 8800, 6, 2, True) while config.py separately declares the same keys in RADAR_CONFIG_KEYS without defaults—duplication the dependency graph cannot see.
- cDep’s core insight applies directly: cross-component configuration dependencies are first-class logical couplings that static import analysis misses; repo-scan’s change-coupling metric is surfacing the same phenomenon between config.py and daemon.py (7 shared commits, 56% degree).
- The ConfigurationObject pattern argues for subsystem-owned, named configuration namespaces over growing flat string-key dicts—hub/daemon settings should live in a hub-owned module with explicit defaults rather than being split across a global loader and consumer magic numbers.
- Import Linter aligns with the ticket’s AC1: once hub settings are extracted, contracts like hub.daemon → hub.settings and config → hub.settings can be declared and enforced in CI, preventing future implicit key-list drift.
- tkt-0008 precedent shows AC1 is satisfied by a shared contract module (report_pipeline), not necessarily a direct import between the two historically-coupled files; AC2 still requires degree strictly below 50% (coupling_min_degree), meaning ≥2 post-refactor commits that touch only one side of the pair—50% exactly remains listed.
- Hub keys are already shared across server.py, notify.py, and daemon.py (serve_host, serve_port, ntfy_*, dashboard_url); extracting repo_scan/hub/settings.py addresses a broader hub package contract, not only the config↔daemon seam.
- daemon.py also reads non-hub RADAR keys (radar_enabled, act_enabled, budget_daily_tokens, docs_dir); a minimal fix should single-source daemon-scheduler defaults while leaving broader RADAR_CONFIG_KEYS decomposition to follow-on tickets unless scope is explicitly expanded.

## Recommendation

Extract hub-owned defaults and key names into repo_scan/hub/settings.py (HUB_DEFAULTS + HUB_CONFIG_KEYS), have daemon.py import that module for constants and defaults instead of inline magic numbers, and have config.py merge HUB_DEFAULTS and validate against HUB_CONFIG_KEYS during load_config—creating explicit import edges config → hub.settings and hub.daemon → hub.settings. Follow tkt-0008’s verification pattern: add contract/import-boundary tests, land the refactor, then make ≥2 follow-up commits touching only config or only daemon/settings so rescanned coupling.md drops the pair below the 50% threshold; optionally add an import-linter contract in a later pass.

## Risks

- config.py importing hub.settings introduces a core→hub package dependency that may conflict with layering intuition—alternatives (shared repo_scan/settings/ package) add scope.
- Partial extraction (only hub serve/ntfy keys) leaves daemon still coupled to config.py via radar/act/budget keys still listed only in RADAR_CONFIG_KEYS.
- Default-value drift if daemon keeps local cfg.get fallbacks instead of referencing HUB_DEFAULTS exclusively.
- Historical coupling degree will not drop until new divergent commits accumulate post-merge; refactor alone is insufficient.
- config.py is in protected_paths—changes require governance/test gate approval.
- Import-linter adoption is not yet in the project; without it, the explicit import edge prevents graph blindness but does not automatically guard against future key-list edits.

## Evidence

- [[gh-seddonym-import-linter\|seddonym/import-linter — Lint your Python architecture.]]
- [[url-wiki-apidesign-org-wiki-configurationobject\|ConfigurationObject]]
- [[gh-xlab-uiuc-cdep-fse-ae\|xlab-uiuc/cdep-fse-ae — Configuration dependency analysis for cloud software]]
- research run: [[2026-06-10-hidden-seam-repo-scan-config-py-repo-sca]]
