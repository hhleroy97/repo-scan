---
type: plan
phase: 4
title: "Week 4 — Observability & north star"
status: done
tags: [planning, telemetry, strategy]
prerequisite: "[[phase-3-week3]]"
---

# Phase 4 — Observability & north star

**Goal:** Measure stage duration and token burn rate; anchor the project with
a north star doc and distilled theory layer.

**North star:** [[NORTH_STAR]] · **Theory:** [[research/theory]]

## Task 4.1 — North star documents ✅

- `docs/NORTH_STAR.md` — mission, hierarchy, balance framework
- `docs/research/theory.md` — curated principles
- Links from `RADAR_CONTEXT.md`

## Task 4.2 — Stage timing ✅

- `repo_scan/hub/telemetry.py` + `stages.jsonl`
- `progress()` stage transitions emit `stage_done`
- Gate wait, fetch, test subprocess timed

## Task 4.3 — Token burn attribution ✅

- `usage.jsonl` adds `stage_id`, `problem`
- `burn_summary()` + `by_stage` rollups

## Task 4.4 — Vault + hub surfacing ✅

- `record_loop` / `record_act` timing callouts
- Activity tab telemetry + TUI section
- `build_state().telemetry`

**Tests:** `tests/test_telemetry.py`, hub/llm/pipeline/act updates
