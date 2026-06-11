"""Knowledge graph payload for the hub — code imports + vault provenance.

Vault: docs/tickets/tkt-0032
Vault: docs/research/sources/gh-cytoscape-cytoscape.js
Spec:  docs/specs/2026-06-10-move-the-agentic-loop-graph-and-untracke-spec
"""

from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

from ..citations import citation_index
from ..provenance import score_node, vault_coverage
from ..ranking import _module_to_file
from ..radar.sources import parse_frontmatter

_WIKILINK_RE = re.compile(r"\[\[([^\]|#]+)")
_MAX_CODE_NODES = 40
_MAX_CODE_EDGES = 80
_DEFAULT_MAX_GRAPH_NODES = 250

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


def _truncate_graph(nodes: list[dict], edges: list[dict],
                    cap: int) -> tuple[list[dict], list[dict]]:
    """Drop lowest-priority nodes when the graph exceeds *cap*.

    Priority ranking (higher = kept first):
    - Nodes with edges (connected) beat nodes without (orphans)
    - Among connected nodes: higher edge degree wins
    - Core vault kinds (ticket, spec, analysis, source) beat ancillary
      kinds (report, doc, gate) at equal degree
    - Code nodes that are linked/cited survive; unconnected code drops first

    After node removal, dangling edges are cleaned up.
    """
    if len(nodes) <= cap:
        return nodes, edges

    degree: dict[str, int] = {}
    for e in edges:
        degree[e["source"]] = degree.get(e["source"], 0) + 1
        degree[e["target"]] = degree.get(e["target"], 0) + 1

    _CORE_KINDS = frozenset({"ticket", "spec", "analysis", "source"})

    def priority(n: dict) -> tuple:
        kind = n.get("kind", "")
        deg = degree.get(n["id"], 0)
        is_core = kind in _CORE_KINDS
        is_code = kind == "code"
        return (
            1 if deg > 0 else 0,       # connected beats orphan
            0 if is_code and deg == 0 else 1,  # unlinked code drops first
            1 if is_core else 0,        # core vault kinds preferred
            deg,                        # higher degree wins
        )

    ranked = sorted(nodes, key=priority, reverse=True)
    kept_nodes = ranked[:cap]
    kept_ids = {n["id"] for n in kept_nodes}
    kept_edges = [e for e in edges
                  if e["source"] in kept_ids and e["target"] in kept_ids]
    return kept_nodes, kept_edges


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


def _dir_coverage(nodes: list[dict], coverage: dict) -> list[dict]:
    """Group code nodes by top-level directory; report tracked vs total."""
    untracked = set(coverage.get("untracked_code") or [])
    buckets: dict[str, dict] = {}
    for n in nodes:
        if n.get("kind") != "code":
            continue
        path = n.get("id", "").split(":", 1)[-1] if ":" in n.get("id", "") else ""
        parts = path.split("/")
        key = "/".join(parts[:2]) if len(parts) > 2 else parts[0] if parts else ""
        if not key:
            continue
        b = buckets.setdefault(key, {"dir": key, "total": 0, "tracked": 0, "untracked": 0})
        b["total"] += 1
        if path in untracked:
            b["untracked"] += 1
        else:
            b["tracked"] += 1
    rows = sorted(buckets.values(), key=lambda r: r["total"], reverse=True)
    return rows[:15]


def _stale_queue(nodes: list[dict]) -> list[dict]:
    """Vault docs with stale_days > 0, sorted by staleness."""
    stale = []
    for n in nodes:
        if n.get("kind") == "code":
            continue
        days = n.get("stale_days")
        if days and days > 0:
            stale.append({
                "id": n["id"], "label": n.get("label", ""),
                "kind": n.get("kind", ""), "doc": n.get("doc", ""),
                "stale_days": days, "score": n.get("score", 0),
                "missing": n.get("missing", []),
            })
    stale.sort(key=lambda r: r["stale_days"], reverse=True)
    return stale[:15]


def _citation_density(nodes: list[dict], edges: list[dict]) -> list[dict]:
    """Per code-node count of inbound 'cites' edges, sorted by importance."""
    cite_count: dict[str, int] = {}
    for e in edges:
        if e.get("kind") == "cites":
            tgt = e["target"]
            cite_count[tgt] = cite_count.get(tgt, 0) + 1
            src = e["source"]
            cite_count[src] = cite_count.get(src, 0) + 1
    rows = []
    for n in nodes:
        if n.get("kind") != "code":
            continue
        nid = n["id"]
        path = nid.split(":", 1)[-1] if ":" in nid else n.get("label", "")
        rows.append({
            "file": path, "label": n.get("label", ""),
            "citations": cite_count.get(nid, 0),
            "score": n.get("score", 0),
        })
    rows.sort(key=lambda r: (-r.get("score", 0), -r["citations"]))
    return rows[:20]


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
    all_nodes = list(node_map.values())
    all_edges = code_edges + vault_edges + cite_edges
    cap = int(cfg.get("graph_max_nodes", _DEFAULT_MAX_GRAPH_NODES))
    nodes, edges = _truncate_graph(all_nodes, all_edges, cap)
    _attach_scores(nodes, root, cfg, scan)
    coverage = vault_coverage(root, cfg, scan, scan.get("citations") or [])
    approved_unhealthy = [
        n for n in nodes
        if n.get("kind") == "spec" and n.get("status") == "approved"
        and (n.get("score", 0)) < 3
    ]
    coverage["approved_unhealthy"] = len(approved_unhealthy)
    coverage["approved_unhealthy_list"] = [
        {"id": n["id"], "label": n.get("label", ""),
         "score": n.get("score", 0), "missing": n.get("missing", []),
         "doc": n.get("doc", "")}
        for n in approved_unhealthy[:10]
    ]
    coverage["signal_matrix"] = _signal_matrix(nodes)
    coverage["untracked_ranked"] = _untracked_ranked(
        scan, coverage.get("untracked_code") or [],
    )
    coverage["dir_coverage"] = _dir_coverage(nodes, coverage)
    coverage["stale_queue"] = _stale_queue(nodes)
    coverage["citation_density"] = _citation_density(nodes, edges)
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


def change_impact(root: Path, cfg: dict) -> dict:
    """Recently changed files → vault docs whose linked_files point at them."""
    try:
        result = subprocess.run(
            ["git", "diff", "--name-only", "HEAD~5..HEAD"],
            capture_output=True, text=True, cwd=root, timeout=5,
        )
        changed = [l.strip() for l in result.stdout.splitlines() if l.strip()]
    except (subprocess.TimeoutExpired, FileNotFoundError):
        changed = []
    if not changed:
        return {"changed": [], "affected_docs": []}

    changed_set = set(changed)
    docs = root / cfg["docs_dir"]
    affected: list[dict] = []
    for sub, kind in (("tickets", "ticket"), ("specs", "spec"),
                      ("research/sources", "source"), ("research/analysis", "analysis")):
        base = docs / sub
        if not base.is_dir():
            continue
        for path in sorted(base.glob("*.md")):
            text = path.read_text(encoding="utf-8", errors="ignore")
            fm = parse_frontmatter(text)
            linked_raw = str(fm.get("linked_files", "") or "")
            if not linked_raw:
                continue
            linked = [p.strip().strip("[]\"'") for p in linked_raw.replace("[", "").replace("]", "").split(",")]
            hits = [p for p in linked if p in changed_set]
            if hits:
                affected.append({
                    "doc": str(path.relative_to(docs)),
                    "kind": kind,
                    "label": str(fm.get("title") or path.stem)[:48],
                    "linked_changed": hits,
                })
    return {"changed": changed[:20], "affected_docs": affected[:15]}
