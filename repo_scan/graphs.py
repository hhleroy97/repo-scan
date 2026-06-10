"""Dependency and call graph generation (Mermaid output).

Coupling subgraph builders normalize paths with ``behavior._norm_node`` and
resolve import edges via ``ranking._module_to_file`` — the same rules as
``hidden_seams``. ``linkStyle`` indices are assigned after pairs are sorted

Vault: docs/tickets/tkt-0003
Spec:  docs/specs/2026-06-10-refactor-repo-scan-graphs-py-cc-56-3-com-spec
and capped so they stay aligned with rendered edges.
"""

import json
from pathlib import Path

from .behavior import _norm_node
from .ranking import _module_to_file
from .utils import chart_label, run, tool_available


def _node_id(name: str) -> str:
    return name.replace(".", "_").replace("/", "_").replace("-", "_")


def _seam_key(a: str, b: str) -> frozenset[str]:
    return frozenset((_norm_node(a), _norm_node(b)))


def _seam_keys(seams: list[dict]) -> set[frozenset[str]]:
    return {_seam_key(s["a"], s["b"]) for s in seams}


def _resolved_file_edges(import_edges: list[tuple[str, str]],
                         line_counts: dict) -> list[tuple[str, str]]:
    """Map module/path import edges to repo-relative file paths."""
    resolved: list[tuple[str, str]] = []
    for src, dst in import_edges:
        src_f = _module_to_file(src, line_counts)
        dst_f = _module_to_file(dst, line_counts)
        if src_f and dst_f and src_f != dst_f:
            resolved.append((src_f, dst_f))
    return resolved


def _one_hop_import_edges(files: set[str], file_edges: list[tuple[str, str]],
                          *, max_edges: int) -> list[tuple[str, str]]:
    """Import edges touching any file in ``files`` (1-hop around the set)."""
    targets = {_norm_node(f) for f in files}
    seen: set[tuple[str, str]] = set()
    out: list[tuple[str, str]] = []
    for src, dst in file_edges:
        if _norm_node(src) in targets or _norm_node(dst) in targets:
            key = (src, dst)
            if key not in seen:
                seen.add(key)
                out.append(key)
                if len(out) >= max_edges:
                    break
    return out


def coupling_to_mermaid(coupling: list[dict], seams: list[dict],
                        import_edges: list[tuple[str, str]], line_counts: dict,
                        *, max_edges: int) -> str | None:
    """Top-N change-coupling pairs as ``graph TD``.

    Seam pairs (no import edge) get dashed red ``linkStyle``; import-backed
    pairs use solid gray. Node IDs from ``_node_id``; labels from ``chart_label``.
    """
    pairs = coupling[:max_edges]
    if not pairs:
        return None
    seam_set = _seam_keys(seams)
    nodes = sorted({n for c in pairs for n in (c["a"], c["b"])})
    lines = ["graph TD"]
    for n in nodes:
        lines.append(f'  {_node_id(n)}["{chart_label(n)}"]')
    for c in pairs:
        na, nb = _node_id(c["a"]), _node_id(c["b"])
        lines.append(f"  {na} --> {nb}")
    for i, c in enumerate(pairs):
        if _seam_key(c["a"], c["b"]) in seam_set:
            lines.append(f"linkStyle {i} stroke:#c0392b,stroke-width:2px,stroke-dasharray: 5 5")
        else:
            lines.append(f"linkStyle {i} stroke:#95a5a6,stroke-width:1px")
    return "\n".join(lines)


def seam_pair_mermaid(a: str, b: str, degree: int,
                      import_edges: list[tuple[str, str]], line_counts: dict,
                      *, max_import_edges: int = 8) -> str | None:
    """Two-node coupling subgraph for a hidden seam ticket.

    The coupling edge is styled as a seam; optional 1-hop import edges from
    resolved ``py_edges``/``ts_edges`` are drawn in gray (capped).
    """
    file_edges = _resolved_file_edges(import_edges, line_counts)
    hop = _one_hop_import_edges({a, b}, file_edges, max_edges=max_import_edges)
    lines = [
        "graph TD",
        f'  {_node_id(a)}["{chart_label(a)}"]',
        f'  {_node_id(b)}["{chart_label(b)}"]',
        f"  {_node_id(a)} -->|{degree}% coupled| {_node_id(b)}",
    ]
    edge_idx = 0
    lines.append(f"linkStyle {edge_idx} stroke:#c0392b,stroke-width:2px,stroke-dasharray: 5 5")
    for src, dst in hop:
        edge_idx += 1
        lines.append(f"  {_node_id(src)} --> {_node_id(dst)}")
        lines.append(f"linkStyle {edge_idx} stroke:#95a5a6,stroke-width:1px")
    return "\n".join(lines)


def refactor_ego_mermaid(file: str, coupling: list[dict], ranking: list[dict],
                         *, max_neighbors: int) -> str | None:
    """Ego subgraph for a refactor ticket: focal file plus top coupled neighbors."""
    neighbors: list[tuple[str, int]] = []
    for c in coupling:
        if c["a"] == file:
            neighbors.append((c["b"], c["degree"]))
        elif c["b"] == file:
            neighbors.append((c["a"], c["degree"]))
    neighbors.sort(key=lambda x: (-x[1], x[0]))
    picked = neighbors[:max_neighbors]
    if not picked and file not in {r["file"] for r in ranking}:
        return None
    nodes = [file] + [n for n, _ in picked]
    lines = [
        "graph TD",
        "  classDef focal fill:#3498db,stroke:#2980b9,color:#fff",
    ]
    for n in nodes:
        lines.append(f'  {_node_id(n)}["{chart_label(n)}"]')
    for i, (neighbor, deg) in enumerate(picked):
        lines.append(f"  {_node_id(file)} -->|{deg}%| {_node_id(neighbor)}")
        lines.append(f"linkStyle {i} stroke:#95a5a6,stroke-width:1px")
    lines.append(f"  class {_node_id(file)} focal")
    return "\n".join(lines)


def edges_to_mermaid(edges: list[tuple[str, str]],
                     scores: dict[str, float] | None = None) -> str | None:
    """Render (src_module, dst_module) edges as a Mermaid graph.

    With `scores` (node name → PageRank), nodes are tinted by importance tier
    so the hubs are visible in the diagram itself: hot (≥60% of max), warm
    (≥25%), cold (rest)."""
    if not edges:
        return None
    seen = set()
    nodes: set[str] = set()
    lines = ["graph TD"]
    for s, t in edges:
        if (s, t) not in seen:
            seen.add((s, t))
            nodes.update((s, t))
            sl, tl = _node_id(s), _node_id(t)
            lines.append(f'  {sl}["{s.split(".")[-1].split("/")[-1]}"] --> {tl}["{t.split(".")[-1].split("/")[-1]}"]')
    if len(lines) <= 1:
        return None

    if scores:
        max_score = max((scores.get(n, 0.0) for n in nodes), default=0.0)
        if max_score > 0:
            tiers: dict[str, list[str]] = {"hot": [], "warm": [], "cold": []}
            for n in sorted(nodes):
                ratio = scores.get(n, 0.0) / max_score
                tier = "hot" if ratio >= 0.6 else ("warm" if ratio >= 0.25 else "cold")
                tiers[tier].append(_node_id(n))
            lines += [
                "  classDef hot fill:#e74c3c,stroke:#922b21,color:#fff",
                "  classDef warm fill:#f5b041,stroke:#b9770e,color:#1a1a1a",
                "  classDef cold fill:#d6dbdf,stroke:#85929e,color:#1a1a1a",
            ]
            for tier, ids in tiers.items():
                if ids:
                    lines.append(f"  class {','.join(ids)} {tier}")
    return "\n".join(lines)


def get_ts_dep_edges(root: Path, ts_files: list[Path]) -> tuple[list[tuple[str, str]], str]:
    """TS/JS dependency edges via `madge --json` (madge >= 6 has no --mermaid).

    Returns (edges_as_relative_paths, skip_reason). Reason is "" on success.
    """
    if not ts_files:
        return [], "no TS/JS files"
    if not tool_available("madge"):
        return [], "madge not installed — npm install -g madge"
    src_candidates = ["src", "app", "lib", "."]
    src_dir = next((root / d for d in src_candidates if (root / d).is_dir()), root)
    # without --extensions, madge silently returns {} for .tsx/.jsx projects
    out, _, code = run(["madge", "--json", "--extensions", "ts,tsx,js,jsx", str(src_dir)],
                       cwd=root)
    if code != 0 or not out.strip():
        return [], "madge produced no output"
    try:
        graph = json.loads(out)
    except json.JSONDecodeError:
        return [], "madge output was not valid JSON"
    # madge paths are relative to src_dir; re-anchor to repo root so they
    # match line_counts/ranking keys (otherwise PageRank silently sees no graph)
    prefix = src_dir.relative_to(root).as_posix()
    prefix = "" if prefix == "." else prefix + "/"
    edges = [(prefix + src, prefix + dst) for src, deps in graph.items() for dst in deps]
    return edges, "" if edges else "no imports between files detected"


def _resolve_python_import(src_mod: str, from_init: bool, spec: str) -> str:
    """Resolve a ``from``/``import`` target to a dotted module name.

  Relative specs (leading dots) are anchored on the source file's package:
  ``from .writers`` in ``repo_scan.scanner`` → ``repo_scan.writers``;
  ``from ..pkg`` walks up one package level. Absolute specs pass through."""
    if not spec.startswith("."):
        return spec
    level = len(spec) - len(spec.lstrip("."))
    rest = spec[level:]
    parts = src_mod.split(".")
    pkg_parts = parts if from_init else parts[:-1]
    up = level - 1
    if up > len(pkg_parts):
        return ""
    base = pkg_parts[: len(pkg_parts) - up] if up else pkg_parts
    if rest:
        return ".".join(base + rest.split("."))
    return ".".join(base) if base else ""


def _match_repo_module(imported: str, repo_modules: set[str]) -> str | None:
    """Return the longest repo module matching an absolute or resolved import."""
    if imported in repo_modules:
        return imported
    for mod in repo_modules:
        if mod.startswith(imported + "."):
            return mod
    return None


def get_python_dep_edges(root: Path, py_files: list[Path], cfg: dict) -> list[tuple[str, str]]:
    """Intra-repo Python import edges as (src_module, dst_module) pairs.

    Relative imports (``from .writers``, ``from ..pkg``) resolve against the
    source file's package so dotted targets like ``repo_scan.writers`` match
    ``repo_modules`` built from repo-relative paths."""
    if not py_files:
        return []
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
            from_init = parts[-1] == "__init__.py"
            if not from_init:
                parts[-1] = parts[-1][:-3]
            src_mod = ".".join(parts)
        except ValueError:
            continue
        for line in src.splitlines():
            line = line.strip()
            imported: str | None = None
            if line.startswith("from ") and " import " in line:
                spec = line.split()[1]
                imported = _resolve_python_import(src_mod, from_init, spec)
            elif line.startswith("import "):
                imported = line.split()[1].split(",")[0].split(".")[0]
            if imported:
                target = _match_repo_module(imported, repo_modules)
                if target:
                    edges.append((src_mod, target))
    return edges


def get_python_dep_graph_mermaid(root: Path, py_files: list[Path], cfg: dict) -> str | None:
    return edges_to_mermaid(get_python_dep_edges(root, py_files, cfg))


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
