# 2026-06-10 — C1 behavioral metrics + C2 tickets engine

GitHits research (code-maat, wily, jscpd, git-of-theseus, Backlog.md,
obsidian-tasks, Kanban plugin, todo-to-issue) shaped both phases — see the
assessment-metrics-and-tickets-roadmap canvas.

## C1 — Behavioral metrics from git history (`repo_scan/behavior.py`)

One `git log --numstat` pass yields three signals static analysis can't see:

- **Change coupling** (code-maat degree formula: shared commits / average
  revisions). Mass changesets (>30 files) excluded as noise. Threshold
  config: `coupling_min_shared` (4), `coupling_min_degree` (50%).
- **Hidden seams**: coupled pairs with *no import edge* (normalized across
  Python dotted modules and TS paths) — implicit contracts the dependency
  graph can't see. First real finding: `pyproject.toml ↔ setup.py` are 100%
  coupled in this repo (duplicated packaging metadata).
- **Ownership / bus factor**: per-file author concentration; silo = one
  author, ≥5 commits, ≥90% share (`silo_min_share`).
- **Code age**: days since last touch; stale threshold `stale_days` (180).

Outputs: `reports/coupling.md` (seam warnings + pair table), "Knowledge map"
section in `health.md` (silo/stale flags), `behavior` block in `scan.json`.

## C2 — Tickets engine (`repo_scan/tickets.py`)

The vault is the tracker: one markdown file per ticket in `docs/tickets/`.

- **Format**: YAML frontmatter (id, title, status, origin auto|human,
  source, priority, fingerprint, evidence wikilinks, created, tags) +
  `## Why` + `## Acceptance criteria` checkboxes. Dataview-queryable;
  evidence wikilinks join the Obsidian graph.
- **Auto-proposal** from five signal sources, strongest first: refactor
  (churn × complexity, untested → high priority), hidden seam, oversized
  file, stale hub (top-5 rank + old), knowledge silo (only when the repo
  has >1 contributor). Capped per scan (`tickets_max_new_per_scan`, 5).
- **Dedup**: content-stable fingerprints (`signal:file`); a fingerprint in
  ANY status — including rejected — is never re-proposed. Saying no sticks.
- **Board**: `tickets/board.md` in Obsidian Kanban-plugin format, columns
  per status, cards as wikilinks. Regenerated every scan from ticket files
  (ticket files stay the single source of truth).
- **Human tickets**: any `.md` with `status` frontmatter is loaded and
  boarded alongside auto tickets.
- Lifecycle: `proposed → approved → in-progress → done` / `rejected`.

## Dogfooding results

- This repo: 8 tickets — top one is "Refactor writers.py (CC 52, untested)",
  plus the pyproject/setup.py seam.
- hhl_site: "Refactor PageSection.tsx (CC 42, 42 commits, untested)" #1,
  "Split DataPipeline.tsx (1433 lines)", and a contact↔services seam.

## Verification

- 13 new tests (`test_behavior.py`: coupling/ownership/age/mass-changeset/
  seam normalization/e2e; `test_tickets.py`: proposal types, silo guard,
  dedup+cap, rejection suppression, human tickets, id roundtrip, scan e2e).
- Full suite: 109 passed.
