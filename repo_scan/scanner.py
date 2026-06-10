"""Scan pipeline orchestration."""

from pathlib import Path

from .churn import get_git_churn
from .complexity import get_python_complexity
from .config import load_config
from .digest import write_digest
from .graphs import edges_to_mermaid, get_c_call_graph_mermaid, get_python_dep_edges, get_ts_dep_edges
from .handoff import write_handoff
from .identity import get_directory_tree
from .languages import detect_languages, get_line_counts
from .ranking import rank_files
from .utils import BOLD, GREEN, ensure_dirs, fmt, header, info, ok, step, warn
from .writers import (
    write_call_report,
    write_candidates,
    write_dep_report,
    write_health_report,
    write_index,
    write_scan_json,
)


def ranking_node_scores(ranking: list[dict]) -> dict[str, float]:
    """Map ranking rows to dep-graph node names (dotted modules for Python,
    relative paths for TS) so graphs can tint nodes by PageRank tier."""
    scores: dict[str, float] = {}
    for r in ranking:
        pr = r.get("pagerank", 0.0)
        path = r["file"]
        scores[path] = pr
        if path.endswith(".py"):
            parts = path[:-3].split("/")
            if parts[-1] == "__init__":
                parts = parts[:-1]
            scores[".".join(parts)] = pr
    return scores


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
    ts_edges, ts_reason = get_ts_dep_edges(root, languages["ts"])
    py_edges = get_python_dep_edges(root, languages["py"], cfg)
    ok(f"TS: {'graph generated' if ts_edges else f'skipped ({ts_reason})'}")
    ok(f"Python: {'graph generated' if py_edges else 'skipped (no intra-repo imports)'}")

    step("Building call graphs")
    c_calls = get_c_call_graph_mermaid(root, languages["c"])
    if languages["c"]:
        ok(f"C: {'graph generated' if c_calls else 'skipped (cflow not available)'}")
    else:
        ok("C: skipped (no C files)")

    step("Ranking files")
    all_edges = py_edges + ts_edges
    ranking = rank_files(line_counts, churn, complexity, all_edges,
                         cfg.get("rank_top_n", 15), exclude_prefix=cfg["docs_dir"] + "/")
    tree = get_directory_tree(root, cfg)
    ok(f"top {len(ranking)} files scored")

    node_scores = ranking_node_scores(ranking)
    ts_deps = edges_to_mermaid(ts_edges, node_scores)
    py_deps = edges_to_mermaid(py_edges, node_scores)

    step("Writing docs")
    write_health_report(root, cfg, line_counts, churn, complexity)
    write_dep_report(root, cfg, ts_deps, py_deps, ts_reason)
    write_call_report(root, cfg, c_calls)
    write_index(root, cfg, line_counts, languages, ranking, tree)
    write_scan_json(root, cfg, line_counts, languages, churn, complexity,
                    ranking, py_edges, ts_edges)

    if cfg.get("radar_enabled"):
        write_candidates(root, cfg, churn, complexity)
        churn_files = {c["file"] for c in churn}
        cc_files = {item["file"] for item in complexity}
        if churn_files & cc_files and not quiet:
            info("RADAR candidates detected — run `radar full` to research the top one")

    if include_handoff:
        write_handoff(root, cfg, languages, line_counts)

    if not quiet:
        crit = [f for f, s in line_counts.items() if s["lines"] >= cfg["line_crit"]]
        docs = cfg["docs_dir"]
        print(fmt(f"\n✓ Done. Open {docs}/index.md in Obsidian to explore.", GREEN + BOLD))
        if crit:
            warn(f"{len(crit)} file(s) exceed {cfg['line_crit']} lines — see {docs}/reports/health.md")
        print()


def collect_digest_inputs(root: Path, cfg: dict) -> dict:
    """Lightweight collection pass for the --digest flag (no report writes)."""
    languages = detect_languages(root, cfg)
    line_counts = get_line_counts(root, cfg)
    churn = get_git_churn(root, cfg)
    complexity = get_python_complexity(root, languages["py"], cfg)
    edges = get_python_dep_edges(root, languages["py"], cfg) + get_ts_dep_edges(root, languages["ts"])[0]
    ranking = rank_files(line_counts, churn, complexity, edges,
                         cfg.get("rank_top_n", 15), exclude_prefix=cfg["docs_dir"] + "/")
    tree = get_directory_tree(root, cfg)
    return {
        "line_counts": line_counts, "languages": languages, "churn": churn,
        "complexity": complexity, "ranking": ranking, "tree": tree,
    }


def run_digest(root: Path) -> Path:
    cfg = load_config(root)
    ensure_dirs(root, cfg)
    data = collect_digest_inputs(root, cfg)
    return write_digest(root, cfg, data["line_counts"], data["languages"],
                        data["churn"], data["complexity"], data["ranking"], data["tree"])
