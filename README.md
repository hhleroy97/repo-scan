# repo-scan

[![CI](https://github.com/hhleroy97/repo-scan/actions/workflows/ci.yml/badge.svg)](https://github.com/hhleroy97/repo-scan/actions/workflows/ci.yml)

Repo intelligence tool. Run it against any codebase — analyzes structure, generates dependency and call graphs as Mermaid diagrams, scores complexity, tracks git churn, writes everything to `docs/` committed to git and readable in Obsidian.

---

## Install (global)

```bash
git clone https://github.com/yourname/repo-scan
cd repo-scan
pip install -e .
```

Puts `repo-scan` on PATH. Run from any repo. Requires Python 3.10+.

Packaging metadata lives in `pyproject.toml` only (PEP 517 `setuptools.build_meta`);
there is no `setup.py`.

On older pip versions (e.g. pip 22.x on Ubuntu 22.04), the editable install may
need build isolation disabled:

```bash
pip install -e . --no-build-isolation
```

---

## Usage

```bash
repo-scan                     # scan cwd
repo-scan /path/to/project    # scan specific path
repo-scan --init              # write .repo-scan.json config
repo-scan --init-agents       # write AGENTS.md scaffold (agent rules)
repo-scan --install-hook      # wire to git pre-commit
repo-scan --handoff           # generate docs/HANDOFF.md bootstrap doc
repo-scan --digest            # single token-budgeted docs/digest.md for LLM context
repo-scan --check-deps        # check optional tool availability
repo-scan --version           # print version
```

---

## Output

```
docs/
  index.md                    # dashboard: identity, ranked files, structure, links
  scan.json                   # machine-readable sidecar for agents (same data)
  digest.md                   # token-budgeted single-file LLM context (--digest)
  reports/
    health.md                 # file sizes, complexity, churn, knowledge map (bus factor)
    dependencies.md           # Mermaid dep graphs (TS + Python), PageRank-tinted
    calls.md                  # Mermaid call graphs (C)
    coupling.md               # coupling network diagram + table; hidden seams flagged
    trend.md                  # scan-over-scan metric history (capped log)
  tickets/
    tkt-NNNN.md               # auto-proposed + human tickets (YAML frontmatter)
    board.md                  # Obsidian Kanban board, columns per status
  architecture/
    dependency-graph.md       # stable dep graph for Obsidian linking
  research/
    candidates.md             # high-churn x high-complexity files (radar_enabled)
  changelog/                  # build + loop progress entries
```

`index.md` opens with the repo identity (manifests, entry points, README summary),
a health verdict and a "since last scan" delta callout, then a "start here" table
ranking files by import-graph PageRank x churn x complexity x size — including a
Tests column flagging files with no matching test file — and a depth-capped
directory tree. One read orients a human or an agent. PageRank is computed inline
(no networkx); "imported by" stays the direct count.

Complexity covers every language: radon scores Python, lizard scores TS/TSX/JS/C/
Java/Go and friends on the same A–F rank scale. Untested candidates get a 2x
priority boost in the RADAR trigger feed.

Behavioral analysis (one `git log --numstat` pass) adds change coupling, per-file
ownership/bus-factor, and code age. `reports/coupling.md` renders the top coupled
pairs as a Mermaid network (dashed red edges = hidden seams with no import link;
gray = import-backed). Coupled pairs with no import edge are also listed in the
table below the diagram.

## Tickets

Every scan auto-proposes tickets (refactor, hidden seam, oversized file, stale
hub, knowledge silo) into `docs/tickets/` — one markdown file each, with YAML
frontmatter (Dataview-queryable) and acceptance criteria. Auto-tickets include a
`## Evidence` section with Mermaid diagrams (coupling ego graph, seam pair, or
size callout) frozen at creation time. `reports/coupling.md` opens with a
coupling network diagram (dashed red = hidden seam, gray = import-backed).
Disable ticket diagrams with `"ticket_diagrams_enabled": false`; cap coupling
edges with `diagram_max_coupling_edges` and refactor neighbors with
`diagram_max_ticket_neighbors`. Review tickets in Obsidian: edit `status`
(`proposed → approved → in-progress → done`/`rejected`) or drag cards on the
generated Kanban `board.md`. Rejected fingerprints are never re-proposed.
Humans add tickets the same way — any `.md` file with a `status` in its
frontmatter. Disable auto-tickets with `"tickets_enabled": false`; cap new
tickets per scan with `tickets_max_new_per_scan`.

Review from the terminal too:

```bash
repo-scan tickets                  # list, sorted by status then priority
repo-scan tickets approve tkt-0001
repo-scan tickets start | reject | done <id>
```

Approval requires at least one real acceptance criterion (not the placeholder
`define done` / `define acceptance criteria before approving`). The hub, CLI,
and `radar top` enforce this; tickets with placeholder criteria stay out of the
radar loop even if marked approved in frontmatter. Each ticket also projects a
PM-facing **card** on read (`outcome`, `why_line`, criteria summary) — override
with an optional `## Card` block (`Outcome:`, `Story:`, `Title:`) or
frontmatter `card_*` keys; the canonical `title` in markdown stays technical.

**Intent intake.** Your ideas enter the same pipeline as scan signals — as
`feature` tickets that the loop researches, specs, implements, and PRs like
any other work:

```bash
repo-scan tickets new "Add CSV export" --why "users asked" \
  --criterion "exports all rows" --criterion "handles utf-8" --approve
```

The dashboard's Tickets tab has the same composer ("New idea"), so intent can
be captured from your phone. Acceptance criteria matter: they ride into the
spec (which must map each criterion to a concrete automated test) and the act
stage refuses to commit `feature` work that ships without tests. Re-submitting
the same title dedups against the existing ticket instead of duplicating.

The loop closes itself: `radar full` works the highest-priority **approved**
ticket (falling back to raw metric candidates), moves it to `in-progress` with
a spec wikilink when the loop's gates pass, and when a later scan sees the
ticket's underlying metric has cleared, the board flags it
"metrics resolved, ready to close".

Plain Markdown + Mermaid. Point Obsidian at the repo root — everything renders natively.

---

## Per-repo config (.repo-scan.json)

```json
{
  "line_warn": 300,
  "line_crit": 600,
  "complexity_min_rank": "C",
  "churn_top_n": 20,
  "exclude_dirs": ["node_modules", ".git", "dist", "build"],
  "docs_dir": "docs",
  "radar_enabled": false,
  "tree_depth": 3,
  "rank_top_n": 15,
  "digest_tokens": 4000
}
```

Run `repo-scan --init` to write defaults. All fields optional.

---

## Optional tools

| Tool | Purpose | Install |
|------|---------|---------|
| `tokei` | Line counts | `brew install tokei` |
| `madge` | TS/JS dep graphs | `npm install -g madge` |
| `radon` | Python complexity | `pip install radon` |
| `lizard` | TS/JS/C/Java/Go complexity | `pip install lizard` |
| `cflow` | C call graphs | `brew install cflow` |

All optional — scan degrades gracefully without them.

---

## radar — the research loop

Installed alongside `repo-scan`. RADAR turns the `docs/` knowledge base into a
research-to-implementation loop: **R**esearch → **A**nalyze → Gate 1 →
**D**raft → **A**udit → Gate 2 → **R**ecord.

```bash
radar ingest github:owner/repo        # normalize one source into docs/research/sources/
radar ingest arxiv:2210.03629         #   also: url:https://...  file:./paper.pdf
radar research "how do X loops work?" # LLM proposes sources, radar ingests them
radar loop "should we adopt X?"       # full pipeline, pauses at gates for approval
radar full                            # metric-triggered: top churn x complexity file
radar act                             # implement an approved spec (tests = hard gate)
radar top                             # terminal dashboard: runs, gates, LLM usage
radar daemon                          # resident runner: scans, loops, acts, gate resume
radar serve                           # mobile dashboard + daemon (port 8800)
```

**Repo snapshot.** Research, analyze, and act stages inject a ranked
`repo_snapshot()` built from `scan.json` (hotspots, open tickets, trend deltas,
coupling alerts) — not whole files. Digest dedup on `scan.generated_at` + git
HEAD keeps parallel loops from re-sending identical context. Tune with
`repo_snapshot_max_chars` (default 2500).

### LLM backend, model routing, and the usage ledger

No API keys. `radar` shells out to an agent CLI on PATH — `cursor-agent` or
`claude` by default, configurable per repo:

```json
{ "llm_cli": ["cursor-agent -p --output-format json -f", "claude -p --output-format json"] }
```

Per-role model routing puts cheap models on the labor and the default
(frontier) model on the judgment — the spec is already approved by the time
an act-model touches code, and tests are the backstop:

```json
{ "llm_roles": { "act": "composer-2.5", "act_fix": "composer-2.5" } }
```

Roles: `research`, `analyze`, `draft`, `audit`, `act`, `act_fix`. Any role
without an override falls back to `llm_roles["default"]` if set, otherwise
the backend's own default. `{ "llm_roles": { "default": "composer-2.5" } }`
is the one-knob way to pin every operation to a cheap model when the API
budget runs dry.

Every LLM call is appended to `docs/<docs_dir>/.radar/usage.jsonl` with real
token counts (parsed from the agent CLI's JSON envelope; plain-text backends
get a chars/4 estimate flagged as such). Both dashboards aggregate it by
day, model, and role.

**Timeouts and liveness.** Agent CLIs are silent until they finish, which
looks identical to a hang. While a call runs, radar emits a heartbeat event
every `llm_heartbeat_seconds` (default 120) — `research · composer-2.5 still
working · 6m elapsed (pid alive, limit 25m)` — to the agent feed, dashboard,
and TUI, so you can tell working from stuck. Hard caps: `llm_timeout` for
research/analyze/draft/audit calls and `act_timeout` for implementation runs;
set them generously — a killed call loses that stage's work (checkpoints
resume from the last completed stage, not mid-call).

### The Act stage — from approved spec to reviewed commit

With `"act_enabled": true`, `radar act` takes the highest-priority in-progress
ticket whose spec was approved at Gate 2 and implements it: the agent CLI
edits the repo on an isolated `radar/<ticket-id>` branch, the test suite must
pass (failures are fed back for bounded fix rounds, `act_fix_rounds`, default
2), and two new gates bracket the work — `pre_implement` before anything
runs, `post_implement` showing the diff stat before the commit lands. You
review and merge the branch; the next scan's metric fingerprints confirm the
fix. The daemon picks up act candidates automatically, so a full
ticket-to-commit cycle can run from your phone.

Safety: refuses dirty trees, never touches your branch, excludes vault churn
from the implementation commit, and a failed run leaves the branch for human
review with a note on the ticket.

**Parallel agents.** Daemon-scheduled acts run in isolated git worktrees
(`~/.cache/repo-scan/worktrees/`), one per ticket branch, so up to
`max_parallel_acts` (default 2) implementations proceed concurrently without
ever touching your checkout — one cheap agent per ticket. `radar act
--worktree` does the same manually. Successful worktrees are pruned after
commit; failed ones are kept for inspection.

Research loops fan out the same way: the daemon starts up to
`max_parallel_loops` (default 2) loops on threads, one per approved ticket,
highest priority first. Loop state (checkpoints, gates, decisions) is keyed
by problem so concurrent loops never collide, and each finished loop links
its own spec onto its ticket by problem slug rather than "newest spec file".
Set `max_parallel_loops` to 1 to force the old one-at-a-time behavior.

```json
{
  "act_enabled": true,
  "test_cmd": "python3 -m pytest -q",
  "act_timeout": 1800,
  "act_fix_rounds": 2,
  "max_parallel_acts": 2
}
```

(`test_cmd` is auto-detected — pytest if `tests/` exists, `npm test` if
`package.json` — but pin it explicitly for anything real.)

### Gates (progressive autonomy)

```json
{ "gates": { "post_analyze": "prompt", "post_audit": "prompt",
             "pre_implement": "prompt", "post_implement": "prompt" } }
```

- `prompt` — CLI y/n; non-interactive runs pause to `docs/research/pending/`
  and resume with `--approve` on the same command (`radar loop "..." --approve
  post_analyze`, or `radar act --approve pre_implement`)
- `auto` — pass through silently (abstract the gate away once trusted)
- `deny` — hard stop

`radar loop` and `radar full` also accept `--gates prompt|auto|deny` to override
both loop gates (`post_analyze`, `post_audit`) for one run. `--approve GATE` is
repeatable; gate names are command-scoped — loop/full: `post_analyze`,
`post_audit`; act: `pre_implement`, `post_implement` (no `--gates` on act; use
config or `gates_by_kind`).

Every decision is appended to `docs/research/decisions.md`. Loop runs are
recorded to `docs/changelog/{date}-loop.md`; specs land in `docs/specs/`
(`status: draft` → `status: approved` after Gate 2).

### Governance — budgets, protected paths, per-kind autonomy

Autonomy is granted in policy, not all at once:

```json
{
  "budget_daily_tokens": 2000000,
  "max_acts_per_day": 6,
  "protected_paths": [".github/*", "repo_scan/config.py"],
  "gates_by_kind": { "refactor": { "pre_implement": "auto" } },
  "require_tests_for_kinds": ["feature"]
}
```

- **Budgets** — when the day's LLM tokens (from the usage ledger) or act-run
  count hit their cap, the daemon stops *starting* new work (one notification,
  one event); runs already mid-flight finish so spent tokens aren't wasted.
- **Protected paths** — if an implementation touches a matching file
  (fnmatch globs), the `post_implement` gate is forced to `prompt` even if
  you've set it to `auto`: sensitive areas always face a human.
- **Per-kind autonomy** (`gates_by_kind`) — trust is earned per work type.
  Keyed by the ticket's fingerprint prefix (`refactor:`, `feature:`,
  `seam:`...), merged over `gates` for that act run only — e.g. let refactors
  start unattended while features still ask first.
- **Acceptance tests** — for kinds in `require_tests_for_kinds` (default
  `["feature"]`), an implementation that changes no test files gets one
  dedicated round to add the spec's acceptance tests; still none and the run
  stops with `no-acceptance-tests`, branch kept for review.

### The hub — approve from your phone

`radar serve` runs a zero-dependency stdlib HTTP server (plus the daemon in a
background thread) and prints a tokenized URL. The dashboard is one
self-contained mobile-first page with five tabs: the **Now** tab shows open
tickets as PM glance rows (`card.outcome`, why line, criteria count) with a
link to the full **Tickets** tab — three-tier cards there (expand for
checklist, edit criteria when not ready, **View ticket** for full markdown);
approve and create actions stay on Tickets (and in `radar top` for terminal
use); live stats and runs; **Gates** for pending approvals with **Approve /
Reject** buttons and the full analysis one tap away; **Activity** for the
decision trail and LLM burn; and **Dashboard** for vault audit from
`scan.json` (coverage %, knowledge debt, E/L/C/F signal matrix, score
histogram, ranked untracked code), a vendored Mermaid agentic-loop diagram
with live run highlighting, and a pan/zoom provenance canvas (`GET /api/graph`;
tap a node for `/api/graph/chain`). The legacy `#graph` hash redirects to
`#dashboard`. Decisions land in a file-backed inbox
(`docs/.radar/decisions/`); the daemon resumes paused loops on its next poll.
Loops checkpoint per stage, so a resume skips completed LLM calls.

```bash
radar serve                # 0.0.0.0:8800, token printed on start
radar serve --port 9000 --no-daemon
radar top                  # same state in the terminal (curses, stdlib)
```

`radar top` is the terminal flavor of the dashboard: live runs, pending
gates (approve with `a`, reject with `r`), actionable tickets, the LLM token
ledger by model and role, and the recent decision trail — handy when you're
already in the shell and don't want to reach for a browser.

**PRs from the phone.** When `act_open_pr` is on, the dashboard's Now tab
lists every open PR with its CI verdict (checks passing / running /
**failing**, plus merge conflicts), read via the `gh` CLI and cached for a
minute. One tap to **Merge** (squash + delete branch, confirm dialog warns
if checks are failing) — the matching ticket is auto-noted and moved to
done.

**Fix & update** on failing/conflicting PRs does more than merge base into
the branch: it updates the branch, diagnoses the blocker (conflicting files
via a local merge probe, or the failed CI log via `gh run view --log-failed`),
shows that diagnosis inline on the card, and when `pr_auto_remediate` is on
(default) spawns a background `act_fix` agent on the PR branch — merge
conflicts, CI failures, then local tests, commit, and push. Diagnosis persists
at `docs/.radar/pr-diagnosis/<pr-number>.json` so it survives refresh.

Remote access, the low-friction way: install [Tailscale](https://tailscale.com)
on this machine and your phone, then open
`http://<machine-tailnet-name>:8800/?token=...` from anywhere. The token
(persisted at `docs/.radar/token`) gates every request; still, treat the
server as private-network-only — don't port-forward it to the internet.

Push notifications (optional): install the [ntfy](https://ntfy.sh) app,
subscribe to a long random topic, and set it in `.repo-scan.json`:

```json
{ "ntfy_topic": "repo-scan-hub-<something-long-and-random>" }
```

The daemon then pushes when a gate needs you, a loop finishes or fails, and
when a scan proposes tickets — tapping the notification opens the dashboard
(set `"serve_host"` to your tailnet name so the link resolves).

Hub config keys (all optional; defaults in `repo_scan/hub/settings.py`):
`serve_host`, `serve_port`, `daemon_poll_seconds`, `daemon_scan_hours`,
`ntfy_topic`, `ntfy_server`, `dashboard_url` (overrides notification links
when a proxy fronts the hub), `vault_autocommit`, `max_parallel_acts`,
`max_parallel_loops`.

Machine-private values (the ntfy topic is effectively a credential) belong in
`.repo-scan.local.json` — same format, merged after `.repo-scan.json`, and
should be gitignored.

### Obsidian graph + Dataview

All radar artifacts carry YAML frontmatter (type, tags, status, confidence —
queryable with Dataview/Bases) and wikilink their provenance: spec → analysis
→ sources + run log, and gate decisions link both. Each loop run renders as a
connected cluster in graph view — click a spec, see exactly what research
justified it. Source `linked_files` emit `[[path]]` ghost nodes so sources
cluster around the code they inform.

### What radar writes

```
docs/
  research/
    sources/{id}.md         # one file per source; your ## Notes are never overwritten
    index.md / tags.md      # rebuilt from sources on every ingest
    runs/                   # one auditable log per research session
    analysis/               # findings + recommendation per loop
    pending/                # paused gates (file-backed, resumable)
    decisions.md            # append-only gate decision trail
  specs/                    # drafted + audited implementation specs
  changelog/{date}-loop.md  # loop outcomes
  changelog/{date}-act.md   # act outcomes (branch, commit, tests, diff)
  .radar/                   # hub runtime state (gitignored): token, runs,
                            #   decision inbox, loop checkpoints
```

---

## Development

```bash
pip install -e ".[dev]"    # pytest>=8, syrupy>=5, radon, lizard
python3 -m pytest tests/   # offline: fake-LLM harness, no network calls
```

Writer output is pinned by syrupy golden files in `tests/__snapshots__/`.
If you intentionally change generated markdown/JSON, refresh them with
`pytest --snapshot-update` and review the diff like any other code change.

Build progress is tracked per phase in `docs/changelog/`.

---

## HANDOFF.md

`repo-scan --handoff` writes `docs/HANDOFF.md`: current repo state + full build spec for packaging this prototype. Hand it to an agent or developer to build the tool out. Delete once done.
