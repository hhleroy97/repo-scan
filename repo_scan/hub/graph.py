"""Knowledge graph payload for the hub — code imports + vault provenance."""

from __future__ import annotations

import json
import re
from pathlib import Path

from ..citations import citation_index
from ..provenance import score_node, vault_coverage
from ..ranking import _module_to_file
from ..radar.sources import parse_frontmatter

_WIKILINK_RE = re.compile(r"\[\[([^\]|#]+)")
_MAX_CODE_NODES = 40
_MAX_CODE_EDGES = 80
_MAX_VAULT_NODES = 60

_PIPELINE = [
    {"id": "scan", "label": "repo-scan"},
    {"id": "ticket", "label": "tickets"},
    {"id": "loop", "label": "RADAR loop"},
    {"id": "spec", "label": "approved spec"},
    {"id": "act", "label": "radar act"},
    {"id": "merge", "label": "PR merge"},
]


def _read_scan(root: Path, cfg: dict) -> dict:
    path = root / cfg["docs_dir"] / "scan.json"
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def _vault_ref(stem: str) -> tuple[str, str, str | None] | None:
    """Map wikilink stem to (kind, key, doc path relative to docs/)."""
    stem = stem.strip()
    if not stem or stem.startswith("."):
        return None
    if stem.startswith("tkt-"):
        return "ticket", stem, f"tickets/{stem}.md"
    if stem.endswith("-spec"):
        return "spec", stem, f"specs/{stem}.md"
    if stem.startswith("research/sources/"):
        name = stem.split("/")[-1]
        return "source", name, f"research/sources/{name}.md"
    if stem.startswith("sources/"):
        name = stem.split("/")[-1]
        return "source", name, f"research/sources/{name}.md"
    if stem.startswith("research/analysis/"):
        name = stem.split("/")[-1]
        return "analysis", name, f"research/analysis/{name}.md"
    if stem.startswith("reports/"):
        return "report", stem, f"{stem}.md"
    if "/" in stem:
        return "doc", stem, f"{stem}.md"
    return None


def _nid(kind: str, key: str) -> str:
    return f"{kind}:{key}"


def _add_node(nodes: dict, kind: str, key: str, *, label: str | None = None,
              doc: str | None = None, extra: dict | None = None) -> str:
    node_id = _nid(kind, key)
    if node_id not in nodes:
        row = {"id": node_id, "kind": kind, "label": label or key, "doc": doc}
        if extra:
            row.update(extra)
        nodes[node_id] = row
    return node_id


def _code_layer(scan: dict) -> tuple[list[dict], list[dict]]:
    files = scan.get("files") or {}
    if not files:
        return [], []
    ranking = scan.get("ranking") or []
    focus = {r["file"] for r in ranking[:_MAX_CODE_NODES]}
    rank_by = {r["file"]: r for r in ranking}
    nodes: dict[str, dict] = {}
    edges: list[dict] = []
    seen: set[tuple[str, str]] = set()
    for src, dst in scan.get("dependency_edges", {}).get("python", []):
        sf = _module_to_file(src, files)
        df = _module_to_file(dst, files)
        if not sf or not df or sf == df:
            continue
        if sf not in focus and df not in focus:
            continue
        key = (sf, df)
        if key in seen:
            continue
        seen.add(key)
        for path in (sf, df):
            short = path.rsplit("/", 1)[-1]
            extra = {}
            if path in rank_by:
                extra["score"] = rank_by[path].get("score")
            _add_node(nodes, "code", path, label=short, doc=None, extra=extra)
        edges.append({
            "source": _nid("code", sf),
            "target": _nid("code", df),
            "kind": "imports",
        })
        if len(edges) >= _MAX_CODE_EDGES:
            break
    return list(nodes.values()), edges


def _link_wikilinks(nodes: dict, edges: list[dict], from_id: str, text: str,
                    rel: str, *, edge_seen: set[tuple[str, str, str]]):
    for stem in _WIKILINK_RE.findall(text):
        ref = _vault_ref(stem)
        if not ref:
            continue
        kind, key, doc = ref
        to_id = _add_node(nodes, kind, key, doc=doc)
        sig = (from_id, to_id, rel)
        if sig in edge_seen:
            continue
        edge_seen.add(sig)
        edges.append({"source": from_id, "target": to_id, "kind": rel})


def _vault_layer(root: Path, cfg: dict) -> tuple[list[dict], list[dict]]:
    docs = root / cfg["docs_dir"]
    nodes: dict[str, dict] = {}
    edges: list[dict] = []
    edge_seen: set[tuple[str, str, str]] = set()

    tickets_dir = docs / "tickets"
    if tickets_dir.is_dir():
        for path in sorted(tickets_dir.glob("tkt-*.md")):
            text = path.read_text(encoding="utf-8", errors="ignore")
            fm = parse_frontmatter(text)
            tid = path.stem
            from_id = _add_node(
                nodes, "ticket", tid,
                label=str(fm.get("title") or tid)[:48],
                doc=f"tickets/{tid}.md",
                extra={"status": fm.get("status")},
            )
            _link_wikilinks(nodes, edges, from_id, text, "evidence", edge_seen=edge_seen)

    specs_dir = docs / "specs"
    if specs_dir.is_dir():
        for path in sorted(specs_dir.glob("*.md")):
            text = path.read_text(encoding="utf-8", errors="ignore")
            fm = parse_frontmatter(text)
            key = path.stem
            from_id = _add_node(
                nodes, "spec", key,
                label=key.replace("-", " ")[:48],
                doc=f"specs/{key}.md",
                extra={"status": fm.get("status")},
            )
            analysis = fm.get("analysis", "")
            if analysis:
                _link_wikilinks(nodes, edges, from_id, analysis, "provenance", edge_seen=edge_seen)
            _link_wikilinks(nodes, edges, from_id, text, "references", edge_seen=edge_seen)

    analysis_dir = docs / "research" / "analysis"
    if analysis_dir.is_dir():
        for path in sorted(analysis_dir.glob("*.md")):
            text = path.read_text(encoding="utf-8", errors="ignore")
            key = path.stem
            from_id = _add_node(
                nodes, "analysis", key,
                label=key.replace("-", " ")[:48],
                doc=f"research/analysis/{key}.md",
            )
            _link_wikilinks(nodes, edges, from_id, text, "evidence", edge_seen=edge_seen)

    sources_dir = docs / "research" / "sources"
    if sources_dir.is_dir():
        for path in sorted(sources_dir.glob("*.md")):
            text = path.read_text(encoding="utf-8", errors="ignore")
            fm = parse_frontmatter(text)
            key = path.stem
            from_id = _add_node(
                nodes, "source", key,
                label=str(fm.get("title") or key)[:48],
                doc=f"research/sources/{key}.md",
            )
            for linked in str(fm.get("linked_files", "")).split(","):
                linked = linked.strip().strip("[]\"'")
                if linked:
                    _add_node(nodes, "code", linked, label=linked.rsplit("/", 1)[-1])
                    edges.append({
                        "source": from_id,
                        "target": _nid("code", linked),
                        "kind": "linked_file",
                    })

    if len(nodes) > _MAX_VAULT_NODES:
        keep = set(list(nodes.keys())[:_MAX_VAULT_NODES])
        nodes = {k: v for k, v in nodes.items() if k in keep}
        edges = [e for e in edges if e["source"] in keep and e["target"] in keep]
    return list(nodes.values()), edges


def _live_highlights(root: Path, cfg: dict) -> list[str]:
    from ..tickets import load_tickets
    from .state import active_runs

    out: list[str] = []
    for run in active_runs(root, cfg):
        if run.get("ticket"):
            out.append(_nid("ticket", run["ticket"]))
        if run.get("id"):
            out.append(_nid("run", run["id"]))
    for t in load_tickets(root, cfg):
        if t.get("status") in ("proposed", "approved", "in-progress"):
            out.append(_nid("ticket", t["id"]))
    pending = root / cfg["docs_dir"] / "research" / "pending"
    if pending.is_dir():
        for path in pending.glob("*.json"):
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                continue
            problem = str(data.get("payload", {}).get("problem", ""))
            if problem:
                out.append(_nid("gate", data.get("gate", path.stem)))
    return sorted(set(out))


def _citation_edges(scan: dict, nodes: dict) -> list[dict]:
    edges: list[dict] = []
    seen: set[tuple[str, str]] = set()
    for row in scan.get("citations") or []:
        src = _nid("code", row["file"])
        tgt = _nid(row["target_kind"], row["target_id"])
        _add_node(nodes, "code", row["file"], label=row["file"].rsplit("/", 1)[-1])
        key = (src, tgt)
        if key in seen:
            continue
        seen.add(key)
        edges.append({"source": src, "target": tgt, "kind": "cites"})
    return edges


_VAULT_SIGNALS = ("evidence", "linked", "cited", "fresh")
_VAULT_KINDS = ("ticket", "spec", "analysis", "source")


def _signal_matrix(nodes: list[dict]) -> dict:
    """Per-kind pass rate for each provenance signal (hub dashboard matrix)."""
    matrix = {
        kind: {sig: {"pass": 0, "total": 0} for sig in _VAULT_SIGNALS}
        for kind in _VAULT_KINDS
    }
    for node in nodes:
        kind = node.get("kind")
        if kind not in matrix:
            continue
        signals = set(node.get("signals") or [])
        for sig in _VAULT_SIGNALS:
            matrix[kind][sig]["total"] += 1
            if sig in signals:
                matrix[kind][sig]["pass"] += 1
    return matrix


def _untracked_ranked(scan: dict, paths: list[str]) -> list[dict]:
    rank_by = {r["file"]: r for r in scan.get("ranking") or []}
    rows = [
        {"file": path, "score": round(rank_by[path].get("score", 0), 1)}
        for path in paths if path in rank_by
    ]
    rows.sort(key=lambda r: r["score"], reverse=True)
    extra = [
        {"file": path, "score": 0}
        for path in paths if path not in rank_by
    ]
    return (rows + extra)[:15]


def _attach_scores(nodes: list[dict], root: Path, cfg: dict, scan: dict) -> None:
    cite_idx = citation_index(scan.get("citations") or [])
    for node in nodes:
        if node.get("kind") == "code":
            continue
        node.update(score_node(node, root, cfg, scan, cite_idx))


_REL_OUT = {
    "ticket": frozenset({"evidence"}),
    "spec": frozenset({"provenance", "references"}),
    "analysis": frozenset({"evidence"}),
    "source": frozenset({"linked_file"}),
}


def build_chain(root: Path, cfg: dict, node_id: str) -> dict:
    """Walk provenance edges from a node for the hub chain panel."""
    graph = build_graph(root, cfg)
    nodes_by_id = {n["id"]: n for n in graph["nodes"]}
    if node_id not in nodes_by_id:
        return {"root": node_id, "chain": []}

    chain: list[dict] = []
    seen: set[str] = set()

    def append(nid: str, depth: int) -> None:
        if nid in seen:
            return
        seen.add(nid)
        node = nodes_by_id.get(nid)
        if not node:
            return
        chain.append({**node, "depth": depth})

    append(node_id, 0)
    queue = [(node_id, 0)]
    while queue:
        cur, depth = queue.pop(0)
        src_kind = cur.split(":", 1)[0]
        allowed = _REL_OUT.get(src_kind, frozenset())
        for edge in graph["edges"]:
            if edge["source"] != cur or edge["kind"] not in allowed:
                continue
            tgt = edge["target"]
            if tgt in seen:
                continue
            append(tgt, depth + 1)
            queue.append((tgt, depth + 1))

    for entry in chain:
        if (
            entry.get("kind") == "spec"
            and entry.get("status") == "approved"
            and entry.get("score", 0) < 3
        ):
            entry["governance_risk"] = True

    return {"root": node_id, "chain": chain}


def build_graph(root: Path, cfg: dict) -> dict:
    """Nodes/edges for the hub graph tab plus pipeline steps and live highlights."""
    scan = _read_scan(root, cfg)
    code_nodes, code_edges = _code_layer(scan)
    vault_nodes, vault_edges = _vault_layer(root, cfg)
    node_map: dict[str, dict] = {}
    for n in code_nodes + vault_nodes:
        node_map[n["id"]] = n
    cite_edges = _citation_edges(scan, node_map)
    nodes = list(node_map.values())
    edges = code_edges + vault_edges + cite_edges
    _attach_scores(nodes, root, cfg, scan)
    coverage = vault_coverage(root, cfg, scan, scan.get("citations") or [])
    approved_unhealthy = [
        n for n in nodes
        if n.get("kind") == "spec" and n.get("status") == "approved"
        and (n.get("score", 0)) < 3
    ]
    coverage["approved_unhealthy"] = len(approved_unhealthy)
    coverage["approved_unhealthy_list"] = [
        {"id": n["id"], "label": n.get("label", "")}
        for n in approved_unhealthy[:10]
    ]
    coverage["signal_matrix"] = _signal_matrix(nodes)
    coverage["untracked_ranked"] = _untracked_ranked(
        scan, coverage.get("untracked_code") or [],
    )
    return {
        "generated_at": scan.get("generated_at"),
        "pipeline": _PIPELINE,
        "nodes": nodes,
        "edges": edges,
        "highlights": _live_highlights(root, cfg),
        "coverage": coverage,
        "stats": {
            "nodes": len(nodes),
            "edges": len(edges),
            "code_nodes": sum(1 for n in nodes if n["kind"] == "code"),
            "vault_nodes": sum(1 for n in nodes if n["kind"] != "code"),
            "healthy": coverage.get("healthy", 0),
            "coverage_pct": coverage.get("coverage_pct", 0),
        },
    }
