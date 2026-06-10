"""Important-files ranking from signals the scan already collects.

The structural term is PageRank over the import graph (inline power
iteration, no networkx — per the approved spec in docs/specs/), so
transitively depended-on hub modules rank above direct-import counts alone.
"""


def _module_to_file(module: str, line_counts: dict) -> str | None:
    """Map a dotted module or relative path back to a counted file path."""
    if module in line_counts:
        return module
    candidate = module.replace(".", "/")
    for suffix in [".py", "/__init__.py"]:
        if candidate + suffix in line_counts:
            return candidate + suffix
    return None


def _build_file_adjacency(dep_edges: list[tuple[str, str]],
                          line_counts: dict) -> dict[str, list[str]]:
    """Directed adjacency (src imports dst) over resolved file paths.

    Stricter than the in-degree count: an edge is kept only when BOTH
    endpoints resolve via _module_to_file (in-degree only ever resolved dst).
    """
    adjacency: dict[str, list[str]] = {}
    for src, dst in dep_edges:
        src_f = _module_to_file(src, line_counts)
        dst_f = _module_to_file(dst, line_counts)
        if src_f and dst_f and src_f != dst_f:
            adjacency.setdefault(src_f, []).append(dst_f)
    return adjacency


def _pagerank(nodes: set[str], adjacency: dict[str, list[str]],
              alpha: float = 0.85, max_iter: int = 100,
              tol: float = 1e-6) -> dict[str, float]:
    """Standard damped PageRank with dangling-node redistribution.

    `nodes` should be the edge-incident node set; callers map isolated files
    to 0 outside (running PageRank over an all-dangling universe would just
    return uniform 1/n).
    """
    if not nodes:
        return {}
    n = len(nodes)
    rank = {node: 1.0 / n for node in nodes}
    out_neighbors = {node: [d for d in adjacency.get(node, []) if d in nodes]
                     for node in nodes}

    for _ in range(max_iter):
        dangling_mass = sum(rank[node] for node in nodes if not out_neighbors[node])
        new_rank = {node: (1.0 - alpha) / n + alpha * dangling_mass / n
                    for node in nodes}
        for node in nodes:
            targets = out_neighbors[node]
            if targets:
                share = alpha * rank[node] / len(targets)
                for target in targets:
                    new_rank[target] += share
        delta = sum(abs(new_rank[node] - rank[node]) for node in nodes)
        rank = new_rank
        if delta < tol:
            break
    return rank


def rank_files(line_counts: dict, churn: list, complexity: list,
               dep_edges: list[tuple[str, str]], top_n: int = 15,
               exclude_prefix: str = "docs/") -> list[dict]:
    """Composite importance score: PageRank centrality x churn x complexity x size.

    Centrality is import-graph PageRank (inline, zero-dependency); files with
    no incident resolved edges score 0 on that term. `imported_by` stays the
    direct in-degree count for transparency. Generated docs are excluded so
    the scan output never ranks itself.
    """
    line_counts = {f: s for f, s in line_counts.items() if not f.startswith(exclude_prefix)}
    if not line_counts:
        return []

    in_degree: dict[str, int] = {}
    for _, dst in dep_edges:
        f = _module_to_file(dst, line_counts)
        if f:
            in_degree[f] = in_degree.get(f, 0) + 1

    adjacency = _build_file_adjacency(dep_edges, line_counts)
    incident = set(adjacency) | {d for targets in adjacency.values() for d in targets}
    pagerank = _pagerank(incident, adjacency) if adjacency else {}

    churn_by_file = {c["file"]: c["commits"] for c in churn}
    cc_by_file: dict[str, int] = {}
    for item in complexity:
        cc_by_file[item["file"]] = cc_by_file.get(item["file"], 0) + item["complexity"]

    max_pr = max(pagerank.values(), default=0.0)
    max_churn = max(churn_by_file.values(), default=0) or 1
    max_cc = max(cc_by_file.values(), default=0) or 1
    max_lines = max((s["lines"] for s in line_counts.values()), default=0) or 1

    ranked = []
    for f, stats in line_counts.items():
        centrality = pagerank.get(f, 0.0) / max_pr if max_pr > 0 else 0.0
        churn_score = churn_by_file.get(f, 0) / max_churn
        cc_score = cc_by_file.get(f, 0) / max_cc
        size_score = stats["lines"] / max_lines
        score = 100 * (0.35 * centrality + 0.3 * churn_score + 0.25 * cc_score + 0.1 * size_score)
        ranked.append({
            "file": f,
            "score": round(score, 1),
            "pagerank": round(pagerank.get(f, 0.0), 6),
            "imported_by": in_degree.get(f, 0),
            "commits": churn_by_file.get(f, 0),
            "complexity": cc_by_file.get(f, 0),
            "lines": stats["lines"],
        })

    ranked.sort(key=lambda x: x["score"], reverse=True)
    return [r for r in ranked[:top_n] if r["score"] > 0]
