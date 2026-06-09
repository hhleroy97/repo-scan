# HANDOFF.md — repo-scan

> **For the agent or developer receiving this:** This document is fully self-contained.
> Read it top to bottom before touching anything. All files you need are listed in
> the file manifest below. The prototype is already working — your job is to package
> it cleanly, verify it installs globally, and confirm all flags work correctly.
> Delete this file once the build is verified.

---

## What this is

`repo-scan` is a global CLI tool that analyzes any git repository and writes a
structured `docs/` knowledge base to it — committed to git, readable in Obsidian,
and consumable by AI coding tools (Cursor, Claude Code) as in-repo context.

It is the foundation layer for the RADAR research loop (built separately). The
`docs/` structure it produces is the shared knowledge base that RADAR writes into.

### What one run produces

```
docs/
  index.md                      # dashboard: overview, action items, wikilinks
  reports/
    health.md                   # file sizes, complexity hotspots, git churn
    dependencies.md             # Mermaid dep graphs (TS + Python)
    calls.md                    # Mermaid call graphs (C via cflow)
  architecture/
    dependency-graph.md         # stable dep graph for Obsidian cross-linking
  research/                     # empty dirs, populated later by RADAR
```

All output is plain Markdown with Mermaid code blocks. Point Obsidian at the
repo root — everything renders natively with no plugins required.

---

## File manifest

These are the files that must exist in this repo. All are included alongside
this HANDOFF.md.

```
repo-scan/
  HANDOFF.md          ← this file (delete after build verified)
  repo_scan.py        ← working prototype, 939 lines, single file
  pyproject.toml      ← package metadata and entry point
  setup.py            ← fallback installer for older pip versions
  README.md           ← usage documentation
```

**Do not modify `repo_scan.py` during the packaging step.** It is the source
of truth for all business logic. Package it as-is, test it, then extend.

---

## Target architecture

### Global install

After setup, any developer should be able to:

```bash
git clone https://github.com/yourname/repo-scan
cd repo-scan
pip install -e .
```

And have `repo-scan` available on PATH from any directory.

### Entry point

`pyproject.toml` declares:
```
repo-scan = "repo_scan:main"
```

`repo_scan.py` exposes a `main()` function at module level. The install wires
`repo-scan` CLI to that function.

### Per-repo config

Each target repo may have a `.repo-scan.json` at its root. The tool reads it
on every run. If absent, all defaults apply. No config is required to run.

Default config (written by `repo-scan --init`):
```json
{
  "line_warn": 300,
  "line_crit": 600,
  "complexity_min_rank": "C",
  "churn_top_n": 20,
  "exclude_dirs": [
    "node_modules", ".git", "__pycache__", ".venv", "venv",
    "dist", "build", ".next", "target", ".mypy_cache",
    ".pytest_cache", "coverage", ".turbo", "out"
  ],
  "docs_dir": "docs",
  "radar_enabled": false
}
```

---

## CLI surface

All flags that must work after install:

```bash
repo-scan                       # scan cwd, write docs/
repo-scan /path/to/repo         # scan specific path
repo-scan --init                # write .repo-scan.json with defaults to cwd
repo-scan --install-hook        # install git pre-commit hook
repo-scan --check-deps          # print availability of optional tools
repo-scan --handoff             # generate docs/HANDOFF.md bootstrap doc
repo-scan --quiet               # minimal output (used by git hook internally)
```

---

## Build steps

Work through these in order. Each is independently verifiable.

### Step 1 — Verify the prototype runs as a script

```bash
python repo_scan.py --check-deps
```

Expected output: a dependency check table showing which of tokei, madge,
radon, cflow are available and which are missing.

```bash
mkdir /tmp/test-repo && cd /tmp/test-repo
git init && git config user.email "t@t.com" && git config user.name "T"
echo "def hello(): pass" > main.py
git add . && git commit -m "init"
python /path/to/repo_scan.py .
```

Expected: `docs/` created with `index.md`, `reports/health.md`,
`reports/dependencies.md`, `reports/calls.md`,
`architecture/dependency-graph.md`. No errors.

### Step 2 — Install as global package

```bash
cd /path/to/repo-scan
pip install -e .
```

Verify:
```bash
which repo-scan           # should return a path
repo-scan --version       # note: not yet implemented, should fail gracefully
repo-scan --check-deps    # should work identically to script mode
```

If `pip install -e .` fails with a `pyproject.toml` error, fall back to:
```bash
pip install -e . --no-build-isolation
```

The `setup.py` is present as a fallback if `pyproject.toml` causes issues
on older pip versions.

### Step 3 — Test all flags against a real repo

Use the test repo from Step 1 or any local repo:

```bash
repo-scan /tmp/test-repo                    # full scan
repo-scan /tmp/test-repo --init             # writes .repo-scan.json
repo-scan /tmp/test-repo --install-hook     # installs pre-commit hook
repo-scan /tmp/test-repo --handoff          # writes docs/HANDOFF.md
repo-scan /tmp/test-repo --check-deps       # dep check
repo-scan /tmp/test-repo --quiet            # minimal output
```

Verify each writes the expected files and exits 0.

### Step 4 — Verify pre-commit hook

```bash
cd /tmp/test-repo
repo-scan . --install-hook
cat .git/hooks/pre-commit     # should contain repo-scan block
echo "x = 1" >> main.py
git add main.py
git commit -m "test hook"     # scan should run, docs/ should be staged and included
git show --stat HEAD          # docs/reports/health.md should appear in the commit
```

The hook must:
- Run without blocking the commit
- Stage and include updated `docs/` files automatically
- Work whether `repo-scan` is on PATH (global install) or only `scripts/repo_scan.py` exists

### Step 5 — Verify Obsidian rendering

Open the target repo root (or `docs/`) as an Obsidian vault:
1. `docs/index.md` — opens cleanly, `[[wikilinks]]` resolve to report files
2. `docs/reports/dependencies.md` — Mermaid blocks render (requires a repo with TS or Python imports)
3. Graph view — shows connections between `index.md` and report files

No Obsidian plugins are required. If Mermaid doesn't render, check that
Obsidian's reading view is active (not source mode).

---

## Known issues and constraints

**Subprocess timeout:** All `subprocess.run` calls use `timeout=30`. This
prevents hangs on large repos or when git commands stall. If a command times
out, the relevant section of the report will note it was skipped.

**Python dependency graph fallback:** The Python dep graph uses a static
import parser (no external deps). It only detects intra-repo imports — stdlib
and third-party imports are ignored. This is intentional. For full dep graphs,
`pydeps` can be integrated as an optional enhancement.

**madge and circular deps:** `madge --mermaid` on a large TS project can
produce very large graphs. A future version should add `--max-depth` limiting.
For now the output is written as-is.

**C call graphs:** `cflow` is capped at 30 source files and depth 3 to
prevent runaway output on large C codebases.

**install-hook idempotency:** Running `--install-hook` multiple times is safe.
The hook checks for the `# --- repo-scan` marker before appending. It appends
to existing hooks rather than replacing them.

---

## Optional tools

All external tools are optional. The scan notes what was skipped.

| Tool | Purpose | Install |
|------|---------|---------|
| `tokei` | Fast line counts (all languages) | `brew install tokei` or `cargo install tokei` |
| `madge` | TS/JS dependency graphs | `npm install -g madge` |
| `radon` | Python complexity scores (CC) | `pip install radon` |
| `cflow` | C/C++ call graphs | `brew install cflow` or `apt install cflow` |
| `git` | Churn analysis | Pre-installed (required) |

---

## Extension points

The prototype is deliberately monolithic. Once packaging is stable, the
natural split is:

```
repo_scan/
  __init__.py
  cli.py           # argparse, main()
  config.py        # load_config(), DEFAULT_CONFIG
  scanner.py       # scan() orchestration
  languages.py     # detect_languages(), get_line_counts()
  graphs.py        # dep + call graph generators
  complexity.py    # radon wrapper
  churn.py         # git log analysis
  writers.py       # write_health_report(), write_dep_report(), etc.
  handoff.py       # write_handoff()
  hooks.py         # install_hook()
  utils.py         # run(), color helpers, git_branch(), etc.
```

Do not refactor into this structure until the monolith is fully tested and
all flags are verified. Refactor as a second pass.

---

## RADAR readiness

`repo-scan` is the foundation. The RADAR research loop (`radar.py`, built
separately) layers on top and uses the same `docs/` structure.

When `radar_enabled: true` in `.repo-scan.json`, the scan will additionally:
- Flag files that are high-complexity AND high-churn as RADAR candidates
- Write candidate file paths to `docs/research/candidates.md`
- Surface these as priority targets for external research ingestion

The `docs/research/` directory is created on every scan (empty) so RADAR has
a stable location to write into when it runs.

---

## Acceptance criteria

The build is complete when:

- [ ] `pip install -e .` succeeds from the repo root
- [ ] `repo-scan` is available on PATH after install
- [ ] `repo-scan --check-deps` runs and exits 0
- [ ] `repo-scan /some/repo` produces all 5 expected docs files
- [ ] `repo-scan --init` writes `.repo-scan.json` without error
- [ ] `repo-scan --install-hook` installs hook, hook runs on next commit
- [ ] `repo-scan --handoff` writes `docs/HANDOFF.md`
- [ ] `repo-scan --quiet` produces minimal terminal output
- [ ] All docs files render correctly in Obsidian (Mermaid + wikilinks)
- [ ] Running `--install-hook` twice does not duplicate the hook
- [ ] No flag hangs or produces an unhandled exception

Once all criteria pass, delete this file.
