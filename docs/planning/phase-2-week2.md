---
type: plan
phase: 2
title: "Week 2 — Agent freshness depth"
status: planned
tags: [planning, act, record, tickets]
prerequisite: "[[phase-1-week1]]"
---

# Phase 2 — Agent freshness depth

**Goal:** Agents see fresh code at act time; merged work is automatically verified;
stale proposed tickets stop cluttering the board.

**Prerequisite:** Phase 1 `repo_snapshot()` landed.

## Task 2.1 — Pre-act context bundle

Before `ACT_PROMPT`, inject into worktree session:
- `git diff main...HEAD` stat (if branch exists)
- Spec excerpt (from approved spec stem)
- Ticket acceptance criteria
- `repo_snapshot()` fresh build
- Last 5 `docs/changelog/*-act.md` entries for this ticket id

**Research to ingest before build:** extend GitHits search on aider `copy-context`, repomix output format.

## Task 2.2 — Record stage

On PR merge (hub `merge_pr` + manual):
1. Scheduled or immediate rescan
2. Compare metric fingerprint vs ticket `fingerprint`
3. Append ticket note with delta summary
4. Auto `done` if fingerprint cleared

## Task 2.3 — Auto-close metrics-resolved tickets

Daemon tick after scan: proposed tickets with `metrics resolved` note → `done` or auto-reject with reason.

**Acceptance criteria, tests, files:** to be detailed when Phase 1 completes.
