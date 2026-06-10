# 2026-06-10 — Pipeline telemetry and north star docs

Stage timing and token burn rate are now tracked end-to-end.

## Observability

- `docs/.radar/stages.jsonl` — per-stage `duration_ms`, `tokens_in/out`, `stage_id`
- `progress()` closes prior stage on transition; `timed_block()` for fetch/test work
- `usage.jsonl` rows carry `stage_id` and `problem` for burn rollups
- Gate wait time recorded from `pending/*.json` `written_at` on resume
- Loop/act changelogs include **Timing** and **Burn rate** callouts
- Hub Activity tab + TUI show pipeline telemetry
- Activity **Stage burn** chart — dual bars per stage (time % blue, tokens % amber)
- Three views: **Avg / run**, **Total**, **By run** (dropdown to pick a specific run)

## Strategy docs

- `docs/NORTH_STAR.md` — mission, ground-truth hierarchy, time/tokens/quality balance
- `docs/research/theory.md` — distilled knowledge principles (human-edited below `## Notes`)
