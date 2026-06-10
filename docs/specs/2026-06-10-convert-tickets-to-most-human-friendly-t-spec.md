---
type: "spec"
problem: "Convert tickets to most human friendly/tech leas project manager terms in. The approval/ticket cards . Retain current ticket as ground truth and have these ticket be abstractions of that ground truth. Easier to interact with when making decisions form a mobile device Acceptance criteria: define acceptance criteria before approving. Research current best practices and draft a spec for this work."
status: "approved"
audit_verdict: "revise"
analysis: "[[2026-06-10-convert-tickets-to-most-human-friendly-t-analysis]]"
drafted_at: "2026-06-10 06:26 UTC"
linked_files: ["repo_scan/hub/server.py", "repo_scan/hub/tui.py"]
---

# Spec — Convert tickets to most human friendly/tech leas project manager terms in. The approval/ticket cards . Retain current ticket as ground truth and have these ticket be abstractions of that ground truth. Easier to interact with when making decisions form a mobile device Acceptance criteria: define acceptance criteria before approving. Research current best practices and draft a spec for this work.
_Drafted 2026-06-10 06:26 UTC by radar — **status: approved**_

I'll check the ticket model, hub UI, and approval flow so the revised spec matches the codebase and covers every audit issue.
## Goal

Make mobile ticket triage decision-ready by projecting each `docs/tickets/tkt-*.md` into a PM-facing card (plain-language outcome, one-line why, criteria summary) while keeping markdown the single source of truth. Block approval until at least one non-placeholder acceptance criterion exists; let mobile users add criteria without opening raw markdown.

## Approach

Extend `parse_ticket()` to derive a `card` object from ground truth — never a second editable file. Resolution order: optional `## Card` (`Outcome:`, `Story:`, `Title:`) → frontmatter `card_*` overrides → heuristics from `Why`, tags/kind, `title`, and `criteria`. Heuristics: strip backtick paths and `(CC N, …)` / line-count parentheticals from display copy; map `refactor` → “Reduce risk in {basename}”, `size` → “Break up oversized {basename}”, `seam` → “Make coupling explicit”, else first sentence of `why` (≤120 chars). Expose `card` (`title`, `outcome`, `story`, `why_line`, `criteria_summary`), `criteria`, `criteria_count`, `criteria_ready` on hub state. Render three disclosure tiers in `hub/ui.py`: glance row (`outcome`, `why_line`, status, priority, `N criteria`), tap-to-expand checklist, “View ticket” via `openDoc`. Add `PATCH /api/ticket` to append/replace checkbox criteria in markdown. Enforce `criteria_ready` in `set_ticket_status(..., "approved")`, hub approve + criteria PATCH validation, CLI `tickets approve`, and TUI approve. Gate `pick_approved_ticket()` on `criteria_ready` so legacy approved placeholders (e.g. tkt-0011) do not enter the radar loop. Scan proposals already ship concrete `criteria`; only derive `card.outcome` at `write_ticket()` time.

## Changes

- **`repo_scan/tickets.py`**
  - Add `PLACEHOLDER_CRITERIA` matching both existing defaults (`define done`, `define acceptance criteria before approving`) plus case/whitespace variants; `criteria_ready(criteria) -> bool`.
  - Add `derive_card(meta, text) -> dict` and `update_ticket_criteria(root, cfg, id, criteria) -> dict`.
  - Extend `parse_ticket()` with `card`, `criteria_ready`, `criteria_summary` (first two non-placeholder lines, joined).
  - Gate `set_ticket_status(..., "approved")` with `ValueError` when `not criteria_ready`.
  - Gate `pick_approved_ticket()` — skip tickets failing `criteria_ready`.
  - In `write_ticket()`, attach derived `card.outcome` when absent; do not rewrite scan `criteria` (already concrete).
  - In `new_ticket()`, require `criteria_ready` when `status="approved"`; default proposed keeps placeholder until filled.

- **`repo_scan/hub/server.py`**
  - Include full `card` + `criteria_*` fields in `build_state()`; 400 on approve when not ready; `PATCH /api/ticket` for criteria edits.

- **`repo_scan/hub/ui.py`**
  - Glance: `card.outcome`, `card.why_line`, criteria badge; expand checklist; inline criteria editor when `!criteria_ready`; disable Approve + hint until ready; `openDoc` for full markdown.

- **`repo_scan/hub/tui.py`**
  - Show `card.outcome`; wrap `set_ticket_status` in try/except — return error string on `ValueError`, no status change.

- **`docs/tickets/` (schema)**
  - Document optional `## Card` and hub/API criteria editing; agents suggest, humans edit ground-truth markdown or hub form.

## Tests

| Acceptance criterion | Automated test |
|---|---|
| Define acceptance criteria before approving | `test_tickets.py::test_approve_blocked_without_valid_criteria` |
| Hub approve rejected without criteria | `test_hub.py::test_ticket_approve_rejected_without_criteria` |
| CLI approve rejected without criteria | `test_tickets_workflow.py::test_tickets_cli_approve_rejected_without_criteria` |
| CLI `new --approve` without `--criterion` fails | `test_tickets_workflow.py::test_tickets_cli_new_approve_requires_criteria` |
| PM card from refactor ticket | `test_tickets.py::test_derive_card_from_refactor_ticket` — no path/CC in `outcome`; technical `title` unchanged |
| `## Card` overrides heuristics | `test_tickets.py::test_parse_ticket_card_section_overrides` — `Outcome`/`Story`/`Title` mapped |
| Hub payload fields | `test_hub.py::test_build_state_includes_ticket_card_fields` |
| Hub criteria PATCH | `test_hub.py::test_ticket_patch_criteria_enables_approve` |
| Hub UI progressive disclosure | `test_hub_ui.py::test_ticket_cards_render_card_outcome_and_criteria_count` |
| TUI approval gate | `test_tui.py::test_tui_approve_blocked_without_criteria` — error message, no status change |
| `pick_approved_ticket` skips bad criteria | `test_tickets_workflow.py::test_pick_approved_skips_placeholder_criteria` |

## Documentation

- **`repo_scan/tickets.py` module docstring** — derived PM card, both placeholder strings, `## Card`, criteria gate on approve and pick.
- **`derive_card()` / `criteria_ready()` docstrings** — override order, heuristic rules, placeholder patterns.
- **`docs/tickets/README.md`** — ticket anatomy, Card block, mobile criteria edit, approval policy.
- **`repo_scan/hub/ui.py`** — comment on three-tier disclosure aligned with `OPEN_STATUSES`.

## Risks

- Heuristic rewriting may misstate edge cases; mitigate with `## Card` override and full-doc drill-down.
- Stricter gate blocks legacy tickets with placeholder criteria until edited — expected on first mobile approve.
- Direct Obsidian/frontmatter `status: "approved"` edits bypass the gate; document that approve must go through hub/CLI/TUI (or criteria must be fixed before loop picks ticket).
- TUI/CLI/hub must share `criteria_ready()` — single helper, no duplicated regex.
- `board.md` Kanban links keep canonical `title`, not `card.outcome`.

## Out of scope

- LLM-generated PM copy at runtime or auto-rewriting markdown `title` on every scan.
- Separate card database, JSON sidecar, or parallel ticket files.
- Changing radar loop or spec generation beyond `pick_approved_ticket` gate and existing `criteria`.
- Redesigning Gates tab layout (only ticket cards adopt PM summary pattern).
- Bulk-migrating existing `tkt-*.md` files.

## Audit

> [!warning] Audit verdict: revise
> The spec aligns well with the existing markdown ticket model, scan criteria behavior, and approval-gap findings, but needs reconciliation on whether PM cards are purely derived at parse time or persisted, plus explicit Now-tab coverage and a few operational risks before human review.
> - Resolution order conflicts with drift mitigation: persisting `## Card` in `write_ticket()` while parsing prefers `## Card` over live heuristics means auto-written PM copy can freeze and diverge when `Why`/`title` change — the analysis explicitly warns against drift and recommends derive-on-read via `parse_ticket`, not persisted card fields that trump refreshed ground truth.
> - Research and the stated mobile goal call for PM glance cards on Now/Gates/Tickets, but the UI section only specifies three-tier disclosure on ticket cards; `rOpenTickets()` on the Now tab is unchanged (still raw `title`/`why`) and Gates is explicitly out of scope — leaving the primary mobile triage surface partially unaddressed.
> - `card.story` and `criteria_summary` are added to the hub payload and card model but never mapped to a disclosure tier; glance uses `outcome`, `why_line`, and criteria count only — dead fields or undocumented UI use.
> - Heuristic map covers `refactor`/`size`/`seam` (via fingerprint kind) but not `stale:` or `silo:` proposals, which fall back to technical `why` text; no test or risk entry for those scan ticket types.
> - Missing risk: `update_ticket_criteria()` markdown rewriting (section boundaries, concurrent Obsidian/hub edits, partial writes) — unlike `set_ticket_status`, which only touches frontmatter.
> - Missing risk: gating `pick_approved_ticket()` on `criteria_ready` can starve the daemon research loop when every approved ticket has placeholder criteria (currently tkt-0011; broader if humans `--approve` without criteria).
> - Missing risk: direct `status: approved` frontmatter edits and Obsidian Kanban workflows bypass all gates; documented briefly but no mitigation (e.g. re-validate on pick/load) beyond pick-time skip.
> - Acceptance-test plan omits Now-tab PM rendering, `update_ticket_criteria` round-trip/markdown integrity, and frontmatter `card_*` overriding `## Card` despite specifying that override order.

## Provenance

- analysis: [[2026-06-10-convert-tickets-to-most-human-friendly-t-analysis]]
