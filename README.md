# repo-scan

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
    health.md                 # file sizes, complexity, git churn
    dependencies.md           # Mermaid dep graphs (TS + Python)
    calls.md                  # Mermaid call graphs (C)
  architecture/
    dependency-graph.md       # stable dep graph for Obsidian linking
  research/
    candidates.md             # high-churn x high-complexity files (radar_enabled)
  changelog/                  # build + loop progress entries
```

`index.md` opens with the repo identity (manifests, entry points, README summary),
a "start here" table ranking files by import centrality x churn x complexity, and a
depth-capped directory tree — one read orients a human or an agent.

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
| `cflow` | C call graphs | `brew install cflow` |

All optional — scan degrades gracefully without them.

---

## HANDOFF.md

`repo-scan --handoff` writes `docs/HANDOFF.md`: current repo state + full build spec for packaging this prototype. Hand it to an agent or developer to build the tool out. Delete once done.
