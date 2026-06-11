---
type: changelog
date: 2026-06-11
tags:
  - changelog
  - provenance
linked_files: ["[[repo_scan/provenance.py]]"]
---
# Freshness demoted to vanity metric

**Date:** 2026-06-11

## Rationale

The "fresh" signal penalized docs whose linked code had been touched
more recently — but a newer code file doesn't mean the doc is wrong.
Updating research or specs every time code changes creates churn without
improving trust.

## Change

- Provenance score is now **0–3** (evidence, linked, cited). Fresh is
  still tracked and displayed in the signal matrix, chain panel glyphs,
  and stale-days strip, but no longer contributes to the numeric score.
- `_SCORE_SIGNALS = ("evidence", "linked", "cited")` in
  `repo_scan/provenance.py` separates scoring from display.
- Healthy threshold: 3 (was 4). Histogram: 0–3 (was 0–4).
- Score ring colors adjusted: green at 3, blue at 2, amber at 1.
- Knowledge debt formula unchanged (still uses coverage_pct, which is
  now based on score == 3).
