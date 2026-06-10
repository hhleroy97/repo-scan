"""Markdown report writers + scan.json sidecar + AGENTS.md scaffold."""

import json
from pathlib import Path

from .identity import detect_entry_points, detect_manifests, readme_summary
from .utils import git_branch, git_last_commit, git_remote_url, now_iso, ok, warn, write_doc


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


def write_dep_report(root: Path, cfg: dict, ts_mermaid: str | None, py_mermaid: str | None,
                     ts_reason: str = ""):
    ts = now_iso()
    docs = root / cfg["docs_dir"]

    lines = ["# Dependency graph", f"_Generated {ts}_", ""]

    if ts_mermaid:
        lines += ["## TypeScript / JavaScript", "", "```mermaid", ts_mermaid, "```", ""]
    else:
        lines += ["## TypeScript / JavaScript", "", f"_Skipped: {ts_reason or 'no graph'}_", ""]

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


def write_index(root: Path, cfg: dict, line_counts: dict, languages: dict,
                ranking: list[dict] | None = None, tree: str = ""):
    ts = now_iso()
    docs = root / cfg["docs_dir"]
    warn_n = cfg["line_warn"]
    crit_n = cfg["line_crit"]

    total_files = sum(len(v) for v in languages.values())
    total_lines = sum(s["lines"] for s in line_counts.values())
    lang_summary = ", ".join(f"{k.upper()}: {len(v)}" for k, v in languages.items() if v)
    large = [f for f, s in line_counts.items() if s["lines"] >= warn_n]
    critical = [f for f, s in line_counts.items() if s["lines"] >= crit_n]
    manifests = detect_manifests(root)
    entry_points = detect_entry_points(root)
    summary = readme_summary(root)

    lines = [
        "# Repo index",
        f"_Last scan: {ts}_",
        "",
    ]
    if summary:
        lines += [f"> {summary}", ""]
    lines += [
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
        f"| Remote | {git_remote_url(root)} |",
    ]
    if manifests:
        lines.append(f"| Manifests | {', '.join(f'`{m}`' for m in manifests)} |")
    lines.append("")

    if entry_points:
        lines += ["## Entry points", ""]
        lines += [f"- {e}" for e in entry_points]
        lines.append("")

    if ranking:
        lines += [
            "## Start here (ranked by importance)",
            "",
            "_Composite of import-graph PageRank × git churn × complexity × size._",
            "_\"Imported by\" counts direct dependents only; PageRank captures transitive importance._",
            "",
            "| File | Score | PageRank | Imported by | Commits | CC | Lines |",
            "|------|-------|----------|-------------|---------|----|-------|",
        ]
        for r in ranking:
            lines.append(f"| `{r['file']}` | {r['score']} | {r.get('pagerank', 0):.4f} | "
                         f"{r['imported_by']} | {r['commits']} | {r['complexity']} | {r['lines']} |")
        lines.append("")

    if tree:
        lines += ["## Structure", "", "```", tree, "```", ""]

    lines += [
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


def write_scan_json(root: Path, cfg: dict, line_counts: dict, languages: dict,
                    churn: list, complexity: list, ranking: list,
                    py_edges: list, ts_edges: list):
    """Machine-readable sidecar so agents don't have to parse markdown."""
    docs = root / cfg["docs_dir"]
    payload = {
        "schema_version": 1,
        "generated_at": now_iso(),
        "repo": {
            "name": root.name,
            "remote": git_remote_url(root),
            "branch": git_branch(root),
            "last_commit": git_last_commit(root),
            "manifests": detect_manifests(root),
            "entry_points": detect_entry_points(root),
        },
        "languages": {k: len(v) for k, v in languages.items() if v},
        "files": line_counts,
        "churn": churn,
        "complexity": complexity,
        "ranking": ranking,
        "dependency_edges": {
            "python": [list(e) for e in py_edges],
            "typescript": [list(e) for e in ts_edges],
        },
        "config": cfg,
    }
    path = docs / "scan.json"
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    ok(str(path.relative_to(root)))


def write_candidates(root: Path, cfg: dict, churn: list, complexity: list):
    """RADAR trigger feed: files that are both high-churn and complex."""
    docs = root / cfg["docs_dir"]
    churn_by_file = {c["file"]: c["commits"] for c in churn}
    cc_by_file: dict[str, int] = {}
    for item in complexity:
        cc_by_file[item["file"]] = cc_by_file.get(item["file"], 0) + item["complexity"]

    candidates = []
    for f in set(churn_by_file) & set(cc_by_file):
        candidates.append({
            "file": f,
            "commits": churn_by_file[f],
            "complexity": cc_by_file[f],
            "priority": churn_by_file[f] * cc_by_file[f],
        })
    candidates.sort(key=lambda x: x["priority"], reverse=True)

    lines = [
        "# RADAR candidates",
        f"_Generated {now_iso()}_",
        "",
        "Files that are both high-churn and high-complexity — the most valuable",
        "targets for external research. Consumed by `radar` as a trigger feed.",
        "",
    ]
    if candidates:
        lines += [
            "| File | Commits | Complexity | Priority |",
            "|------|---------|------------|----------|",
        ]
        for c in candidates[:10]:
            lines.append(f"| `{c['file']}` | {c['commits']} | {c['complexity']} | {c['priority']} |")
    else:
        lines.append("_No files are currently both high-churn and high-complexity._")
    lines.append("")

    write_doc(docs / "research" / "candidates.md", "\n".join(lines), root)


AGENTS_TEMPLATE = """\
# AGENTS.md

Rules for AI agents working in this repository. Generated by `repo-scan --init-agents`
— edit to fit this repo, then commit.

## Ownership

- `docs/research/`  — RADAR writes, human annotates
- `docs/specs/`     — RADAR drafts, human approves before merge
- `docs/reports/`   — repo-scan writes, do not edit manually
- Source code       — human writes, RADAR never touches directly

## Gate behavior

- Gate 1 (post-Analyze): always require approval
- Gate 2 (post-Audit): always require approval

Gates are configured per-repo in `.repo-scan.json` under `"gates"`.

## Off-limits

- Never modify files outside `docs/` without explicit approval
- Never commit to main directly
- Never delete existing source files in `docs/research/sources/`

## Context

- Start from `docs/index.md` (human view) or `docs/scan.json` (machine view)
- Diagrams are always Mermaid
"""


def write_agents_md(root: Path):
    path = root / "AGENTS.md"
    if path.exists():
        warn("AGENTS.md already exists — skipping (edit it directly)")
        return
    path.write_text(AGENTS_TEMPLATE, encoding="utf-8")
    ok(f"wrote {path.name} — review the ownership rules and commit")
