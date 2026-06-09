#!/usr/bin/env python3
"""
repo-scan — repo intelligence tool

Global usage (after install):
    repo-scan                        # scan cwd
    repo-scan /path/to/repo          # scan specific repo
    repo-scan --init                 # write .repo-scan.json config to cwd
    repo-scan --install-hook         # install git pre-commit hook
    repo-scan --check-deps           # check required tools
    repo-scan --handoff              # generate HANDOFF.md bootstrap doc

Per-repo config: .repo-scan.json at repo root (optional, all fields have defaults)
"""

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


# ---------------------------------------------------------------------------
# Defaults (overridden by .repo-scan.json)
# ---------------------------------------------------------------------------

DEFAULT_CONFIG = {
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
    "radar_enabled": False,
}

TS_EXTENSIONS = {".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs"}
PY_EXTENSIONS = {".py"}
C_EXTENSIONS  = {".c", ".h", ".cpp", ".cc", ".cxx", ".hpp"}


# ---------------------------------------------------------------------------
# Config loader
# ---------------------------------------------------------------------------

def load_config(root: Path) -> dict:
    cfg = DEFAULT_CONFIG.copy()
    config_file = root / ".repo-scan.json"
    if config_file.exists():
        try:
            overrides = json.loads(config_file.read_text())
            cfg.update(overrides)
        except json.JSONDecodeError as e:
            warn(f".repo-scan.json parse error: {e} — using defaults")
    return cfg


def write_default_config(root: Path):
    config_file = root / ".repo-scan.json"
    if config_file.exists():
        print(f"  .repo-scan.json already exists, skipping")
        return
    config_file.write_text(json.dumps(DEFAULT_CONFIG, indent=2) + "\n")
    print(f"  wrote .repo-scan.json — edit thresholds and excluded dirs as needed")


# ---------------------------------------------------------------------------
# Terminal output helpers (no external deps)
# ---------------------------------------------------------------------------

RESET  = "\033[0m"
BOLD   = "\033[1m"
DIM    = "\033[2m"
GREEN  = "\033[32m"
YELLOW = "\033[33m"
RED    = "\033[31m"
CYAN   = "\033[36m"
WHITE  = "\033[37m"

def _supports_color() -> bool:
    return hasattr(sys.stdout, "isatty") and sys.stdout.isatty()

def fmt(text: str, *codes: str) -> str:
    if not _supports_color():
        return text
    return "".join(codes) + text + RESET

def info(msg: str):  print(fmt(f"  {msg}", DIM))
def ok(msg: str):    print(fmt(f"  ✓ {msg}", GREEN))
def warn(msg: str):  print(fmt(f"  ⚠ {msg}", YELLOW))
def err(msg: str):   print(fmt(f"  ✗ {msg}", RED))
def step(msg: str):  print(fmt(f"\n{msg}", BOLD))
def header(msg: str):
    bar = "─" * len(msg)
    print(fmt(f"\n{bar}\n{msg}\n{bar}", BOLD + CYAN))


# ---------------------------------------------------------------------------
# Utilities
# ---------------------------------------------------------------------------

def run(cmd: list[str], cwd: Path = None, timeout: int = 30) -> tuple[str, str, int]:
    try:
        result = subprocess.run(
            cmd, cwd=str(cwd) if cwd else None,
            capture_output=True, text=True, timeout=timeout,
        )
        return result.stdout or "", result.stderr or "", result.returncode
    except subprocess.TimeoutExpired:
        return "", "timeout", 1
    except Exception as e:
        return "", str(e), 1


def tool_available(name: str) -> bool:
    return subprocess.run(["which", name], capture_output=True).returncode == 0


def ensure_dirs(root: Path, cfg: dict):
    docs = root / cfg["docs_dir"]
    for d in ["reports", "architecture", "research"]:
        (docs / d).mkdir(parents=True, exist_ok=True)


def write_doc(path: Path, content: str, root: Path):
    path.write_text(content, encoding="utf-8")
    try:
        rel = path.relative_to(root)
    except ValueError:
        rel = path
    ok(str(rel))


def now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")


def now_date() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def git_root(path: Path) -> Path | None:
    out, _, code = run(["git", "rev-parse", "--show-toplevel"], cwd=path)
    return Path(out.strip()) if code == 0 else None


def git_remote_url(root: Path) -> str:
    out, _, code = run(["git", "remote", "get-url", "origin"], cwd=root)
    return out.strip() if code == 0 else "unknown"


def git_branch(root: Path) -> str:
    out, _, code = run(["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd=root)
    return out.strip() if code == 0 else "unknown"


def git_last_commit(root: Path) -> str:
    out, _, code = run(["git", "log", "-1", "--pretty=%h %s"], cwd=root)
    return out.strip() if code == 0 else "unknown"


# ---------------------------------------------------------------------------
# Language detection
# ---------------------------------------------------------------------------

def detect_languages(root: Path, cfg: dict) -> dict[str, list[Path]]:
    skip = set(cfg["exclude_dirs"])
    buckets: dict[str, list[Path]] = {"ts": [], "py": [], "c": []}
    for f in root.rglob("*"):
        if not f.is_file():
            continue
        if any(p in skip for p in f.parts):
            continue
        ext = f.suffix.lower()
        if ext in TS_EXTENSIONS:
            buckets["ts"].append(f)
        elif ext in PY_EXTENSIONS:
            buckets["py"].append(f)
        elif ext in C_EXTENSIONS:
            buckets["c"].append(f)
    return buckets


# ---------------------------------------------------------------------------
# Line counts
# ---------------------------------------------------------------------------

def get_line_counts(root: Path, cfg: dict) -> dict[str, dict]:
    counts = {}
    skip = set(cfg["exclude_dirs"])

    if tool_available("tokei"):
        out, _, code = run(["tokei", "--output", "json"], cwd=root)
        if code == 0:
            try:
                data = json.loads(out)
                for lang_data in data.values():
                    for report in lang_data.get("reports", []):
                        path = Path(report["name"])
                        try:
                            rel = path.relative_to(root)
                        except ValueError:
                            rel = path
                        if any(p in skip for p in rel.parts):
                            continue
                        counts[str(rel)] = {
                            "lines": report["stats"]["code"],
                            "bytes": path.stat().st_size if path.exists() else 0,
                        }
                return counts
            except (json.JSONDecodeError, KeyError):
                pass

    all_exts = TS_EXTENSIONS | PY_EXTENSIONS | C_EXTENSIONS
    for f in root.rglob("*"):
        if not f.is_file():
            continue
        if any(p in skip for p in f.parts):
            continue
        if f.suffix.lower() not in all_exts:
            continue
        try:
            n = len(f.read_text(encoding="utf-8", errors="ignore").splitlines())
            counts[str(f.relative_to(root))] = {"lines": n, "bytes": f.stat().st_size}
        except OSError:
            pass

    return counts


# ---------------------------------------------------------------------------
# Git churn
# ---------------------------------------------------------------------------

def get_git_churn(root: Path, cfg: dict) -> list[dict]:
    out, _, code = run(["git", "log", "--name-only", "--pretty=format:", "--no-merges"], cwd=root)
    if code != 0:
        return []
    churn: dict[str, int] = {}
    for line in out.splitlines():
        line = line.strip()
        if line:
            churn[line] = churn.get(line, 0) + 1
    sorted_churn = sorted(churn.items(), key=lambda x: x[1], reverse=True)
    return [{"file": f, "commits": c} for f, c in sorted_churn[:cfg["churn_top_n"]]]


# ---------------------------------------------------------------------------
# Complexity
# ---------------------------------------------------------------------------

def get_python_complexity(root: Path, py_files: list[Path], cfg: dict) -> list[dict]:
    if not tool_available("radon") or not py_files:
        return []
    out, _, code = run(["radon", "cc", "--json", "--min", cfg["complexity_min_rank"], str(root)], cwd=root)
    if code != 0 or not out.strip():
        return []
    results = []
    try:
        data = json.loads(out)
        for filepath, functions in data.items():
            try:
                rel = str(Path(filepath).relative_to(root))
            except ValueError:
                rel = filepath
            for fn in functions:
                results.append({
                    "file": rel,
                    "name": fn.get("name", "?"),
                    "rank": fn.get("rank", "?"),
                    "complexity": fn.get("complexity", 0),
                    "lineno": fn.get("lineno", 0),
                })
    except (json.JSONDecodeError, KeyError):
        pass
    return sorted(results, key=lambda x: x["complexity"], reverse=True)


# ---------------------------------------------------------------------------
# Dependency graphs
# ---------------------------------------------------------------------------

def get_ts_dep_graph_mermaid(root: Path) -> str | None:
    if not tool_available("madge"):
        return None
    src_candidates = ["src", "app", "lib", "."]
    src_dir = next((root / d for d in src_candidates if (root / d).is_dir()), root)
    out, _, code = run(["madge", "--mermaid", str(src_dir)], cwd=root)
    return out.strip() if code == 0 and out.strip() else None


def get_python_dep_graph_mermaid(root: Path, py_files: list[Path], cfg: dict) -> str | None:
    if not py_files:
        return None
    skip = set(cfg["exclude_dirs"])
    repo_modules: set[str] = set()
    for f in py_files:
        try:
            rel = f.relative_to(root)
            parts = list(rel.parts)
            if parts[-1] == "__init__.py":
                parts = parts[:-1]
            else:
                parts[-1] = parts[-1][:-3]
            repo_modules.add(".".join(parts))
        except ValueError:
            pass

    edges: list[tuple[str, str]] = []
    for f in py_files:
        if any(p in skip for p in f.parts):
            continue
        try:
            src = f.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        try:
            rel = f.relative_to(root)
            parts = list(rel.parts)
            if parts[-1] != "__init__.py":
                parts[-1] = parts[-1][:-3]
            src_mod = ".".join(parts)
        except ValueError:
            continue
        for line in src.splitlines():
            line = line.strip()
            imported = None
            if line.startswith("from ") and " import " in line:
                imported = line.split()[1].lstrip(".")
            elif line.startswith("import "):
                imported = line.split()[1].split(".")[0]
            if imported:
                for mod in repo_modules:
                    if mod == imported or mod.startswith(imported + "."):
                        edges.append((src_mod, mod))
                        break

    if not edges:
        return None

    seen = set()
    lines = ["graph TD"]
    for s, t in edges:
        if (s, t) not in seen:
            seen.add((s, t))
            sl = s.replace(".", "_")
            tl = t.replace(".", "_")
            lines.append(f'  {sl}["{s.split(".")[-1]}"] --> {tl}["{t.split(".")[-1]}"]')
    return "\n".join(lines) if len(lines) > 1 else None


def get_c_call_graph_mermaid(root: Path, c_files: list[Path]) -> str | None:
    if not tool_available("cflow") or not c_files:
        return None
    c_paths = [str(f) for f in c_files[:30]]
    out, _, code = run(["cflow", "--depth=3"] + c_paths, cwd=root)
    if code != 0 or not out.strip():
        return None
    lines = ["graph TD"]
    stack: list[str] = []
    seen: set[tuple[str, str]] = set()
    for line in out.splitlines():
        stripped = line.lstrip()
        if not stripped:
            continue
        depth = (len(line) - len(stripped)) // 4
        name = stripped.split("(")[0].strip().replace(" ", "_")
        if not name:
            continue
        stack = stack[:depth]
        if stack:
            edge = (stack[-1], name)
            if edge not in seen:
                seen.add(edge)
                lines.append(f'  {stack[-1]} --> {name}')
        stack.append(name)
    return "\n".join(lines) if len(lines) > 1 else None


# ---------------------------------------------------------------------------
# Report writers
# ---------------------------------------------------------------------------

def write_health_report(root: Path, cfg: dict, line_counts: dict, churn: list, complexity: list):
    ts = now_iso()
    warn_n = cfg["line_warn"]
    crit_n = cfg["line_crit"]
    docs = root / cfg["docs_dir"]

    lines = [
        "# Health report",
        f"_Generated {ts}_  |  _Branch: {git_branch(root)}_  |  _Last commit: {git_last_commit(root)}_",
        "",
        "## File sizes",
        "",
        "| File | Lines | Size | Status |",
        "|------|-------|------|--------|",
    ]
    for rel, stats in sorted(line_counts.items(), key=lambda x: x[1]["lines"], reverse=True)[:40]:
        n = stats["lines"]
        kb = stats["bytes"] / 1024
        status = "🔴 critical" if n >= crit_n else ("🟡 large" if n >= warn_n else "✅")
        lines.append(f"| `{rel}` | {n} | {kb:.1f} KB | {status} |")
    lines.append("")

    if complexity:
        lines += [
            "## Complexity hotspots",
            "",
            "| File | Function | Rank | Score | Line |",
            "|------|----------|------|-------|------|",
        ]
        for item in complexity[:20]:
            lines.append(f"| `{item['file']}` | `{item['name']}` | {item['rank']} | {item['complexity']} | {item['lineno']} |")
        lines.append("")
    else:
        lines += ["## Complexity", "", "_radon not available or no Python files_", ""]

    if churn:
        lines += [
            "## Git churn (most changed files)",
            "",
            "| File | Commits |",
            "|------|---------|",
        ]
        for item in churn[:15]:
            lines.append(f"| `{item['file']}` | {item['commits']} |")
        lines.append("")

    alerts = [f for f, s in line_counts.items() if s["lines"] >= crit_n]
    if alerts:
        lines += ["## Action items", ""]
        for a in alerts:
            lines.append(f"- [ ] Split `{a}` ({line_counts[a]['lines']} lines)")
        lines.append("")

    write_doc(docs / "reports" / "health.md", "\n".join(lines), root)


def write_dep_report(root: Path, cfg: dict, ts_mermaid: str | None, py_mermaid: str | None):
    ts = now_iso()
    docs = root / cfg["docs_dir"]

    lines = ["# Dependency graph", f"_Generated {ts}_", ""]

    if ts_mermaid:
        lines += ["## TypeScript / JavaScript", "", "```mermaid", ts_mermaid, "```", ""]
    else:
        lines += ["## TypeScript / JavaScript", "", "_madge not installed — run `npm install -g madge`_", ""]

    if py_mermaid:
        lines += ["## Python", "", "```mermaid", py_mermaid, "```", ""]
    else:
        lines += ["## Python", "", "_No intra-repo Python imports detected_", ""]

    content = "\n".join(lines)
    write_doc(docs / "reports" / "dependencies.md", content, root)
    write_doc(docs / "architecture" / "dependency-graph.md", content, root)


def write_call_report(root: Path, cfg: dict, c_mermaid: str | None):
    ts = now_iso()
    docs = root / cfg["docs_dir"]

    lines = ["# Call graph", f"_Generated {ts}_", ""]

    if c_mermaid:
        lines += ["## C / C++", "", "```mermaid", c_mermaid, "```", ""]
    else:
        lines += ["## C / C++", "", "_cflow not available or no C files found_", ""]

    lines += [
        "## TypeScript",
        "",
        "_TS call graph via ts-morph — coming in next version_",
        "",
        "## Python",
        "",
        "_Python call graph via AST walker — coming in next version_",
        "",
    ]

    write_doc(docs / "reports" / "calls.md", "\n".join(lines), root)


def write_index(root: Path, cfg: dict, line_counts: dict, languages: dict):
    ts = now_iso()
    docs = root / cfg["docs_dir"]
    warn_n = cfg["line_warn"]
    crit_n = cfg["line_crit"]

    total_files = sum(len(v) for v in languages.values())
    total_lines = sum(s["lines"] for s in line_counts.values())
    lang_summary = ", ".join(f"{k.upper()}: {len(v)}" for k, v in languages.items() if v)
    large = [f for f, s in line_counts.items() if s["lines"] >= warn_n]
    critical = [f for f, s in line_counts.items() if s["lines"] >= crit_n]

    lines = [
        "# Repo index",
        f"_Last scan: {ts}_",
        "",
        "## Overview",
        "",
        "| Metric | Value |",
        "|--------|-------|",
        f"| Source files | {total_files} |",
        f"| Total lines | {total_lines:,} |",
        f"| Languages | {lang_summary} |",
        f"| Large files (>{warn_n} lines) | {len(large)} |",
        f"| Critical files (>{crit_n} lines) | {len(critical)} |",
        f"| Branch | {git_branch(root)} |",
        f"| Last commit | {git_last_commit(root)} |",
        "",
        "## Reports",
        "",
        "- [[reports/health]] — file sizes, complexity, git churn",
        "- [[reports/dependencies]] — dependency graphs (Mermaid)",
        "- [[reports/calls]] — call graphs (Mermaid)",
        "",
        "## Architecture",
        "",
        "- [[architecture/dependency-graph]] — stable dep graph for cross-linking",
        "- [[architecture/overview]] — hand-written system overview _(create this)_",
        "",
        "## Research",
        "",
        "- [[research/index]] — ingested sources _(populated by RADAR)_",
        "- [[research/theory]] — distilled understanding _(yours to write)_",
        "",
    ]

    if critical:
        lines += ["## Action items", ""]
        for f in critical:
            lines.append(f"- [ ] Split `{f}` ({line_counts[f]['lines']} lines)")
        lines.append("")

    write_doc(docs / "index.md", "\n".join(lines), root)


# ---------------------------------------------------------------------------
# HANDOFF.md — one-time bootstrap doc for building this tool
# ---------------------------------------------------------------------------

def write_handoff(root: Path, cfg: dict, languages: dict, line_counts: dict):
    ts = now_iso()
    docs = root / cfg["docs_dir"]

    total_files = sum(len(v) for v in languages.values())
    total_lines = sum(s["lines"] for s in line_counts.values())
    lang_list = ", ".join(f"{k.upper()} ({len(v)} files)" for k, v in languages.items() if v)

    # Top 10 largest files for context
    top_files = sorted(line_counts.items(), key=lambda x: x[1]["lines"], reverse=True)[:10]
    top_files_md = "\n".join(f"- `{f}` — {s['lines']} lines" for f, s in top_files)

    content = f"""# HANDOFF.md — repo-scan bootstrap

> **Note for agent/developer:** This document was auto-generated by `repo-scan` on {ts}.
> It is a one-time bootstrap artifact. Once the tool is built and functional,
> archive or delete this file. It is not a recurring output.

---

## Purpose

This document provides everything needed to build `repo-scan` as a
production-ready global CLI tool for this repository. The initial prototype
script (`scripts/repo_scan.py`) and per-repo config (`.repo-scan.json`) already
exist. This handoff defines the target architecture, UX, and build steps.

---

## Repo context

| Property | Value |
|----------|-------|
| Scanned at | {ts} |
| Remote | {git_remote_url(root)} |
| Branch | {git_branch(root)} |
| Last commit | {git_last_commit(root)} |
| Source files | {total_files} |
| Total lines | {total_lines:,} |
| Languages detected | {lang_list} |

### Largest files at time of scan

{top_files_md}

---

## Target architecture

### Global install

The tool should be installable globally via:

```bash
pip install -e /path/to/repo-scan
# or eventually:
pip install repo-scan
```

This exposes a `repo-scan` command on PATH. Internally it is a standard
Python package with a `pyproject.toml` entry point.

### Directory structure

```
repo-scan/               # the tool's own repo (separate from target repos)
  repo_scan/
    __init__.py
    cli.py               # argparse entry point
    scanner.py           # orchestrates the scan pipeline
    languages.py         # file detection, line counting
    graphs.py            # dep + call graph generation
    complexity.py        # radon, es-complexity wrappers
    churn.py             # git log analysis
    writers.py           # markdown report writers
    handoff.py           # HANDOFF.md generator
    config.py            # .repo-scan.json loader + defaults
    hooks.py             # git hook installer
    utils.py             # shared helpers
  scripts/
    repo_scan.py         # current monolithic prototype (source of truth for logic)
  pyproject.toml
  README.md
```

### Per-repo config

Each target repo may have a `.repo-scan.json` at its root:

```json
{json.dumps(DEFAULT_CONFIG, indent=2)}
```

The tool reads this on every run. If absent, all defaults apply.

### Git hook behavior

Running `repo-scan --install-hook` writes `.git/hooks/pre-commit`.
The hook:
1. Runs `repo-scan` against the repo root
2. Stages changed files under `docs/` automatically
3. Never blocks a commit — warnings only
4. Prints a brief summary of what changed

---

## docs/ output structure

All output is plain Markdown with Mermaid code blocks.
Point Obsidian at the repo root or `docs/` folder — everything renders natively.

```
docs/
  index.md                     # dashboard: overview, links, action items
  reports/
    health.md                  # file sizes, complexity, churn alerts
    dependencies.md            # Mermaid dep graphs (TS + Python)
    calls.md                   # Mermaid call graphs (C via cflow)
  architecture/
    dependency-graph.md        # stable dep graph for Obsidian cross-linking
    overview.md                # hand-written (not generated)
    decisions/                 # ADRs (written by RADAR loop, not repo-scan)
  research/                    # populated by RADAR loop (not repo-scan)
    index.md
    sources/
```

---

## Build steps

Work through these in order. Each step is independently testable.

### Step 1 — Package scaffold

- [ ] Create `pyproject.toml` with entry point `repo-scan = repo_scan.cli:main`
- [ ] Split `scripts/repo_scan.py` into the module structure above
- [ ] Verify `pip install -e .` exposes `repo-scan` on PATH
- [ ] `repo-scan --check-deps` works from any directory

### Step 2 — Config system

- [ ] `config.py` loads `.repo-scan.json` from cwd or passed path
- [ ] Falls back to `DEFAULT_CONFIG` for any missing keys
- [ ] `repo-scan --init` writes default config to cwd
- [ ] Validate config keys and types on load, warn on unknown keys

### Step 3 — Scanner pipeline

- [ ] Each analysis module (`languages`, `graphs`, `complexity`, `churn`)
      is independently importable and testable
- [ ] Each module accepts `(root: Path, cfg: dict)` and returns structured data
- [ ] `scanner.py` orchestrates them in order, collecting results
- [ ] Progress output uses the color helpers in `utils.py`

### Step 4 — Report writers

- [ ] Each writer accepts `(root, cfg, data)` and writes to `docs/`
- [ ] All Mermaid blocks validated (no empty graphs written)
- [ ] `docs/index.md` Obsidian wikilinks use `[[filename]]` format
- [ ] Timestamps in reports use UTC ISO format

### Step 5 — Git hook

- [ ] `hooks.py` installs/uninstalls pre-commit hook cleanly
- [ ] Appends to existing hook if one exists (doesn't overwrite)
- [ ] Hook script is self-contained shell — no Python path assumptions
- [ ] `repo-scan --install-hook` idempotent (safe to run multiple times)

### Step 6 — HANDOFF.md generation

- [ ] `handoff.py` generates this document programmatically
- [ ] Reads actual repo state (languages, line counts, git metadata)
- [ ] Writes to `docs/HANDOFF.md`
- [ ] Includes note that it is a one-time artifact

### Step 7 — RADAR readiness

- [ ] `docs/research/` directory created on first scan
- [ ] `docs/index.md` includes `[[research/index]]` link
- [ ] Config has `radar_enabled` flag (default false)
- [ ] When enabled, scan output notes which files are RADAR candidates
      (high complexity + high churn = most valuable to research)

---

## Tool dependencies

| Tool | Purpose | Install | Required? |
|------|---------|---------|-----------|
| tokei | Line counts | `brew install tokei` | No (fallback built in) |
| madge | TS dep graphs | `npm install -g madge` | No |
| radon | Python complexity | `pip install radon` | No |
| cflow | C call graphs | `brew install cflow` | No |
| git | Churn analysis | pre-installed | Yes |

All external tools are optional. The scan degrades gracefully and notes
what was skipped in the reports.

---

## Key design constraints

1. **Zero required deps beyond Python stdlib + git.** Everything else enhances.
2. **Output is always valid Markdown.** No tool should write broken Mermaid.
3. **Never block a commit.** The pre-commit hook is advisory only.
4. **Config is additive.** Unknown keys in `.repo-scan.json` are warned, not errors.
5. **Obsidian-first.** All cross-links use `[[wikilink]]` format.
6. **RADAR-ready.** The `docs/` structure is the shared knowledge base
   that RADAR (`radar.py`, built separately) reads from and writes into.

---

## Reference: current prototype

The working prototype is at `scripts/repo_scan.py`. It is a single-file
monolith with all logic intact. Use it as the source of truth for business
logic when splitting into the module structure above. Do not modify the
prototype — build the package alongside it, then replace once stable.
"""

    write_doc(docs / "HANDOFF.md", content, root)
    print(fmt("  → archive or delete HANDOFF.md once the tool is built", DIM))


# ---------------------------------------------------------------------------
# Dep check
# ---------------------------------------------------------------------------

def check_deps():
    tools = {
        "tokei":  "brew install tokei  OR  cargo install tokei",
        "madge":  "npm install -g madge",
        "radon":  "pip install radon",
        "cflow":  "brew install cflow  OR  apt install cflow",
        "git":    "(should already be installed)",
    }
    header("Dependency check")
    for tool, install in tools.items():
        if tool_available(tool):
            ok(f"{tool:<10} available")
        else:
            warn(f"{tool:<10} missing — {install}")
    print()


# ---------------------------------------------------------------------------
# Git hook installer
# ---------------------------------------------------------------------------

HOOK_SCRIPT = """\

# --- repo-scan pre-commit hook ---
REPO_ROOT="$(git rev-parse --show-toplevel)"
if command -v repo-scan &>/dev/null; then
    echo "repo-scan: scanning..."
    repo-scan "$REPO_ROOT" --quiet
    git add "$REPO_ROOT/docs/" 2>/dev/null
    echo "repo-scan: docs/ updated"
elif [ -f "$REPO_ROOT/scripts/repo_scan.py" ]; then
    echo "repo-scan: scanning (script mode)..."
    python "$REPO_ROOT/scripts/repo_scan.py" "$REPO_ROOT"
    git add "$REPO_ROOT/docs/" 2>/dev/null
fi
# --- end repo-scan ---
"""

def install_hook(root: Path):
    git_dir = root / ".git"
    if not git_dir.exists():
        err("Not a git repository")
        sys.exit(1)

    hook_path = git_dir / "hooks" / "pre-commit"

    if hook_path.exists():
        if "repo-scan" in hook_path.read_text():
            warn("Hook already installed — skipping")
            return
        with hook_path.open("a") as f:
            f.write(HOOK_SCRIPT)
        ok(f"Appended to existing pre-commit hook at {hook_path}")
    else:
        hook_path.write_text("#!/bin/sh" + HOOK_SCRIPT)
        hook_path.chmod(0o755)
        ok(f"Installed pre-commit hook at {hook_path}")


# ---------------------------------------------------------------------------
# Main scan
# ---------------------------------------------------------------------------

def scan(root: Path, quiet: bool = False, include_handoff: bool = False):
    cfg = load_config(root)

    if not quiet:
        header(f"repo-scan  {root.name}")
        info(f"Config: {'custom .repo-scan.json' if (root / '.repo-scan.json').exists() else 'defaults'}")

    ensure_dirs(root, cfg)

    step("Detecting languages")
    languages = detect_languages(root, cfg)
    for lang, files in languages.items():
        if files:
            ok(f"{lang.upper()}: {len(files)} files")

    step("Counting lines")
    line_counts = get_line_counts(root, cfg)
    ok(f"{len(line_counts)} files")

    step("Checking git churn")
    churn = get_git_churn(root, cfg)
    ok(f"{len(churn)} files in history")

    step("Analyzing complexity")
    complexity = get_python_complexity(root, languages["py"], cfg)
    if complexity:
        ok(f"{len(complexity)} complex functions (rank {cfg['complexity_min_rank']}+)")
    else:
        info("radon not available or no Python files")

    step("Building dependency graphs")
    ts_deps = get_ts_dep_graph_mermaid(root)
    py_deps = get_python_dep_graph_mermaid(root, languages["py"], cfg)
    ok(f"TS: {'graph generated' if ts_deps else 'skipped (madge not found)' }")
    ok(f"Python: {'graph generated' if py_deps else 'skipped (no imports found)'}")

    step("Building call graphs")
    c_calls = get_c_call_graph_mermaid(root, languages["c"])
    ok(f"C: {'graph generated' if c_calls else 'skipped (cflow not found)'}")

    step("Writing docs")
    write_health_report(root, cfg, line_counts, churn, complexity)
    write_dep_report(root, cfg, ts_deps, py_deps)
    write_call_report(root, cfg, c_calls)
    write_index(root, cfg, line_counts, languages)

    if include_handoff:
        write_handoff(root, cfg, languages, line_counts)

    if not quiet:
        crit = [f for f, s in line_counts.items() if s["lines"] >= cfg["line_crit"]]
        print(fmt(f"\n✓ Done. Open docs/index.md in Obsidian to explore.", GREEN + BOLD))
        if crit:
            warn(f"{len(crit)} file(s) exceed {cfg['line_crit']} lines — see docs/reports/health.md")
        print()


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="repo-scan — repo intelligence tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("repo_path", nargs="?", default=".", help="Repo root (default: cwd)")
    parser.add_argument("--init",          action="store_true", help="Write default .repo-scan.json to repo")
    parser.add_argument("--install-hook",  action="store_true", help="Install git pre-commit hook")
    parser.add_argument("--check-deps",    action="store_true", help="Check required tools")
    parser.add_argument("--handoff",       action="store_true", help="Generate docs/HANDOFF.md bootstrap doc")
    parser.add_argument("--quiet",         action="store_true", help="Minimal output (for hook use)")
    args = parser.parse_args()

    root = Path(args.repo_path).resolve()
    if not root.exists():
        err(f"Path not found: {root}")
        sys.exit(1)

    if args.check_deps:
        check_deps()
        return

    if args.install_hook:
        install_hook(root)
        return

    if args.init:
        step("Writing config")
        write_default_config(root)
        return

    scan(root, quiet=args.quiet, include_handoff=args.handoff)


if __name__ == "__main__":
    main()
