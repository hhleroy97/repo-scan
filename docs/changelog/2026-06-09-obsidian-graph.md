# 2026-06-09 — Obsidian graph: frontmatter + provenance links

Follow-on to B4. Graph view only renders resolved wikilinks, and radar's
artifacts were link-sparse — causally related files (run → analysis → spec)
weren't connected. This change makes every loop run a visible provenance
cluster and unlocks Dataview queries.

## What changed

- **Source notes use YAML frontmatter** — metadata moved from an opaque
  ```source code block to real frontmatter (`id`, `type`, `url`, `tags`,
  `linked_files`, `relevance`, `ingested_at`). Obsidian now sees tags as tag
  nodes and properties as Dataview-queryable fields. Tags are slugified
  (`Multi Agent` → `multi-agent`); `linked_files` emit `[[path]]` wikilinks so
  code files appear as ghost nodes clustering their related sources.
  Stdlib-only frontmatter writer/parser (quoted scalars survive colons in
  URLs/titles); `## Notes` preservation unchanged.
- **Provenance cross-links** — each pipeline stage now wikilinks its evidence:
  - analysis → ingested sources + research run log (`## Evidence` section +
    `sources` frontmatter)
  - spec → analysis (`## Provenance` section + `analysis` frontmatter)
  - gate decisions in `decisions.md` → the analysis (Gate 1) / spec (Gate 2)
  - loop changelog entries → the spec
- **Unambiguous bare links** — analysis and spec filenames get `-analysis` /
  `-spec` suffixes; previously all three per-run artifacts shared the same
  date-slug name, which would have made bare wikilinks ambiguous.
- **Frontmatter on run logs** (`type: research-run`, question, source ids) and
  specs (`type: spec`, status, audit verdict) for Dataview.
- GitHub source titles truncated to ~80 chars (full description was becoming
  the note title); index table titles capped at 90.

## Verification

- 2 new tests + extended loop e2e (64 total): frontmatter round-trip with
  colons/lists, Obsidian-format source notes, and full cluster assertions
  (spec ↔ analysis ↔ sources/run, decisions linking both, stems unambiguous).
- Live repomix source re-ingested into the new format; rescan clean.

## Using it in Obsidian

- Local graph (depth 1–2) on any spec/source is the daily tool; global graph
  groups: color by `path:research`, `path:specs`, `path:reports`.
- Dataview example: `TABLE confidence FROM "docs/research/analysis" WHERE type = "analysis"`.
