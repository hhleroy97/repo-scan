---
type: "changelog"
date: "2026-06-10"
tags: [changelog, hub, prs, ci]
---

# PR status + merge from the dashboard; CI branch-name fix

The act stage opens PRs, but reviewing them meant leaving the phone — and
two agent PRs sat failing CI with no visibility into why. Both ends fixed.

## CI fix (the actual test failure)

`test_daemon_runs_act_for_inprogress_ticket` asserted the base branch is
`main`, but GitHub runners default `init.defaultBranch` to `master`.
`tests/conftest.py` now creates fixture repos with `git init -b main`, so
the suite is deterministic everywhere. Verified by re-running the test with
`GIT_CONFIG_GLOBAL` forcing `defaultBranch = master`.

This failure is also why the open agent PRs (e.g. radar/tkt-0002) showed
red: their branches carry the pre-fix test, and re-running CI against the
same code can never pass. The cure is updating the branch from main — now
one tap (below).

## PR surface (`repo_scan/hub/prs.py`)

- `list_open_prs()` — open PRs via `gh pr list --json`, each with branch,
  mapped ticket (radar/<id> branches), mergeable state, and a collapsed
  checks verdict: `failing` > `pending` > `passing` / `none`. Cached 60s
  so the dashboard poll doesn't hammer the GitHub API; writes invalidate.
- `merge_pr()` — `gh pr merge --squash --delete-branch`; on success the
  mapped ticket gets a note and moves to done, and the event feed records
  the merge.
- `update_pr_branch()` — `gh pr update-branch`, re-running CI against
  current main.

## Dashboard

Now tab gains a Pull requests section: check-status badge (failing PRs get
a red border), ticket badge, View link, **Update branch** on
failing/conflicting PRs, and **Merge** with a confirm dialog that shouts
when checks are failing. New endpoints: `POST /api/pr/merge`,
`POST /api/pr/update`.

## Tests

`tests/test_prs.py` — 8 tests with a fake `gh` on PATH: rollup collapse,
ticket mapping, cache behavior, merge happy path (ticket noted + done),
merge failure propagation, update-branch, quiet no-gh degradation, and
state payload inclusion. Suite: 195 passed.
