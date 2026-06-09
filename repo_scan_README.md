# repo-scan

Repo intelligence tool. Run it against any codebase — analyzes structure, generates dependency and call graphs as Mermaid diagrams, scores complexity, tracks git churn, writes everything to `docs/` committed to git and readable in Obsidian.

---

## Install (global)

```bash
git clone https://github.com/yourname/repo-scan
cd repo-scan
pip install -e .
```

Puts `repo-scan` on PATH. Run from any repo.

---

## Usage

```bash
repo-scan                     # scan cwd
repo-scan /path/to/project    # scan specific path
repo-scan --init              # write .repo-scan.json config
repo-scan --install-hook      # wire to git pre-commit
repo-scan --handoff           # generate docs/HANDOFF.md bootstrap doc
repo-scan --check-deps        # check optional tool availability
```

---

## Output

```
docs/
  index.md                    # dashboard: overview, links, action items
  reports/
    health.md                 # file sizes, complexity, git churn
    dependencies.md           # Mermaid dep graphs (TS + Python)
    calls.md                  # Mermaid call graphs (C)
  architecture/
    dependency-graph.md       # stable dep graph for Obsidian linking
  research/                   # populated by RADAR (separate tool)
```

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
  "radar_enabled": false
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
