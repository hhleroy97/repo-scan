---
type: north-star
updated: "2026-06-10"
tags: [strategy, radar, knowledge-graph]
---

# North star — knowledge graph as ground truth

## Mission

Offer a **robust, git-committed knowledge graph** where external sources and scan
metrics flow into linked, auditable documentation that humans and agents treat as
ground truth — either referenced (wikilinks, evidence) or brought in (ingested
sources, specs, changelogs).

Success means: every meaningful change traces to real evidence, every agent pass
leaves a durable artifact, and the repo's `docs/` vault is more trustworthy than
ephemeral LLM context.

**Distilled principles:** [[research/theory]]

**Technical reference:** [[RADAR_CONTEXT]]

---

## Ground-truth hierarchy

When artifacts conflict, precedence is:

1. **Ticket markdown** (`docs/tickets/tkt-*.md`) — work item, acceptance criteria, status
2. **Approved spec** (`docs/specs/*`, `status: approved`) — implementation contract
3. **Analysis** (`docs/research/analysis/*`) — synthesized findings for one problem
4. **Source human notes** (`docs/research/sources/*` below `## Notes`) — curated claims
5. **scan.json** — machine-readable structural truth (metrics, edges, seams)
6. **Derived indexes** — `index.md`, `research/index.md`, PM cards, `candidates.md`
7. **Ephemeral context** — `repo_snapshot()`, in-flight prompts (never canonical)

Derived views are regenerated; never edit them to "fix" truth.

---

## Graph linking contract

| Artifact | Link field | Target |
|----------|------------|--------|
| Source | `linked_files` in frontmatter | Code paths as `[[path]]` ghost nodes |
| Ticket | `evidence` | Reports, sources, diagrams |
| Analysis | `## Evidence` | `[[research/sources/...]]` wikilinks |
| Spec | `analysis:` frontmatter | Provenance cluster in Obsidian |

**Target:** every approved spec traces to ≥1 ingested source and ≥1 metric signal
(ticket evidence or scan-derived ticket).

---

## Three-way balance

RADAR optimizes three competing objectives. Telemetry in `docs/.radar/` feeds
these proxies.

| Objective | Proxy metrics | Config knobs |
|-----------|---------------|--------------|
| **Time to response** | Stage `duration_ms`, gate wait, run wall clock | `llm_timeout`, `llm_heartbeat_seconds`, gate `auto` |
| **Token burn rate** | tok/min per stage, role, run; daily budget headroom | `llm_roles`, `repo_snapshot_max_chars`, `max_sources` |
| **Output quality** | Audit verdict, criteria coverage, post-merge metric delta, tests | audit revise cap, act fix rounds, human gates |

### Initial posture

- **Research / analyze** — higher token budget; cheaper model acceptable
- **Draft / audit** — quality-first model routing
- **Act** — bounded fix rounds; doc drift check before merge
- **Gates** — human time is an acceptable quality cost until trust earns `auto`

Tune from `stages.jsonl` and `usage.jsonl` rollups on the hub Activity tab.

---

## Context surfaces

| Surface | Audience | When to use |
|---------|----------|-------------|
| `scan.json` | Tools, agents, reports | Full structural truth; trend diffs |
| `digest.md` | LLM with tight budget | Single-file export |
| `repo_snapshot()` | In-flight prompts | Fresh ranked context; not committed |
| `research/sources/*.md` | Humans + analyze stage | External claims with provenance |
| `theory.md` | Humans | Distilled beliefs between sources and specs |

---

## Lifecycle

```
scan → ticket (auto-propose) → loop (research→analyze→draft→audit)
     → spec (approved) → act → PR → merge → rescan → trend delta
```

Ground truth updates at: ingest (sources), analyze (findings), record (spec),
act (code + changelog), rescan (metrics).

---

## Current vs planned

| Area | Today | Planned |
|------|-------|---------|
| Ingest fetchers | arxiv, github, url, file | npm, HN, Semantic Scholar |
| Metric-triggered loop | Tickets auto-propose; manual loop | Threshold auto-fire |
| `linked_files` | Mostly manual | Auto-suggest at analyze |
| Telemetry | Per-LLM usage ledger | Per-stage timing + burn rate |
| Theory layer | `theory.md` (this milestone) | Human-curated, agent-suggested |
