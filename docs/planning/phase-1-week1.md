---
type: plan
phase: 1
title: "Week 1 — Bridge UI and agent freshness"
status: ready-for-review
tags: [planning, ui, research, repo-snapshot, diagrams]
linked_research:
  - "[[url-aider-chat-docs-repomap]]"
  - "[[url-humanlayer-advanced-context-engineering]]"
  - "[[url-githits-repo-snapshot-token-budget]]"
  - "[[url-githits-mermaid-coupling-subgraph]]"
  - "[[gh-mermaid-js-mermaid]]"
---

# Phase 1 — Bridge UI and agent freshness

**Goal:** Land the in-flight diagram feature, give RADAR stages a ranked live repo
snapshot (not stale one-liners), and make the phone dashboard show what agents
are doing *right now* without waiting for Phase 3 SSE.

**Research basis (GitHits + existing vault):**

| Source | Takeaway for this phase |
|--------|-------------------------|
| [[url-aider-chat-docs-repomap]] | Ranked symbol map + token budget, not whole-repo dump |
| [[url-humanlayer-advanced-context-engineering]] | Fresh context at research boundary; research ≠ implement |
| [[url-githits-repo-snapshot-token-budget]] | Digest dedup on `scan.generated_at` + git HEAD |
| [[url-githits-mermaid-coupling-subgraph]] | Subgraph coupling diagrams validate tkt-0012 spec |
| [[gh-mermaid-js-mermaid]] | Renderer/ecosystem reference (already ingested) |
| Approved spec [[2026-06-10-i-want-to-add-a-more-robust-way-to-visua-spec]] | Implementation contract for task 1.1 |

---

## Task 1.1 — Merge PR #11 (ticket Evidence diagrams)

**Why first:** Unblocks visual UX in Obsidian *and* richer ticket cards; code is
implemented, CI green, mergeable.

**Steps:**
1. From hub phone or CLI: squash-merge PR #11 (`radar/tkt-0012`)
2. `git pull --ff-only` on hub machine
3. Update tkt-0012: replace `Tbd` criteria with real checkboxes from spec Tests table
4. Set tkt-0012 → `done` after rescan confirms diagrams in new auto-tickets
5. Restart `radar serve` if needed

**Acceptance criteria:**
- [ ] `coupling.md` opens with Mermaid network (seam edges dashed red)
- [ ] New auto-proposed refactor/seam ticket includes `## Evidence` with diagram
- [ ] `ticket_diagrams_enabled: false` omits Evidence (existing test)
- [ ] tkt-0012 ticket criteria no longer `Tbd`

**Tests:** existing `test_visuals.py`, `test_tickets.py`, snapshot refresh — should pass on main after merge.

**Files (on branch, verify after merge):** `repo_scan/graphs.py`, `writers.py`, `tickets.py`, `scanner.py`, `config.py`

---

## Task 1.2 — `repo_snapshot()` injected into research + analyze

**Problem:** `repo_context_snippet()` (`research.py`) sends ~5 lines from
`scan.json`. Parallel loops and long gate waits leave analyze/draft working on
stale mental models.

**Design (Aider-informed, repo-scan-native):**

Add `repo_snapshot(root, cfg) -> str` in `repo_scan/radar/research.py`:

```
## Repo snapshot (generated {scan.generated_at}, main@{short_sha})
Languages: {languages}
Hotspots (rank × churn × complexity):
  - {file} — rank #{n}, {lines} lines, tests: {yes|no}, churn {c}
Open tickets: {id}: {title} ({status}) × up to 5
Metric deltas (if trends.md / scan delta available): top 3 regressions
Coupling alert: top seam pair if any
Digest: {first 800 chars of digest.md or health.md summary}
```

**Injection points:**
1. `PROPOSE_PROMPT` — replace/extend `{repo_context}` block
2. `ANALYZE_PROMPT` in `pipeline.py` — new `{repo_snapshot}` section
3. Optional: `DRAFT_PROMPT` one-liner "snapshot as of {timestamp}"

**Dedup (PraisonAI pattern):** `repo_snapshot_digest(root)` = hash of
`scan.generated_at` + `git rev-parse HEAD`. Store last digest in checkpoint;
skip re-building prose if unchanged within same loop.

**Config:** reuse `digest_tokens` cap (default 4000) for snapshot max chars;
new key optional `repo_snapshot_max_chars` (default 2500).

**Acceptance criteria:**
- [ ] New loop research stage prompt includes snapshot when `scan.json` exists
- [ ] Analyze stage always receives snapshot even when research checkpoint resumes
- [ ] Parallel loops on different tickets see same snapshot for same scan+HEAD
- [ ] Missing scan.json degrades to current one-liner (no error)
- [ ] Snapshot never includes full file contents (map philosophy per Aider)

**Tests (new `tests/test_repo_snapshot.py`):**
- `test_snapshot_includes_ranking_and_tickets`
- `test_snapshot_digest_stable_for_same_scan`
- `test_snapshot_degrades_without_scan_json`
- `test_analyze_prompt_receives_snapshot` (mock/fake LLM captures argv or prompt file)

**Files to touch:**
- `repo_scan/radar/research.py` — `repo_snapshot`, `repo_snapshot_digest`, extend `repo_context_snippet`
- `repo_scan/radar/pipeline.py` — `ANALYZE_PROMPT`, wire snapshot
- `repo_scan/config.py` — optional `repo_snapshot_max_chars`
- `README.md` — one paragraph under RADAR
- `docs/changelog/2026-06-10-repo-snapshot.md`

---

## Task 1.3 — Live run panel on Now tab (polling upgrade)

**Problem:** `stage` / `stage_detail` are written by `progress.py` and shown in
`radar top`, but the phone Now tab buries them in a small dim line inside the
run list. Users poll every 12s and cannot tell if agents are alive.

**Design (SSE deferred — see [[url-githits-sse-stdlib-dashboard]]):**

**Server (`build_state`):** add `live_runs` — filter `runs` where
`status in (queued, running, waiting-on-gate)` with full `stage`, `stage_detail`,
`ticket`, `kind`, `gate`, `updated_at`.

**Client (`ui.py`):**
1. New `rLiveRuns()` section at top of Now tab — card per active run:
   - Large status dot + ticket id
   - Stage as headline (`[3/7] Draft`)
   - Detail as subline (`composer-2.5 · still working · 6m elapsed`)
   - Gate name if `waiting-on-gate`
2. Adaptive poll: `setInterval(refresh, hasLiveRuns ? 3000 : 12000)`
3. Last event from feed matching run problem shown inline

**Acceptance criteria:**
- [ ] Active act run shows stage_detail within 3s on phone without opening TUI
- [ ] No active runs → poll stays 12s (no extra load)
- [ ] `formBusy()` still prevents wipe during ticket composer input
- [ ] Waiting-on-gate runs show gate name prominently + link to Gates tab

**Tests:**
- `tests/test_hub.py::test_build_state_live_runs` — running run appears in `live_runs`
- Manual UAT: start act, confirm Now tab updates stage text

**Files:**
- `repo_scan/hub/server.py` — `build_state` adds `live_runs`
- `repo_scan/hub/ui.py` — `rLiveRuns()`, adaptive poll
- `docs/changelog/2026-06-10-live-run-panel.md`

---

## Phase 1 — out of scope

- SSE `/events` endpoint (Phase 3)
- Pre-act context bundle (Phase 2)
- Record stage post-merge (Phase 2)
- Hub-rendered Mermaid (spec explicitly out of scope; Obsidian/GitHub render)
- Backfill Evidence into existing tickets

---

## Suggested build order

1. Task 1.1 (merge) — 15 min human + verify
2. Task 1.2 (repo_snapshot) — core agent freshness, ~1 session
3. Task 1.3 (live panel) — UX payoff, ~half session

**Commit strategy:** one commit per task + changelog each.

---

## Review checklist (for human)

- [ ] Agree with snapshot fields (ranking, tickets, deltas, digest)?
- [ ] `repo_snapshot_max_chars` default 2500 OK?
- [ ] 3s poll when live acceptable for Tailscale phone battery?
- [ ] Merge PR #11 now or after 1.2/1.3 code ready?
