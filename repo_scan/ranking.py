"""Important-files ranking from signals the scan already collects."""


def _module_to_file(module: str, line_counts: dict) -> str | None:
    """Map a dotted module or relative path back to a counted file path."""
    if module in line_counts:
        return module
    candidate = module.replace(".", "/")
    for suffix in [".py", "/__init__.py"]:
        if candidate + suffix in line_counts:
            return candidate + suffix
    return None


def rank_files(line_counts: dict, churn: list, complexity: list,
               dep_edges: list[tuple[str, str]], top_n: int = 15,
               exclude_prefix: str = "docs/") -> list[dict]:
    """Composite importance score: import centrality x churn x complexity.

    Heuristic stand-in for aider-style PageRank — uses signals the scan
    already collects, keeping the zero-dependency rule. Generated docs are
    excluded so the scan output never ranks itself.
    """
    line_counts = {f: s for f, s in line_counts.items() if not f.startswith(exclude_prefix)}
    if not line_counts:
        return []

    in_degree: dict[str, int] = {}
    for _, dst in dep_edges:
        f = _module_to_file(dst, line_counts)
        if f:
            in_degree[f] = in_degree.get(f, 0) + 1

    churn_by_file = {c["file"]: c["commits"] for c in churn}
    cc_by_file: dict[str, int] = {}
    for item in complexity:
        cc_by_file[item["file"]] = cc_by_file.get(item["file"], 0) + item["complexity"]

    max_deg = max(in_degree.values(), default=0) or 1
    max_churn = max(churn_by_file.values(), default=0) or 1
    max_cc = max(cc_by_file.values(), default=0) or 1
    max_lines = max((s["lines"] for s in line_counts.values()), default=0) or 1

    ranked = []
    for f, stats in line_counts.items():
        centrality = in_degree.get(f, 0) / max_deg
        churn_score = churn_by_file.get(f, 0) / max_churn
        cc_score = cc_by_file.get(f, 0) / max_cc
        size_score = stats["lines"] / max_lines
        score = 100 * (0.35 * centrality + 0.3 * churn_score + 0.25 * cc_score + 0.1 * size_score)
        ranked.append({
            "file": f,
            "score": round(score, 1),
            "imported_by": in_degree.get(f, 0),
            "commits": churn_by_file.get(f, 0),
            "complexity": cc_by_file.get(f, 0),
            "lines": stats["lines"],
        })

    ranked.sort(key=lambda x: x["score"], reverse=True)
    return [r for r in ranked[:top_n] if r["score"] > 0]
