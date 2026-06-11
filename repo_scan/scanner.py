"""Scan pipeline orchestration.

Report writes delegate to ``report_pipeline.write_scan_reports``; this module
no longer imports ``writers`` directly.

Vault: docs/tickets/tkt-0002, docs/tickets/tkt-0008
Vault: docs/research/analysis/2026-06-10-refactor-repo-scan-scanner-py-cc-27-8-co-analysis
Vault: docs/research/sources/url-www-socratopia-app-library-software-engineering-craft-en-cha
Vault: docs/research/sources/url-refactoring-com-catalog-replacenestedconditionalwithguardcla
Vault: docs/research/sources/url-refactoring-com-catalog-consolidateduplicateconditionalfragm
Vault: docs/research/sources/url-refactoring-com-catalog-decomposeconditional-html
Vault: docs/research/sources/url-docs-python-org-3-tutorial-modules-html-packages
Vault: docs/research/sources/gh-python-cpython
Vault: docs/research/sources/arxiv-2401.15298
Vault: docs/research/sources/gh-ThoughtWorksInc-WorkingEffectivelyWithLegacyCode
Vault: docs/research/sources/arxiv-2302.09153
Spec:  docs/specs/2026-06-10-refactor-repo-scan-scanner-py-cc-27-8-co-spec
"""

from dataclasses import dataclass, field
from pathlib import Path

from .behavior import analyze_history, hidden_seams
from .churn import get_git_churn
from .complexity import get_complexity
from .config import load_config
from .digest import write_digest
from .graphs import edges_to_mermaid, get_c_call_graph_mermaid, get_python_dep_edges, get_ts_dep_edges
from .handoff import write_handoff
from .identity import get_directory_tree
from .languages import detect_languages, get_line_counts
from .ranking import rank_files
from .tests_map import find_tested_files, is_test_file
from .report_pipeline import ReportPayload, write_scan_reports
from .trends import compute_delta, load_previous_summary, summarize_metrics
from .utils import BOLD, GREEN, ensure_dirs, fmt, header, info, ok, step, warn
from .writers import write_candidates


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


@dataclass
class ScanContext:
    root: Path
    quiet: bool = False
    include_handoff: bool = False
    cfg: dict = field(default_factory=dict)
    languages: dict = field(default_factory=dict)
    line_counts: dict = field(default_factory=dict)
    churn: list = field(default_factory=list)
    behavior: dict = field(default_factory=dict)
    complexity: list = field(default_factory=list)
    ts_edges: list = field(default_factory=list)
    ts_reason: str = ""
    py_edges: list = field(default_factory=list)
    c_calls: str | None = None
    ranking: list = field(default_factory=list)
    tree: str = ""
    tested: set = field(default_factory=set)
    node_scores: dict = field(default_factory=dict)
    ts_deps: str | None = None
    py_deps: str | None = None
    prev_summary: dict | None = None
    curr_summary: dict = field(default_factory=dict)
    delta: dict | None = None
    seams: list = field(default_factory=list)
    citations: list = field(default_factory=list)


def _prepare_scan(ctx: ScanContext) -> None:
    ctx.cfg = load_config(ctx.root)
    if not ctx.quiet:
        header(f"repo-scan  {ctx.root.name}")
        info(f"Config: {'custom .repo-scan.json' if (ctx.root / '.repo-scan.json').exists() else 'defaults'}")
    ensure_dirs(ctx.root, ctx.cfg)


def _detect_languages(ctx: ScanContext) -> None:
    step("Detecting languages")
    ctx.languages = detect_languages(ctx.root, ctx.cfg)
    for lang, files in ctx.languages.items():
        if files:
            ok(f"{lang.upper()}: {len(files)} files")


def _count_lines(ctx: ScanContext) -> None:
    step("Counting lines")
    ctx.line_counts = get_line_counts(ctx.root, ctx.cfg)
    ok(f"{len(ctx.line_counts)} files")


def _check_git_churn(ctx: ScanContext) -> None:
    step("Checking git churn")
    ctx.churn = get_git_churn(ctx.root, ctx.cfg)
    ok(f"{len(ctx.churn)} files in history")


def _analyze_behavior(ctx: ScanContext) -> None:
    step("Behavioral analysis (git history)")
    ctx.behavior = analyze_history(ctx.root, ctx.cfg, set(ctx.line_counts))
    ok(f"{len(ctx.behavior['coupling'])} coupled pairs, "
       f"{len(ctx.behavior['ownership'])} files with ownership data")


def _analyze_complexity(ctx: ScanContext) -> None:
    step("Analyzing complexity")
    ctx.complexity = get_complexity(ctx.root, ctx.languages["py"], ctx.cfg)
    if ctx.complexity:
        ok(f"{len(ctx.complexity)} complex functions (rank {ctx.cfg['complexity_min_rank']}+)")
    else:
        info("no functions at threshold (or radon/lizard not installed)")


def _build_dependency_graphs(ctx: ScanContext) -> None:
    step("Building dependency graphs")
    ctx.ts_edges, ctx.ts_reason = get_ts_dep_edges(ctx.root, ctx.languages["ts"])
    ctx.py_edges = get_python_dep_edges(ctx.root, ctx.languages["py"], ctx.cfg)
    ok(f"TS: {'graph generated' if ctx.ts_edges else f'skipped ({ctx.ts_reason})'}")
    ok(f"Python: {'graph generated' if ctx.py_edges else 'skipped (no intra-repo imports)'}")


def _build_call_graphs(ctx: ScanContext) -> None:
    step("Building call graphs")
    ctx.c_calls = get_c_call_graph_mermaid(ctx.root, ctx.languages["c"])
    if ctx.languages["c"]:
        ok(f"C: {'graph generated' if ctx.c_calls else 'skipped (cflow not available)'}")
    else:
        ok("C: skipped (no C files)")


def _rank_files(ctx: ScanContext) -> None:
    step("Ranking files")
    all_edges = ctx.py_edges + ctx.ts_edges
    ctx.ranking = rank_files(ctx.line_counts, ctx.churn, ctx.complexity, all_edges,
                             ctx.cfg.get("rank_top_n", 15),
                             exclude_prefix=ctx.cfg["docs_dir"] + "/")
    ctx.tree = get_directory_tree(ctx.root, ctx.cfg)
    ctx.tested = find_tested_files(list(ctx.line_counts))
    for r in ctx.ranking:
        r["tested"] = r["file"] in ctx.tested or is_test_file(r["file"])
    untested_ranked = sum(1 for r in ctx.ranking if not r["tested"])
    ok(f"top {len(ctx.ranking)} files scored ({untested_ranked} without tests)")

    ctx.node_scores = ranking_node_scores(ctx.ranking)
    ctx.ts_deps = edges_to_mermaid(ctx.ts_edges, ctx.node_scores)
    ctx.py_deps = edges_to_mermaid(ctx.py_edges, ctx.node_scores)


def _scan_citations(ctx: ScanContext) -> None:
    from .citations import scan_citations
    step("Scanning code → doc citations")
    ctx.citations = scan_citations(ctx.root, ctx.cfg, ctx.line_counts)
    ok(f"{len(ctx.citations)} citation(s)")


def _write_reports(ctx: ScanContext) -> None:
    step("Writing docs")
    _scan_citations(ctx)
    ctx.prev_summary = load_previous_summary(ctx.root, ctx.cfg)
    from .provenance import vault_health_payload
    vh = vault_health_payload(
        ctx.root, ctx.cfg, ctx.line_counts, ctx.citations, ctx.behavior,
        ranking=ctx.ranking,
    )
    ctx.curr_summary = summarize_metrics(ctx.line_counts, ctx.complexity, ctx.cfg, vh)
    ctx.delta = compute_delta(ctx.prev_summary, ctx.curr_summary)

    all_edges = ctx.py_edges + ctx.ts_edges
    ctx.seams = hidden_seams(ctx.behavior["coupling"], all_edges)
    payload = ReportPayload(
        line_counts=ctx.line_counts,
        languages=ctx.languages,
        churn=ctx.churn,
        complexity=ctx.complexity,
        ranking=ctx.ranking,
        tree=ctx.tree,
        behavior=ctx.behavior,
        seams=ctx.seams,
        ts_mermaid=ctx.ts_deps,
        py_mermaid=ctx.py_deps,
        ts_reason=ctx.ts_reason,
        c_mermaid=ctx.c_calls,
        py_edges=ctx.py_edges,
        ts_edges=ctx.ts_edges,
        curr_summary=ctx.curr_summary,
        delta=ctx.delta,
        citations=ctx.citations,
    )
    write_scan_reports(ctx.root, ctx.cfg, payload)


def _maybe_run_radar(ctx: ScanContext) -> None:
    if not ctx.cfg.get("radar_enabled"):
        return
    write_candidates(ctx.root, ctx.cfg, ctx.churn, ctx.complexity, tested=ctx.tested)
    churn_files = {c["file"] for c in ctx.churn}
    cc_files = {item["file"] for item in ctx.complexity}
    if churn_files & cc_files and not ctx.quiet:
        info("RADAR candidates detected — run `radar full` to research the top one")


def _maybe_run_tickets(ctx: ScanContext) -> None:
    if not ctx.cfg.get("tickets_enabled", True):
        return
    from .tickets import generate_tickets
    created, resolved = generate_tickets(ctx.root, ctx.cfg, {
        "line_counts": ctx.line_counts, "ranking": ctx.ranking, "churn": ctx.churn,
        "complexity": ctx.complexity, "tested": ctx.tested, "behavior": ctx.behavior,
        "seams": ctx.seams, "py_edges": ctx.py_edges, "ts_edges": ctx.ts_edges,
    })
    if ctx.quiet:
        return
    if created:
        info(f"{created} ticket(s) proposed — review {ctx.cfg['docs_dir']}/tickets/board.md "
             f"or `repo-scan tickets`")
    for t in resolved:
        info(f"{t['id']} looks resolved (metric cleared) — "
             f"`repo-scan tickets done {t['id']}`")


def _maybe_write_handoff(ctx: ScanContext) -> None:
    if ctx.include_handoff:
        write_handoff(ctx.root, ctx.cfg, ctx.languages, ctx.line_counts)


def _print_completion(ctx: ScanContext) -> None:
    if ctx.quiet:
        return
    crit = [f for f, s in ctx.line_counts.items() if s["lines"] >= ctx.cfg["line_crit"]]
    docs = ctx.cfg["docs_dir"]
    print(fmt(f"\n✓ Done. Open {docs}/index.md in Obsidian to explore.", GREEN + BOLD))
    if crit:
        warn(f"{len(crit)} file(s) exceed {ctx.cfg['line_crit']} lines — see {docs}/reports/health.md")
    print()


def _post_scan_actions(ctx: ScanContext) -> None:
    _maybe_run_radar(ctx)
    _maybe_run_tickets(ctx)
    _maybe_write_handoff(ctx)
    _print_completion(ctx)


def scan(root: Path, quiet: bool = False, include_handoff: bool = False):
    ctx = ScanContext(root=root, quiet=quiet, include_handoff=include_handoff)
    _prepare_scan(ctx)
    _detect_languages(ctx)
    _count_lines(ctx)
    _check_git_churn(ctx)
    _analyze_behavior(ctx)
    _analyze_complexity(ctx)
    _build_dependency_graphs(ctx)
    _build_call_graphs(ctx)
    _rank_files(ctx)
    _write_reports(ctx)
    _post_scan_actions(ctx)


def collect_digest_inputs(root: Path, cfg: dict) -> dict:
    """Lightweight collection pass for the --digest flag (no report writes)."""
    languages = detect_languages(root, cfg)
    line_counts = get_line_counts(root, cfg)
    churn = get_git_churn(root, cfg)
    complexity = get_complexity(root, languages["py"], cfg)
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
