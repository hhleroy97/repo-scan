---
type: "changelog"
date: "2026-06-10"
tags: [changelog, hub, vault]
---

# Vault auto-commit after every run and scan

Loops and scans write artifacts continuously (specs, analyses, sources,
tickets, decision trail), but nothing committed them — agentic history
piled up untracked until a human rescued it in catch-up commits.

## Changes

- `commit_vault()` in `repo_scan/hub/daemon.py`: stages and commits
  `docs/` after every loop, act, and scheduled scan, with `vault:` prefixed
  messages naming the run. Pathspec-scoped commit, so a human's staged code
  work is never swept in. Thread-locked so parallel acts don't race the git
  index.
- Push is best-effort: fast-forward sync first (`sync_local`), then
  `git push origin HEAD`; offline just accumulates local commits.
- `docs/research/pending/` is gitignored — paused-gate state is transient
  (consumed on resume), it belongs with `.radar/` runtime state, and it was
  what kept the tree looking dirty mid-run.
- New config key `vault_autocommit` (default true).

## Tests

`test_commit_vault_commits_docs_only` (docs committed, staged human work
untouched and still pending) and `test_commit_vault_noop_when_clean_or_disabled`.
Suite: 262 passed.
