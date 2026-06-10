---
type: changelog
date: 2026-06-10
tags:
  - changelog
  - hub
  - pr
---

# PR diagnose & remediate from the phone

The **Fix & update** button on failing or conflicting PRs now does real work
instead of only calling `gh pr update-branch`.

## What changed

- **`remediate_pr()`** — orchestrates update-branch, local conflict probe
  (temp worktree merge against `origin/main`), and CI log capture
  (`gh run list` + `gh run view --log-failed`). Diagnosis is persisted under
  `docs/.radar/pr-diagnosis/<number>.json` and merged into dashboard state.
- **Background agent fix** — when `pr_auto_remediate` is true (default) and the
  PR maps to a radar ticket, a thread runs `act_fix` on the PR branch:
  resolve conflicts, apply CI-log-guided fixes, run tests with bounded fix
  rounds, commit, and push. Progress lands on the ticket and agent feed.
- **Dashboard** — PR cards show inline diagnosis (conflict files, CI log
  tail, fix-pushed status). Button renamed **Fix & update**; API returns
  `{ok, message, diagnosis, fix_started}`.

## Config

```json
{ "pr_auto_remediate": true }
```

Set false to diagnose only (no agent thread).

## Tests

- `test_probe_merge_conflicts_detects_files` — real git merge probe
- `test_remediate_pr_captures_ci_log` — fake gh returns CI failure log
