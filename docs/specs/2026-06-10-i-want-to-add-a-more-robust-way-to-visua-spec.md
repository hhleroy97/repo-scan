---
type: "spec"
problem: "I want to add a more robust way to visualize changes out ogther a list of low hanging options we could include in the tickets such as simple visual diagrams as aid or soemthinf. _captured from intent — refine before approving_ Acceptance criteria: Tbd. Research current best practices and draft a spec for this work."
status: "approved"
audit_verdict: "revise"
analysis: "[[2026-06-10-i-want-to-add-a-more-robust-way-to-visua-analysis]]"
drafted_at: "2026-06-10 13:43 UTC"
linked_files: ["repo_scan/config.py", "repo_scan/graphs.py", "repo_scan/scanner.py", "repo_scan/writers.py", "tests/test_scanner_snapshots.py"]
---

# Spec — I want to add a more robust way to visualize changes out ogther a list of low hanging options we could include in the tickets such as simple visual diagrams as aid or soemthinf. _captured from intent — refine before approving_ Acceptance criteria: Tbd. Research current best practices and draft a spec for this work.
_Drafted 2026-06-10 13:43 UTC by radar — **status: approved**_

I'll check the codebase for how signals, edges, and writers are wired so the revised spec matches reality.
## Goal

Give scan-driven tickets and `reports/coupling.md` first-class Mermaid diagrams so change coupling, hidden seams, and refactor hotspots are visible in-context—not only as tables and `[[reports/...]]` links. v1 delivers static coupling subgraphs at scan time (industry graph mental model); temporal trend encoding stays out of scope.

## Approach

Extend the existing Markdown+Mermaid pipeline (`writers.py`, `graphs.py`). Add pure builders over `ScanContext` / `scan.json` inputs (`behavior.coupling`, `seams`, `ranking`, `py_edges`/`ts_edges`, churn/complexity)—no new renderer, no code-maat runtime.

**Path normalization** — Coupling/seams use repo-relative paths; `py_edges`/`ts_edges` use module or path keys. Reuse `behavior._norm_node` and `ranking._module_to_file(line_counts)` when classifying import-backed vs seam edges and when drawing optional 1-hop import edges (same rules as `hidden_seams`).

1. **Report-level coupling network** — `coupling_to_mermaid()` renders top-N pairs as `graph TD`. Seam pairs (no import edge) use dashed red `linkStyle`; import-backed pairs use solid gray. Node IDs via `graphs._node_id`; labels via `writers._chart_label`. Recompute `linkStyle` indices after edge sort/cap.

2. **Ticket-level Evidence block** — `ticket_evidence_diagrams(fingerprint, signals, cfg)` returns Mermaid blocks keyed by fingerprint prefix (skip all when `ticket_diagrams_enabled` is false):
   - `refactor:{file}` — `graph TD` ego subgraph: ticket file node styled distinctly; top coupled neighbors (cap `diagram_max_ticket_neighbors`); edges from coupling degree.
   - `seam:{a}+{b}` — 2-node coupling subgraph; seam edge styled; optional 1-hop import edges from normalized `py_edges + ts_edges`.
   - `size:{file}` — no chart; one-line callout linking to health report (`[[reports/health#...]]`).

3. **Write path** — `write_coupling_report` prepends the network diagram above the table. `write_ticket` inserts `## Evidence` (footnote `_Created {now_date()}_ from scan data_`) before `## Notes` when diagrams are non-empty. `generate_tickets` passes full signals including edges; human/intent tickets skip diagrams.

Diagrams are deterministic at ticket-create time. Existing ticket files are not rewritten—diagrams appear on new auto-tickets only.

## Changes

- **`repo_scan/graphs.py`** — `coupling_to_mermaid(coupling, seams, import_edges, line_counts, *, max_edges)`; `seam_pair_mermaid(a, b, degree, import_edges, line_counts)`; `refactor_ego_mermaid(file, coupling, ranking, *, max_neighbors)`; export or internally share `_node_id`.
- **`repo_scan/writers.py`** — extend `write_coupling_report(root, cfg, coupling, seams, py_edges, ts_edges, line_counts)`; prepend `coupling_to_mermaid` output.
- **`repo_scan/tickets.py`** — `ticket_evidence_diagrams(...)`; extend `write_ticket(..., signals=None)`; thread `signals` from `generate_tickets`.
- **`repo_scan/scanner.py`** — `_write_reports`: pass `ctx.py_edges`, `ctx.ts_edges`, `ctx.line_counts` into `write_coupling_report`. `_maybe_run_tickets`: add `py_edges`, `ts_edges`, `line_counts` to the signals dict.
- **`repo_scan/config.py`** — `ticket_diagrams_enabled` (default `True`), `diagram_max_coupling_edges` (default `20`), `diagram_max_ticket_neighbors` (default `4`).
- **`tests/test_visuals.py`** — builders: seam styling, caps, ego subgraph includes + highlights ticket file, `linkStyle` index stability.
- **`tests/test_writers_snapshots.py`** — refresh `test_coupling_report_snapshot`.
- **`tests/test_tickets.py`** — Evidence section, disabled flag, size callout-only.

## Tests

| Requirement | Test |
|---|---|
| Coupling report includes Mermaid network | `test_writers_snapshots.py::test_coupling_report_snapshot` |
| Seam edges visually distinct from import-backed edges | `test_visuals.py::test_coupling_to_mermaid_styles_seam_edges` |
| Large coupling lists respect edge cap; `linkStyle` matches filtered edges | `test_visuals.py::test_coupling_to_mermaid_respects_max_edges` |
| Refactor ticket embeds ego subgraph with highlighted file | `test_visuals.py::test_refactor_ego_mermaid_highlights_file` |
| Seam ticket embeds pair subgraph | `test_visuals.py::test_ticket_seam_subgraph` |
| Auto-ticket markdown includes Evidence; disabled omits it | `test_tickets.py::test_write_ticket_evidence_diagrams` |
| Size ticket: callout only, no mermaid fence | `test_tickets.py::test_size_ticket_evidence_callout_only` |
| Output uses `graph TD` only (no `quadrantChart` in ticket Evidence) | `test_tickets.py::test_evidence_no_quadrant_chart` |

## Documentation

- **`README.md`** — Tickets: auto-tickets include Evidence diagrams; coupling report has a network diagram; `ticket_diagrams_enabled` disables them.
- **`repo_scan/graphs.py`** — docstrings on builders (inputs, `_norm_node` / `_module_to_file`, seam styling, caps, `linkStyle`).
- **`repo_scan/tickets.py`** — `write_ticket` / `ticket_evidence_diagrams` docstrings (fingerprint mapping, no overwrite).
- **`docs/changelog/`** — ticket Evidence diagrams and coupling graph.

## Risks

- **Scale** — uncapped graphs break GitHub/Obsidian rendering; caps and basename labels are mandatory.
- **Staleness** — diagrams frozen at ticket creation; rescans do not update open tickets.
- **`linkStyle` order** — indices are position-sensitive; must be rebuilt after sort/filter.
- **False-positive seams** — relative-import resolution gaps (e.g. scanner.py↔writers.py) can show misleading seam edges until import-graph fixes land.
- **Snapshot churn** — syrupy fixtures for `coupling.md` and ticket samples need intentional updates.

## Out of scope

- Temporal coupling trends (strengthening/weakening edges over sliding git windows).
- Interactive graphs, hub UI, or non-Mermaid renderers.
- Backfilling Evidence into existing tickets.
- Diagrams for human `new_ticket` / radar intent tickets without scan signals.
- `quadrantChart` / `xychart-beta` in ticket Evidence (health report quadrant unchanged).
- code-maat as a runtime dependency.

## Audit

> [!warning] Audit verdict: revise
> The spec aligns well with existing Mermaid writers, coupling/seam signals, and fingerprinted tickets, but needs wiring fixes (signals kwargs, import layering), sharper caps/anchors, and explicit handling of omitted ticket kinds before human review.
> - Extending the `signals` dict with `py_edges`/`ts_edges` and passing it to `propose_from_scan(cfg, **signals)` will raise `TypeError` unless extra keys are stripped or `propose_from_scan` is updated—the spec does not address this wiring.
> - Placing `coupling_to_mermaid` in `graphs.py` while labeling via `writers._chart_label` and calling it from `write_coupling_report` in `writers.py` introduces a writers↔graphs circular-import risk; Risks omit this and do not say to move the label helper (e.g. to `utils`).
> - Size-ticket callout `[[reports/health#...]]` has no defined anchor scheme—`health.md` has section headings only, not per-file anchors.
> - Seam-ticket optional 1-hop import edges have no node/edge cap; a high fan-in file can still blow past the stated scale limits.
> - `linkStyle` is new to the repo with no prior GitHub/Obsidian parity check; seam-vs-import styling may not render consistently across viewers.
> - Coupling table is hardcoded to `coupling[:20]` while the diagram uses `diagram_max_coupling_edges` (default 20)—no rule to keep them aligned when config changes.
> - `tests/test_scanner_snapshots.py` builds golden `coupling.md` via `write_coupling_report` for E2E comparison; Changes/Tests only mention `test_writers_snapshots`, so scanner characterization updates are missing.
> - Research lists refactor quadrant highlights and gitGraph/timeline as low-hanging ticket aids; spec drops them without listing them as deferred follow-ups, so the ticket option menu from intent is only partly reflected.
> - Auto-ticket kinds `stale:` and `silo:` are not covered—Evidence behavior is unspecified for two of five `propose_from_scan` proposal types.
> - Source problem acceptance criteria remain Tbd; the spec supplies a test matrix but no reviewer-facing acceptance criteria.
> - `## Evidence` body section overlaps semantically with frontmatter `evidence:` wikilinks—naming collision risk for humans and future parsers.

## Provenance

- analysis: [[2026-06-10-i-want-to-add-a-more-robust-way-to-visua-analysis]]
