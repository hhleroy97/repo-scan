# Knowledge graph viewer — roadmap

_Why Obsidian Mermaid is not enough, and where the interactive graph lives next._

**Related:** [[architecture/agentic-loop]] · [[NORTH_STAR]] · [[reports/dependencies]]

---

## Problem

Obsidian is a strong **vault editor** but a weak **graph runtime**:

| Limitation | Effect on repo-scan |
|------------|---------------------|
| Mermaid fixed layout | Horizontal scroll on `graph LR` and wide sequence diagrams |
| No pan/zoom on embedded charts | Agentic loop unreadable on phone/narrow panes |
| Local graph ≠ semantic graph | Obsidian's graph shows wikilinks, not import edges, ticket→spec→source provenance |
| No live run overlay | Cannot see which ticket/loop/act is active on the diagram |
| Static at scan time | `scan.json` and coupling data are not interactive in Obsidian |

The **ground truth** stays in git (`docs/`, `scan.json`). We need a **viewer** that
renders structure and provenance without fighting the editor pane.

---

## Short-term (now) — documentation without horizontal scroll

1. **ASCII-first** diagrams in [[architecture/agentic-loop]] — primary in Obsidian.
2. **Vertical Mermaid only** (`graph TD`) inside collapsible `<details>` blocks.
3. **Tables** for gates, stages, and hierarchy — no layout engine required.
4. README keeps one vertical lifecycle + table; links here for depth.

**Status:** done — ASCII docs validated in vault.

---

## Medium-term — hub dashboard (MVP shipped)

Live on **`radar serve`** → **Dashboard** tab (`GET /api/graph`). Vault audit panels
(signal matrix, histogram, untracked queue) plus mobile-first canvas
with pan/zoom, layer filter (All / Vault / Code), collapsible agentic-loop
pipeline, tap-to-open vault docs. No CDN — inline canvas + force layout.

### MVP scope (implemented)

| Layer | Source | View |
|-------|--------|------|
| **Code structure** | `scan.json` import/call edges | Pan/zoom dep graph (reuse Mermaid data or JSON edges) |
| **Agentic loop** | static contract | Vertical pipeline UI (CSS steps — same content as ASCII doc) |
| **Vault provenance** | wikilinks in tickets/specs/sources | ticket → spec → analysis → source edges |
| **Live state** | hub `build_state()` | highlight active run, waiting gate, open ticket |

### Implementation sketch

```
repo_scan/hub/
  graph.py          # build_graph_state() from scan.json + vault parse
  ui/_graph.py      # Cytoscape.js or pure SVG; pinch-zoom on mobile
  server.py         # GET /api/graph  +  #graph tab
```

**Why hub first:** same auth/session as gates and tickets; `scan.json` already
machine-readable; no new deployment target; validates graph UX before a standalone app.

### Library options (hub frontend)

| Tool | Fit | Trade-off |
|------|-----|-----------|
| **Cytoscape.js** | Proven pan/zoom, layouts, mobile | ~300 KB CDN; best for MVP |
| **vis-network** | Fast force layout | Heavier styling; good for large graphs |
| **D3 force** | Maximum control | More code to maintain |
| **Mermaid runtime** | Reuse existing diagrams | Still poor pan/zoom; not recommended for primary viewer |
| **Neo4j / Kuzu** | Query-heavy graphs at scale | Overkill until vault edges exceed ~5k |

**Recommendation:** Cytoscape.js on hub for MVP; defer graph DB until provenance queries
need Cypher/GSQL.

---

## Phase 5 — knowledge audit dashboard (shipped)

Turns the Graph tab into a **trust signal** for vault docs:

| Feature | Source | UI |
|---------|--------|-----|
| **Provenance scoring** | `repo_scan/provenance.py` | Coverage layer — score rings (0–3, fresh is vanity) |
| **Signal matrix** | `coverage.signal_matrix` | Per-kind pass % for E/L/C (fresh shown but unscored) |
| **Score histogram** | `coverage.score_histogram` | Bar chart of docs by score |
| **Untracked queue** | `coverage.untracked_ranked` | Ranked code missing vault backlinks |
| **Closed-loop edges** | `cites` + `linked_file` | Green solid = doc↔code both ways |
| **Provenance chain** | `GET /api/graph/chain?id=…` | E/L/C checklist + stale strip per row |

**Status:** done — see `docs/changelog/2026-06-11-vault-provenance.md`.

### Post-launch improvements (shipped)

| Feature | Source | UI |
|---------|--------|-----|
| **Trend sparklines** | `S.trend_sparkline` | Mini SVG on vault-% and files cards |
| **Knowledge debt score** | `coverage.knowledge_debt` | 0–100 composite card (coverage + stale + untracked) |
| **Approved-but-unhealthy badge** | `coverage.approved_unhealthy` | Inline warning count on stale-docs card |
| **Last-scan delta** | `S.vault_delta` | ↑/↓ arrows on vault-% and untracked cards |
| **Orphan drill-down** | matrix cell `onclick` | Click any signal-matrix cell to filter graph by that signal |
| **Fragile code links** | `coverage.thin_citations` | Collapsible list of files with ≤1 vault citation |
| **Scan trend chart** | `S.trend_sparkline` | Full SVG chart of vault-% and file count over last 12 scans |
| **Run history on loop** | `classDef completed` | Green trail showing last completed run stages on Mermaid diagram |
| **Governance risk badge** | `chain[].governance_risk` | "approved but unhealthy" badge in chain panel for low-score specs |

---

## Long-term — dedicated knowledge graph (if hub MVP succeeds)

Trigger a separate graph service when:

- Vault has **>500** provenance edges and hub JSON payloads lag
- You need **retrospective queries** ("all specs touching file X that cited source Y")
- Multiple repos share one graph

Candidates:

| System | Role |
|--------|------|
| **Kuzu** | Embedded graph DB, SQL/GQL, ships with Python — fits file-backed vault |
| **Neo4j** | Mature, best tooling, hosted Aura option |
| **Memgraph** | Real-time analytics, stream-friendly |

Vault markdown remains canonical; the graph DB is a **derived index** (like
`scan.json`), rebuilt on rescan/ingest.

---

## Decision gate

| Result | Next step |
|--------|-----------|
| ASCII + tables readable in Obsidian | Keep vault docs as ground truth; prioritize hub **Loop** pipeline tab |
| Hub pipeline tab used on phone | Add **Graph** tab with `scan.json` import graph + provenance overlay |
| Graph tab daily driver | Spec Kuzu/Neo4j derived index + cross-repo queries |
| Graph tab unused | Stay on ASCII docs + `reports/*.md` Mermaid exports for code structure |

---

## Out of scope (for now)

- Replacing Obsidian as the vault editor
- Auto-layout Mermaid fixes in Obsidian (upstream; not reliable)
- GraphQL API before hub MVP proves the UX

Track implementation in planning when a phase is opened; link from [[NORTH_STAR]] planned table.
