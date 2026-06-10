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

On older pip versions (e.g. pip 22.x on Ubuntu 22.04), the editable install
may fail with a `setup.py develop` permission error. Use the fallback:

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
    coupling.md               # change coupling + hidden seams (coupled, no import edge)
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
ownership/bus-factor, and code age. Coupled pairs with no import edge are flagged
as hidden seams in `reports/coupling.md`.

## Tickets

Every scan auto-proposes tickets (refactor, hidden seam, oversized file, stale
hub, knowledge silo) into `docs/tickets/` — one markdown file each, with YAML
frontmatter (Dataview-queryable) and acceptance criteria. Review them in
Obsidian: edit `status` (`proposed → approved → in-progress → done`/`rejected`)
or drag cards on the generated Kanban `board.md`. Rejected fingerprints are
never re-proposed. Humans add tickets the same way — any `.md` file with a
`status` in its frontmatter. Disable with `"tickets_enabled": false`; cap new
tickets per scan with `tickets_max_new_per_scan`.

Review from the terminal too:

```bash
repo-scan tickets                  # list, sorted by status then priority
repo-scan tickets approve tkt-0001
repo-scan tickets start | reject | done <id>
```

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
radar daemon                          # resident runner: scans, loops, gate resume
radar serve                           # mobile dashboard + daemon (port 8800)
```

### LLM backend

No API keys. `radar` shells out to an agent CLI on PATH — `cursor-agent` or
`claude` by default, configurable per repo:

```json
{ "llm_cli": ["cursor-agent -p --output-format text", "claude -p"] }
```

### Gates (progressive autonomy)

```json
{ "gates": { "post_analyze": "prompt", "post_audit": "prompt" } }
```

- `prompt` — CLI y/n; non-interactive runs pause to `docs/research/pending/`
  and resume with `radar loop "..." --approve post_analyze`
- `auto` — pass through silently (abstract the gate away once trusted)
- `deny` — hard stop

Every decision is appended to `docs/research/decisions.md`. Loop runs are
recorded to `docs/changelog/{date}-loop.md`; specs land in `docs/specs/`
(`status: draft` → `status: approved` after Gate 2).

### The hub — approve from your phone

`radar serve` runs a zero-dependency stdlib HTTP server (plus the daemon in a
background thread) and prints a tokenized URL. The dashboard is one
self-contained mobile-first page: live stats and runs, pending gates with
**Approve / Reject** buttons and the full analysis one tap away, the ticket
board, and the decision trail. Decisions land in a file-backed inbox
(`docs/.radar/decisions/`); the daemon resumes paused loops on its next poll.
Loops checkpoint per stage, so a resume skips completed LLM calls.

```bash
radar serve                # 0.0.0.0:8800, token printed on start
radar serve --port 9000 --no-daemon
```

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

Hub config keys (all optional): `serve_host`, `serve_port`,
`daemon_poll_seconds`, `daemon_scan_hours`, `ntfy_topic`, `ntfy_server`.

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
