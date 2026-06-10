---
type: plan
phase: 5
title: "Week 5 — Knowledge audit dashboard"
status: shipped
tags: [planning, hub, graph, provenance, vault]
linked_research:
  - "[[NORTH_STAR]]"
  - "[[architecture/agentic-loop]]"
  - "[[architecture/graph-viewer-roadmap]]"
---

# Phase 5 — Knowledge audit dashboard

**Goal:** Turn the hub Graph tab from a viz into a **trust signal** — prove that
docs in `docs/` are connected to ground truth (code, sources, tickets) and
surface orphans before they rot the vault.

**Why now:** Phase 4 shipped the graph viewer. The graph already has the nodes
and edges; what's missing is the **provenance health story** the user reads at
a glance.

**Non-goals:**
- Derived graph DB (Kuzu) — deferred until provenance edges > 500
- LLM-driven doc generation — manual `linked_files` stays primary
- Replacing Obsidian — vault editing stays in Obsidian

---

## Ground-truth contract (what we are validating)

A doc earns its place in the vault when it can answer **all four** of:

| Check | Where it lives | How we detect |
|-------|----------------|---------------|
| **Traces upstream** | spec → analysis → source; ticket → spec | wikilinks in frontmatter + body |
| **Anchors to code** | source/spec `linked_files:` resolve in `scan.json` | path lookup |
| **Code acknowledges back** | `cites: docs/...` markers in `.py` files or commits | repo grep at scan |
| **Stays fresh** | doc mtime vs last commit touching linked file | `scan.json` `age_days` + git |

A node missing any of the four is an **orphan candidate** — surfaced in the
graph as a red ring, listed in a coverage report, and counted as a metric so
"vault health" trends scan-over-scan.

---

## Task 5.1 — Provenance scoring backend

**Files:**
- `repo_scan/provenance.py` — new module, pure scoring
- `repo_scan/hub/graph.py` — attach scores to nodes
- `tests/test_provenance.py` — new

**Module surface:**

```python
def score_node(node: dict, root: Path, cfg: dict, scan: dict, citations: dict)
  -> dict
    # returns {"signals": ["evidence","linked","cited","fresh"],
    #          "score": 0..4, "missing": ["cited"], "stale_days": int|None}

def vault_coverage(root: Path, cfg: dict) -> dict
    # returns {"docs": N, "scored_by_kind": {...},
    #          "orphans": [...], "untracked_code": [...],
    #          "coverage_pct": float}
```

**Signals (cheap to compute):**

1. **evidence** — has frontmatter `analysis:` (spec) / `## Evidence` block (ticket) /
   cites `[[sources/...]]` (analysis)
2. **linked** — `linked_files:` frontmatter values exist in `scan.json` files
3. **cited** — code grep finds doc stem in `.py` comments/docstrings (see 5.2)
4. **fresh** — `max(linked_file age_days) <= doc_age_days + grace` (default 14 days)

**Acceptance criteria:**
- [ ] `score_node` returns 0–4 plus the missing signal list
- [ ] `vault_coverage` summarizes by kind (ticket/spec/analysis/source)
- [ ] Missing `scan.json` → all docs score 0 on `linked` (no crash)
- [ ] Orphan list excludes nodes with score == 4
- [ ] Pure-Python; no new deps

**Tests:**
- `test_score_full_chain_scores_four`
- `test_missing_linked_files_drops_signal`
- `test_stale_doc_loses_fresh_signal`
- `test_vault_coverage_counts_orphans_by_kind`
- `test_untracked_code_excludes_tests_and_docs`

---

## Task 5.2 — Code → doc citation scanner

**Problem:** Today only docs → code edges exist (`linked_files`). For the
"code acknowledges back" signal we need the reverse direction.

**Files:**
- `repo_scan/citations.py` — new scanner
- `repo_scan/scanner.py` — call during scan, write to `scan.json` under `citations`
- `tests/test_citations.py` — new

**Detection rules (no false-positive frenzy):**

| Marker | Example | Mapped to |
|--------|---------|-----------|
| Doc path in comment | `# see docs/specs/foo-spec.md` | spec foo-spec |
| Wikilink in docstring | `"""[[tkt-0042]]"""` | ticket tkt-0042 |
| `spec: <stem>` tag | `# spec: foo-spec` | spec foo-spec |
| `ticket: tkt-####` tag | `# ticket: tkt-0042` | ticket |

Walk Python (and TS later) source. Drop anything not pointing at a real vault
file. Cap citations per file at 20 to bound noise.

**Acceptance criteria:**
- [ ] `scan.json["citations"]` lists `{file, target_kind, target_id, line}` rows
- [ ] Scanner skips `docs/`, `tests/*.py` that only assert text presence
- [ ] Adds < 200 ms to a 100-file scan
- [ ] Unresolved targets dropped silently (logged at debug)

**Tests:**
- `test_detects_comment_path_reference`
- `test_detects_wikilink_in_docstring`
- `test_excludes_tests_directory_by_default`
- `test_unresolved_references_dropped`

---

## Task 5.3 — Graph tab coverage view

**Files:**
- `repo_scan/hub/graph.py` — include score + missing fields per node
- `repo_scan/hub/ui/_graph.py` — coverage layer + score rings
- `repo_scan/hub/ui/_css.py` — score ring colors
- `tests/test_hub_graph.py` — assertions for scored payload
- `tests/test_hub_ui.py` — assert `coverage` button present

**UI changes:**

1. Add **Coverage** layer button next to All/Vault/Code. When active:
   - Vault nodes shown; code nodes dimmed unless cited
   - Node ring color = score (0=red, 1-2=amber, 3=blue, 4=green)
   - Hover/tap → score breakdown ("missing: cited, fresh")
2. Toolbar summary: `"42/58 docs healthy (72%)"` from `vault_coverage`
3. Node label suffix `★0` … `★4` (subtle) when in coverage layer

**Acceptance criteria:**
- [ ] Coverage layer renders score rings without re-laying out
- [ ] Tapping a low-score node still opens its doc
- [ ] `coverage_pct` shown in toolbar matches `vault_coverage` server value
- [ ] Test suite covers byte-parity hash update + line cap ≤ 300

**Tests:**
- `test_dashboard_has_coverage_layer`
- `test_graph_payload_includes_node_scores`
- `test_vault_coverage_endpoint_returns_pct`

---

## Task 5.4 — Provenance chain panel

**Files:**
- `repo_scan/hub/ui/_graph.py` — slide-up panel renderer
- `repo_scan/hub/graph.py` — `/api/graph/chain?id=...` (or include eager in payload for small graphs)
- `tests/test_hub_graph.py` — chain endpoint shape

**Behavior:** Tap any node → slide-up panel (mobile-first) shows the full chain:

```
ticket tkt-0042  ★3  missing: fresh
  └─ spec foo-spec  [approved 2026-06-08]  ★4
      └─ analysis foo-analysis  [confidence high]  ★3
          ├─ source arxiv:2305.12345  ★2
          └─ source github:org/repo  ★4
              └─ code repo_scan/radar/gates.py  [a5106e2, 0d ago]
```

Each row tappable → opens that doc. Bottom action: "Open in Obsidian" (deep
link `obsidian://open?vault=...&file=...`) — opt-in via config.

**Acceptance criteria:**
- [ ] Panel walks ticket → spec → analysis → source → code in order
- [ ] Missing signals shown per row (badge or "missing: X")
- [ ] Tap dismisses; backdrop closes
- [ ] Reuses existing `openDoc` for vault reads
- [ ] Works when chain has gaps (renders what exists)

**Tests:**
- `test_chain_walks_ticket_to_code`
- `test_chain_renders_with_missing_links`
- `test_dashboard_has_chain_panel`

---

## Task 5.5 — Vault health metric in `scan.json` + trend

**Files:**
- `repo_scan/writers.py` — write `vault_health` block into `scan.json`
- `repo_scan/trends.py` — track `vault_coverage_pct` and `untracked_code_count`
- `docs/reports/health.md` — new "Vault health" section
- `tests/test_trends.py` — trend assertions

**Payload:**

```json
"vault_health": {
  "coverage_pct": 0.72,
  "score_histogram": {"0": 3, "1": 5, "2": 8, "3": 12, "4": 30},
  "orphans_by_kind": {"source": 2, "spec": 1, "analysis": 0, "ticket": 0},
  "untracked_code_count": 14,
  "stale_docs_count": 6
}
```

**Acceptance criteria:**
- [ ] `health.md` opens with vault-health table + verdict callout
- [ ] Trend graph entry per scan (existing trends pipeline)
- [ ] Coverage delta surfaced in `since last scan` callout when ≥ 5%
- [ ] Falls back gracefully when `provenance.py` returns empty

---

## Task 5.6 — Documentation + UAT

**Files:**
- `README.md` — short paragraph under Knowledge graph section
- `docs/architecture/graph-viewer-roadmap.md` — flip Phase 5 items to "shipped"
- `docs/NORTH_STAR.md` — update Current/Planned table
- `docs/changelog/2026-06-11-vault-provenance.md`
- `docs/changelog/2026-06-11-citation-scanner.md`

**UAT script:**
1. Open hub → Graph → Coverage layer
2. Find a low-score node, confirm ring color and breakdown
3. Tap → confirm chain panel walks upstream
4. Run `repo-scan` → confirm `vault_health` block in `scan.json`
5. Check `reports/health.md` opens with vault-health verdict
6. Add a fake `# spec: foo-spec` to a code file → rescan → ticket "foo-spec" gains the `cited` signal

---

## Phase 5 — out of scope

- LLM-suggested `linked_files` (deferred; NORTH_STAR "Planned")
- Graph DB derived index (Kuzu / Neo4j) — gated on edge count
- Editing docs from the hub
- Auto-fix for orphan docs (manual review stays the contract)
- TypeScript citation scanning (Python first; mirror the API later)

---

## Suggested build order

1. **5.1 + 5.2 sequentially** — scoring needs citations data. Single PR per task with tests.
2. **5.5** before UI — landing `vault_health` in `scan.json` lets `health.md` and TUI surface the data immediately, even without the new graph view.
3. **5.3** — coverage layer (visual win, builds on backend).
4. **5.4** — chain panel (deepest UX; iterative on top of coverage).
5. **5.6** — docs/changelog/UAT at the end.

**Commit strategy:** one commit per task, atomic. Changelog entry per logical
feature (provenance scoring + citations together, then UI tasks separately).

---

## Review checklist (for human)

- [ ] Four signals (evidence/linked/cited/fresh) capture "ground truth"? Add or drop any?
- [ ] Freshness grace window — 14 days reasonable? Lower for hot files (rank ≥ tier 1)?
- [ ] Citation markers — start with comment paths + wikilinks only, defer `cites:` tag convention until adoption?
- [ ] Coverage layer default vs explicit toggle?
- [ ] Chain panel: eager-load with `/api/graph` or lazy `/api/graph/chain?id=`?
- [ ] `obsidian://` deep links — opt-in flag in `.repo-scan.json` (`obsidian_vault_name`)?
- [ ] Acceptance: ship behind `vault_audit_enabled: true` first scan, or default on?
