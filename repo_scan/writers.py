"""Markdown report writers + scan.json sidecar + AGENTS.md scaffold."""

import json
from pathlib import Path

from .graphs import coupling_to_mermaid
from .identity import detect_entry_points, detect_manifests, readme_summary
from .trends import trend_callout
from .utils import chart_label, git_branch, git_last_commit, git_remote_url, now_iso, ok, warn, write_doc


# ---------------------------------------------------------------------------
# Visual helpers — Mermaid charts + Obsidian callouts (also render on GitHub)
# ---------------------------------------------------------------------------

def callout(kind: str, title: str, body_lines: list[str] | None = None) -> list[str]:
    """Obsidian callout block (`> [!warning] ...`). GitHub renders the common
    kinds (note/tip/warning) as alerts too."""
    lines = [f"> [!{kind}] {title}"]
    for line in body_lines or []:
        lines.append(f"> {line}")
    return lines


def mermaid_pie(title: str, pairs: list[tuple[str, float]]) -> list[str]:
    if not pairs:
        return []
    lines = ["```mermaid", f'pie title {title}']
    for label, value in pairs:
        lines.append(f'    "{label}" : {value:g}')
    lines += ["```", ""]
    return lines


def mermaid_bar(title: str, y_title: str, labels: list[str], values: list[float],
                y_max: float | None = None) -> list[str]:
    if not labels or not values:
        return []
    top = y_max if y_max is not None else max(values) or 1
    label_str = ", ".join(f'"{chart_label(l)}"' for l in labels)
    value_str = ", ".join(f"{v:g}" for v in values)
    return [
        "```mermaid",
        "xychart-beta",
        f'    title "{title}"',
        f"    x-axis [{label_str}]",
        f'    y-axis "{y_title}" 0 --> {top:g}',
        f"    bar [{value_str}]",
        "```",
        "",
    ]


def mermaid_quadrant(title: str, x_axis: str, y_axis: str,
                     quadrants: tuple[str, str, str, str],
                     points: list[tuple[str, float, float]]) -> list[str]:
    """quadrantChart with normalized 0..1 points. quadrants order:
    (top-right, top-left, bottom-left, bottom-right)."""
    if not points:
        return []
    lines = [
        "```mermaid",
        "quadrantChart",
        f"    title {title}",
        f"    x-axis {x_axis}",
        f"    y-axis {y_axis}",
        f"    quadrant-1 {quadrants[0]}",
        f"    quadrant-2 {quadrants[1]}",
        f"    quadrant-3 {quadrants[2]}",
        f"    quadrant-4 {quadrants[3]}",
    ]
    seen: set[str] = set()
    for label, x, y in points:
        name = chart_label(label)
        while name in seen:
            name += "·"
        seen.add(name)
        lines.append(f"    {name}: [{min(max(x, 0.02), 0.98):.2f}, {min(max(y, 0.02), 0.98):.2f}]")
    lines += ["```", ""]
    return lines


def churn_complexity_quadrant(rows: list[dict], title: str = "Churn vs complexity") -> list[str]:
    """Shared quadrant: x=churn, y=complexity. Top-right = RADAR candidates."""
    plot = [r for r in rows if r.get("commits", 0) or r.get("complexity", 0)]
    max_commits = max((r["commits"] for r in plot), default=0)
    max_cc = max((r["complexity"] for r in plot), default=0)
    if not plot or not max_commits or not max_cc:
        return []
    points = [(r["file"], r["commits"] / max_commits, r["complexity"] / max_cc)
              for r in plot[:12]]
    return mermaid_quadrant(
        title,
        "Low churn --> High churn",
        "Low complexity --> High complexity",
        ("RADAR candidates", "Complex but stable", "Quiet", "Hot but simple"),
        points,
    )


# --- health.md section builders (pure: inputs -> list[str]) ----------------

def _health_dir_pie_section(line_counts: dict) -> list[str]:
    by_dir: dict[str, int] = {}
    for rel, stats in line_counts.items():
        top = rel.split("/")[0] if "/" in rel else "(root)"
        by_dir[top] = by_dir.get(top, 0) + stats["lines"]
    dir_pairs = sorted(by_dir.items(), key=lambda x: x[1], reverse=True)
    if len(dir_pairs) > 7:
        rest = sum(v for _, v in dir_pairs[7:])
        dir_pairs = dir_pairs[:7] + [("other", rest)]
    dir_pairs = [(d, v) for d, v in dir_pairs if v > 0]
    return ["## Where the code lives", ""] + mermaid_pie("Lines of code by directory", dir_pairs)


def _health_sizes_section(line_counts: dict, warn_n: int, crit_n: int) -> list[str]:
    lines = [
        "## File sizes",
        "",
        "| File | Lines | Size | Status |",
        "|------|-------|------|--------|",
    ]
    for rel, stats in sorted(line_counts.items(), key=lambda x: x[1]["lines"], reverse=True)[:40]:
        n = stats["lines"]
        kb = stats["bytes"] / 1024
        status = "**critical**" if n >= crit_n else ("*large*" if n >= warn_n else "ok")
        lines.append(f"| `{rel}` | {n} | {kb:.1f} KB | {status} |")
    return lines + [""]


def _health_complexity_section(complexity: list) -> list[str]:
    if not complexity:
        return ["## Complexity", "", "_radon not available or no Python files_", ""]
    lines = [
        "## Complexity hotspots",
        "",
        "| File | Function | Rank | Score | Line |",
        "|------|----------|------|-------|------|",
    ]
    for item in complexity[:20]:
        lines.append(f"| `{item['file']}` | `{item['name']}` | {item['rank']} | {item['complexity']} | {item['lineno']} |")
    return lines + [""]


def _health_churn_section(churn: list) -> list[str]:
    if not churn:
        return []
    top_churn = churn[:10]
    lines = ["## Git churn (most changed files)", ""]
    lines += mermaid_bar("Commits touching each file", "Commits",
                         [c["file"] for c in top_churn],
                         [c["commits"] for c in top_churn])
    lines += ["| File | Commits |", "|------|---------|"]
    lines += [f"| `{item['file']}` | {item['commits']} |" for item in churn[:15]]
    return lines + [""]


def _health_knowledge_section(behavior: dict | None, cfg: dict) -> list[str]:
    if not behavior or not behavior.get("ownership"):
        return []
    silo_share = cfg.get("silo_min_share", 0.9)
    stale_days = cfg.get("stale_days", 180)
    age = behavior.get("age_days", {})
    lines = [
        "## Knowledge map (bus factor)",
        "",
        "_Top-author share near 100% on an active file = knowledge silo._",
        "",
        "| File | Commits | Authors | Top author share | Age (days) | Flag |",
        "|------|---------|---------|------------------|------------|------|",
    ]
    for o in behavior["ownership"][:15]:
        flags = []
        if o["top_share"] >= silo_share and o["commits"] >= 5 and o["authors"] == 1:
            flags.append("silo")
        if age.get(o["file"], 0) >= stale_days:
            flags.append("stale")
        lines.append(f"| `{o['file']}` | {o['commits']} | {o['authors']} | "
                     f"{o['top_share']:.0%} | {age.get(o['file'], '?')} | "
                     f"{', '.join(flags) or '—'} |")
    return lines + [""]


def _health_actions_section(line_counts: dict, crit_n: int) -> list[str]:
    alerts = [f for f, s in line_counts.items() if s["lines"] >= crit_n]
    if not alerts:
        return []
    return ["## Action items", ""] + callout(
        "warning",
        f"{len(alerts)} file(s) over the {crit_n}-line critical threshold",
        [f"- [ ] Split `{a}` ({line_counts[a]['lines']} lines)" for a in alerts],
    ) + [""]


def _health_vault_section(root: Path, cfg: dict, line_counts: dict,
                          citations: list | None, behavior: dict | None,
                          ranking: list | None) -> list[str]:
    from .provenance import vault_coverage
    scan_stub = {
        "files": line_counts,
        "ranking": ranking or [],
        "behavior": behavior or {},
        "citations": citations or [],
    }
    cov = vault_coverage(root, cfg, scan_stub, citations or [])
    if not cov["docs"]:
        return []
    pct = int(round(cov["coverage_pct"] * 100))
    kind = "warning" if pct < 70 else ("note" if pct < 90 else "tip")
    lines = callout(
        kind,
        f"Vault provenance: {cov['healthy']}/{cov['docs']} docs fully traced ({pct}%)",
        [
            f"Untracked ranked code: {cov['untracked_code_count']}",
            f"Stale docs: {cov['stale_docs_count']}",
        ],
    ) + ["", "## Vault health", "",
         "| Metric | Value |",
         "|--------|-------|",
         f"| Coverage | {pct}% ({cov['healthy']}/{cov['docs']}) |",
         f"| Untracked code (ranked) | {cov['untracked_code_count']} |",
         f"| Stale docs | {cov['stale_docs_count']} |"]
    for kind_name, count in sorted(cov.get("orphans_by_kind", {}).items()):
        if count:
            lines.append(f"| Orphan {kind_name}s | {count} |")
    lines.append("")
    return lines


def write_health_report(root: Path, cfg: dict, line_counts: dict, churn: list, complexity: list,
                        behavior: dict | None = None, citations: list | None = None,
                        ranking: list | None = None):
    warn_n, crit_n = cfg["line_warn"], cfg["line_crit"]
    lines = [
        "# Health report",
        f"_Generated {now_iso()}_  |  _Branch: {git_branch(root)}_  |  _Last commit: {git_last_commit(root)}_",
        "",
    ]
    lines += _health_vault_section(root, cfg, line_counts, citations, behavior, ranking)
    lines += _health_dir_pie_section(line_counts)
    lines += _health_sizes_section(line_counts, warn_n, crit_n)
    lines += _health_complexity_section(complexity)
    lines += _health_churn_section(churn)
    lines += _health_knowledge_section(behavior, cfg)
    lines += _health_actions_section(line_counts, crit_n)
    write_doc(root / cfg["docs_dir"] / "reports" / "health.md", "\n".join(lines), root)


def write_coupling_report(root: Path, cfg: dict, coupling: list[dict], seams: list[dict],
                          py_edges: list[tuple[str, str]] | None = None,
                          ts_edges: list[tuple[str, str]] | None = None,
                          line_counts: dict | None = None):
    """Change coupling: files that move together in commits.

    When ``line_counts`` is provided, prepends a Mermaid network of the top
    coupled pairs (capped by ``diagram_max_coupling_edges``); the table uses
    the same cap.
    """
    docs = root / cfg["docs_dir"]
    min_shared = cfg.get("coupling_min_shared", 4)
    min_degree = cfg.get("coupling_min_degree", 50)
    max_edges = cfg.get("diagram_max_coupling_edges", 20)
    seam_keys = {(s["a"], s["b"]) for s in seams}

    lines = [
        "# Change coupling",
        f"_Generated {now_iso()}_",
        "",
        f"Files that change together (≥{min_shared} shared commits, ≥{min_degree}% degree).",
        "Coupled pairs **without** an import edge are hidden seams — an implicit",
        "contract the dependency graph can't see.",
        "",
    ]
    if coupling and line_counts is not None:
        import_edges = (py_edges or []) + (ts_edges or [])
        chart = coupling_to_mermaid(coupling, seams, import_edges, line_counts,
                                    max_edges=max_edges)
        if chart:
            lines += ["```mermaid", chart, "```", ""]
    if seams:
        lines += callout(
            "warning",
            f"{len(seams)} hidden seam(s): coupled in history, no import edge",
            [f"- `{s['a']}` ↔ `{s['b']}` ({s['degree']}% over {s['shared']} commits)"
             for s in seams[:5]],
        ) + [""]
    if coupling:
        lines += [
            "| File A | File B | Shared commits | Degree | Import edge |",
            "|--------|--------|----------------|--------|-------------|",
        ]
        for c in coupling[:max_edges]:
            seam = (c["a"], c["b"]) in seam_keys
            lines.append(f"| `{c['a']}` | `{c['b']}` | {c['shared']} | {c['degree']}% | "
                         f"{'**none — seam**' if seam else 'yes'} |")
    else:
        lines += callout("tip", "No significant change coupling at current thresholds")
    lines.append("")
    write_doc(docs / "reports" / "coupling.md", "\n".join(lines), root)


def write_dep_report(root: Path, cfg: dict, ts_mermaid: str | None, py_mermaid: str | None,
                     ts_reason: str = ""):
    ts = now_iso()
    docs = root / cfg["docs_dir"]

    lines = ["# Dependency graph", f"_Generated {ts}_", ""]

    if ts_mermaid or py_mermaid:
        lines += ["_Node color = PageRank tier: red = hub, amber = mid, gray = leaf._", ""]

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


# --- index.md section builders (pure: inputs -> list[str]) -----------------

def _index_size_callout(line_counts: dict, large: list, critical: list,
                        warn_n: int, crit_n: int) -> list[str]:
    if critical:
        worst = max(critical, key=lambda f: line_counts[f]["lines"])
        return callout(
            "warning",
            f"{len(critical)} file(s) exceed {crit_n} lines — see [[reports/health]]",
            [f"Largest: `{worst}` ({line_counts[worst]['lines']} lines)"],
        ) + [""]
    if large:
        return callout(
            "note",
            f"No critical files; {len(large)} file(s) above the {warn_n}-line watermark",
        ) + [""]
    return callout("tip", f"Healthy: every file is under {warn_n} lines") + [""]


def _index_overview_section(root: Path, line_counts: dict, languages: dict,
                            large: list, critical: list,
                            warn_n: int, crit_n: int) -> list[str]:
    total_files = sum(len(v) for v in languages.values())
    total_lines = sum(s["lines"] for s in line_counts.values())
    lang_summary = ", ".join(f"{k.upper()}: {len(v)}" for k, v in languages.items() if v)
    manifests = detect_manifests(root)
    lines = [
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
    return lines + [""]


def _index_entry_points_section(root: Path) -> list[str]:
    entry_points = detect_entry_points(root)
    if not entry_points:
        return []
    return ["## Entry points", ""] + [f"- {e}" for e in entry_points] + [""]


def _index_ranking_section(ranking: list[dict] | None) -> list[str]:
    if not ranking:
        return []
    lines = [
        "## Start here (ranked by importance)",
        "",
        "_Composite of import-graph PageRank × git churn × complexity × size._",
        "_\"Imported by\" counts direct dependents only; PageRank captures transitive importance._",
        "",
        "| File | Score | PageRank | Imported by | Commits | CC | Lines | Tests |",
        "|------|-------|----------|-------------|---------|----|-------|-------|",
    ]
    for r in ranking:
        tests = "yes" if r.get("tested") else "**no**"
        lines.append(f"| `{r['file']}` | {r['score']} | {r.get('pagerank', 0):.4f} | "
                     f"{r['imported_by']} | {r['commits']} | {r['complexity']} | "
                     f"{r['lines']} | {tests} |")
    lines.append("")
    top = ranking[:8]
    lines += mermaid_bar("Importance score (top files)", "Score",
                         [r["file"] for r in top], [r["score"] for r in top], y_max=100)
    lines += churn_complexity_quadrant(ranking, "Where to focus: churn vs complexity")
    return lines


_INDEX_LINKS = [
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


def _index_actions_section(line_counts: dict, critical: list) -> list[str]:
    if not critical:
        return []
    return ["## Action items", ""] + \
        [f"- [ ] Split `{f}` ({line_counts[f]['lines']} lines)" for f in critical] + [""]


def write_index(root: Path, cfg: dict, line_counts: dict, languages: dict,
                ranking: list[dict] | None = None, tree: str = "",
                delta: dict | None = None):
    warn_n, crit_n = cfg["line_warn"], cfg["line_crit"]
    large = [f for f, s in line_counts.items() if s["lines"] >= warn_n]
    critical = [f for f, s in line_counts.items() if s["lines"] >= crit_n]
    summary = readme_summary(root)

    lines = ["# Repo index", f"_Last scan: {now_iso()}_", ""]
    if summary:
        lines += [f"> {summary}", ""]
    lines += _index_size_callout(line_counts, large, critical, warn_n, crit_n)
    lines += trend_callout(delta)
    lines += _index_overview_section(root, line_counts, languages, large, critical,
                                     warn_n, crit_n)
    lines += _index_entry_points_section(root)
    lines += _index_ranking_section(ranking)
    if tree:
        lines += ["## Structure", "", "```", tree, "```", ""]
    lines += _INDEX_LINKS
    lines += _index_actions_section(line_counts, critical)
    write_doc(root / cfg["docs_dir"] / "index.md", "\n".join(lines), root)


def write_scan_json(root: Path, cfg: dict, line_counts: dict, languages: dict,
                    churn: list, complexity: list, ranking: list,
                    py_edges: list, ts_edges: list, behavior: dict | None = None,
                    citations: list | None = None):
    """Machine-readable sidecar so agents don't have to parse markdown."""
    docs = root / cfg["docs_dir"]
    payload = scan_payload(root, cfg, line_counts, languages, churn, complexity,
                           ranking, py_edges, ts_edges, behavior,
                           citations=citations)
    path = docs / "scan.json"
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    ok(str(path.relative_to(root)))


def scan_payload(root: Path, cfg: dict, line_counts: dict, languages: dict,
                 churn: list, complexity: list, ranking: list,
                 py_edges: list, ts_edges: list, behavior: dict | None = None,
                 citations: list | None = None) -> dict:
    """Pure scan.json payload builder, separated from file I/O."""
    cites = citations or []
    from .provenance import vault_health_payload
    vault_health = vault_health_payload(
        root, cfg, line_counts, cites, behavior, ranking=ranking,
    )
    return {
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
        "behavior": {
            "coupling": (behavior or {}).get("coupling", [])[:20],
            "ownership": (behavior or {}).get("ownership", [])[:20],
            "age_days": (behavior or {}).get("age_days", {}),
        },
        "citations": cites,
        "vault_health": vault_health,
        "config": cfg,
    }


def write_candidates(root: Path, cfg: dict, churn: list, complexity: list,
                     tested: set | None = None):
    """RADAR trigger feed: files that are both high-churn and complex.
    Untested candidates get a 2x priority boost — churn x complexity x no
    safety net is the strongest possible refactor trigger."""
    docs = root / cfg["docs_dir"]
    churn_by_file = {c["file"]: c["commits"] for c in churn}
    cc_by_file: dict[str, int] = {}
    for item in complexity:
        cc_by_file[item["file"]] = cc_by_file.get(item["file"], 0) + item["complexity"]

    candidates = []
    for f in set(churn_by_file) & set(cc_by_file):
        has_tests = tested is None or f in tested
        priority = churn_by_file[f] * cc_by_file[f] * (1 if has_tests else 2)
        candidates.append({
            "file": f,
            "commits": churn_by_file[f],
            "complexity": cc_by_file[f],
            "tested": has_tests,
            "priority": priority,
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
        lines += churn_complexity_quadrant(candidates, "Candidate zone (top-right)")
        lines += [
            "| File | Commits | Complexity | Tests | Priority |",
            "|------|---------|------------|-------|----------|",
        ]
        for c in candidates[:10]:
            tests = "yes" if c["tested"] else "**no** (2x)"
            lines.append(f"| `{c['file']}` | {c['commits']} | {c['complexity']} | "
                         f"{tests} | {c['priority']} |")
    else:
        lines += callout("tip", "No files are currently both high-churn and high-complexity")
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
