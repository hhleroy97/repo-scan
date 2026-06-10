---
type: theory
updated: "2026-06-10"
tags: [research, principles]
---

# Distilled understanding

Human-curated layer between raw ingested sources and implementation specs.
RADAR may suggest edits above `## Notes`; everything below is yours.

See also: [[NORTH_STAR]]

---

## Core beliefs

1. **Committed markdown beats ephemeral context** — if it is not in `docs/` and
   git, it did not happen. `repo_snapshot()` is a lens, not ground truth.
2. **Provenance clusters beat orphan notes** — sources → analysis → spec → act
   changelog should form one Obsidian cluster per problem.
3. **Metrics trigger attention, humans trigger commitment** — scan proposes;
   gates approve recording and implementation.
4. **Real sources anchor claims** — specs cite ingested material or scan
   evidence, not model memory.

---

## Approved patterns

| Pattern | Why | Sources |
|---------|-----|---------|
| Reflexion audit (capped revise) | Quality without infinite loops | [[sources/arxiv-reflexion]] (if ingested) |
| File-backed gates | Pause/resume without checkpointer | [[2026-06-09-phase-b3-loop]] changelog |
| `repo_snapshot()` injection | Agents see fresh ranking + tickets | [[2026-06-10-repo-snapshot]] changelog |
| Ticket as ground truth, PM card derived | One canonical work item | `repo_scan/tickets.py` |
| Syrupy snapshots before refactor | Verify complexity drops | writers/languages refactor specs |

---

## Rejected / deferred

| Idea | Status | Notes |
|------|--------|-------|
| Dump full `scan.json` into prompts | Rejected | Use ranked snapshot + digest |
| Hub-rendered Mermaid | Deferred | Obsidian/GitHub render instead |
| Autonomous loop on every candidate | Deferred | Budget + gate trust first |
| Auto-overwrite source `## Notes` | Rejected | Human notes are sacred |

---

## Open questions

- When should `linked_files` be auto-populated from analyze output?
- What metric delta closes a ticket without human review?
- Optimal `llm_roles` split per repo size (burn vs quality)?
- Re-ingest policy for stale URLs vs trusting human notes?

## Notes

_yours to annotate — RADAR never overwrites below this line_
