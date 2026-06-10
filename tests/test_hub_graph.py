"""Hub knowledge graph API and vault/code layer builders."""

import json
import urllib.request

import pytest

pytest_plugins = ["tests.test_hub"]

from repo_scan.config import DEFAULT_CONFIG
from repo_scan.hub.graph import build_chain, build_graph
from repo_scan.hub.state import create_run, update_run


def test_build_graph_empty_without_scan(tmp_repo):
    g = build_graph(tmp_repo, DEFAULT_CONFIG)
    assert g["nodes"] == []
    assert g["edges"] == []
    assert len(g["pipeline"]) == 6
    assert g["stats"]["nodes"] == 0


def test_build_graph_code_layer_from_scan(tmp_repo):
    scan = {
        "generated_at": "2026-06-10 12:00 UTC",
        "files": {
            "repo_scan/a.py": {"lines": 10},
            "repo_scan/b.py": {"lines": 20},
        },
        "ranking": [
            {"file": "repo_scan/a.py", "score": 10, "pagerank": 0.1},
            {"file": "repo_scan/b.py", "score": 8, "pagerank": 0.05},
        ],
        "dependency_edges": {
            "python": [["repo_scan.a", "repo_scan.b"]],
            "typescript": [],
        },
    }
    docs = tmp_repo / "docs"
    docs.mkdir(parents=True, exist_ok=True)
    (docs / "scan.json").write_text(json.dumps(scan), encoding="utf-8")

    g = build_graph(tmp_repo, DEFAULT_CONFIG)
    assert g["stats"]["code_nodes"] == 2
    kinds = {n["kind"] for n in g["nodes"]}
    assert "code" in kinds
    assert any(e["kind"] == "imports" for e in g["edges"])


def test_build_graph_vault_provenance(tmp_repo):
    docs = tmp_repo / "docs"
    (docs / "tickets").mkdir(parents=True)
    (docs / "specs").mkdir(parents=True)
    (docs / "research" / "analysis").mkdir(parents=True)
    (docs / "scan.json").write_text("{}", encoding="utf-8")
    (docs / "tickets" / "tkt-0001.md").write_text(
        "---\ntitle: Fix seam\nstatus: in-progress\n---\n"
        "## Evidence\n[[seam-spec]]\n",
        encoding="utf-8",
    )
    (docs / "specs" / "seam-spec.md").write_text(
        "---\nstatus: approved\nanalysis: [[seam-analysis]]\n---\n",
        encoding="utf-8",
    )
    (docs / "research" / "analysis" / "seam-analysis.md").write_text(
        "# Analysis\n- [[sources/paper-1]]\n",
        encoding="utf-8",
    )

    g = build_graph(tmp_repo, DEFAULT_CONFIG)
    ids = {n["id"] for n in g["nodes"]}
    assert "ticket:tkt-0001" in ids
    assert "spec:seam-spec" in ids
    assert "analysis:seam-analysis" in ids
    assert any(e["source"] == "ticket:tkt-0001" and e["target"] == "spec:seam-spec"
               for e in g["edges"])


def test_build_graph_highlights_active_ticket(tmp_repo):
    docs = tmp_repo / "docs"
    docs.mkdir(parents=True, exist_ok=True)
    (docs / "scan.json").write_text("{}", encoding="utf-8")
    run = create_run(tmp_repo, DEFAULT_CONFIG, "problem?", ticket="tkt-0042")
    update_run(tmp_repo, DEFAULT_CONFIG, run["id"], "running")

    g = build_graph(tmp_repo, DEFAULT_CONFIG)
    assert "ticket:tkt-0042" in g["highlights"]
    assert f"run:{run['id']}" in g["highlights"]


def test_api_graph_endpoint(hub_server):
    root, cfg, token, base = hub_server
    docs = root / "docs"
    docs.mkdir(parents=True, exist_ok=True)
    (docs / "scan.json").write_text(
        json.dumps({"files": {}, "ranking": [], "dependency_edges": {"python": []}}),
        encoding="utf-8",
    )

    req = urllib.request.Request(
        f"{base}/api/graph",
        headers={"X-Radar-Token": token},
    )
    with urllib.request.urlopen(req, timeout=10) as resp:
        body = json.loads(resp.read().decode())
    assert "nodes" in body and "pipeline" in body
    assert "coverage" in body
    assert resp.status == 200


def test_graph_payload_includes_signal_matrix(tmp_repo):
    docs = tmp_repo / "docs"
    (docs / "specs").mkdir(parents=True)
    (docs / "scan.json").write_text(json.dumps({"files": {}, "citations": []}), encoding="utf-8")
    (docs / "specs" / "foo-spec.md").write_text("---\nstatus: draft\n---\n", encoding="utf-8")
    g = build_graph(tmp_repo, DEFAULT_CONFIG)
    matrix = g["coverage"]["signal_matrix"]
    assert "spec" in matrix
    assert "evidence" in matrix["spec"]


def test_graph_payload_includes_node_scores(tmp_repo):
    docs = tmp_repo / "docs"
    (docs / "specs").mkdir(parents=True)
    (docs / "scan.json").write_text(json.dumps({"files": {}, "citations": []}), encoding="utf-8")
    (docs / "specs" / "foo-spec.md").write_text(
        "---\nstatus: approved\nanalysis: [[foo-analysis]]\n---\n",
        encoding="utf-8",
    )
    (docs / "research" / "analysis").mkdir(parents=True, exist_ok=True)
    (docs / "research" / "analysis" / "foo-analysis.md").write_text(
        "- [[sources/s1]]\n", encoding="utf-8",
    )
    (docs / "research" / "sources").mkdir(parents=True, exist_ok=True)
    (docs / "research" / "sources" / "s1.md").write_text(
        "---\ntitle: S\n---\nbody\n", encoding="utf-8",
    )
    g = build_graph(tmp_repo, DEFAULT_CONFIG)
    spec = next(n for n in g["nodes"] if n["id"] == "spec:foo-spec")
    assert "score" in spec
    assert "missing" in spec
    assert g["coverage"]["docs"] >= 2


def test_vault_coverage_endpoint_returns_pct(hub_server):
    root, cfg, token, base = hub_server
    docs = root / "docs"
    (docs / "specs").mkdir(parents=True, exist_ok=True)
    (docs / "scan.json").write_text(
        json.dumps({"files": {}, "ranking": [], "citations": [], "vault_health": {}}),
        encoding="utf-8",
    )
    (docs / "specs" / "x-spec.md").write_text("---\nstatus: draft\n---\n", encoding="utf-8")
    req = urllib.request.Request(f"{base}/api/graph", headers={"X-Radar-Token": token})
    with urllib.request.urlopen(req, timeout=10) as resp:
        body = json.loads(resp.read().decode())
    assert "coverage_pct" in body["stats"] or "coverage" in body


def test_chain_walks_ticket_to_code(tmp_repo):
    docs = tmp_repo / "docs"
    (docs / "tickets").mkdir(parents=True)
    (docs / "specs").mkdir(parents=True)
    (docs / "research" / "sources").mkdir(parents=True)
    scan = {
        "files": {"repo_scan/g.py": {"lines": 5}},
        "citations": [],
        "dependency_edges": {"python": []},
        "ranking": [],
    }
    (docs / "scan.json").write_text(json.dumps(scan), encoding="utf-8")
    (docs / "tickets" / "tkt-0001.md").write_text(
        "---\ntitle: T\n---\n## Evidence\n[[loop-spec]]\n", encoding="utf-8",
    )
    (docs / "specs" / "loop-spec.md").write_text(
        "---\nanalysis: [[loop-analysis]]\n---\n", encoding="utf-8",
    )
    (docs / "research" / "analysis").mkdir(parents=True, exist_ok=True)
    (docs / "research" / "analysis" / "loop-analysis.md").write_text(
        "[[sources/src-1]]\n", encoding="utf-8",
    )
    (docs / "research" / "sources" / "src-1.md").write_text(
        "---\nlinked_files: [repo_scan/g.py]\n---\n", encoding="utf-8",
    )
    chain = build_chain(tmp_repo, DEFAULT_CONFIG, "ticket:tkt-0001")
    kinds = [r["kind"] for r in chain["chain"]]
    assert "ticket" in kinds
    assert "spec" in kinds


def test_chain_renders_with_missing_links(tmp_repo):
    docs = tmp_repo / "docs"
    docs.mkdir(parents=True, exist_ok=True)
    (docs / "scan.json").write_text("{}", encoding="utf-8")
    chain = build_chain(tmp_repo, DEFAULT_CONFIG, "missing:id")
    assert chain["chain"] == []


def test_chain_annotates_governance_risk(tmp_repo):
    docs = tmp_repo / "docs"
    (docs / "specs").mkdir(parents=True)
    (docs / "scan.json").write_text(
        json.dumps({"files": {}, "citations": [], "dependency_edges": {"python": []}, "ranking": []}),
        encoding="utf-8",
    )
    (docs / "specs" / "risky-spec.md").write_text(
        "---\nstatus: approved\n---\nNo evidence or links\n", encoding="utf-8",
    )
    chain = build_chain(tmp_repo, DEFAULT_CONFIG, "spec:risky-spec")
    risky = [r for r in chain["chain"] if r.get("governance_risk")]
    assert len(risky) >= 1
    assert risky[0]["id"] == "spec:risky-spec"


def test_api_graph_chain_endpoint(hub_server):
    root, cfg, token, base = hub_server
    docs = root / "docs"
    (docs / "scan.json").write_text("{}", encoding="utf-8")
    req = urllib.request.Request(
        f"{base}/api/graph/chain?id=ticket:missing",
        headers={"X-Radar-Token": token},
    )
    with urllib.request.urlopen(req, timeout=10) as resp:
        body = json.loads(resp.read().decode())
    assert body["root"] == "ticket:missing"
    assert "chain" in body
