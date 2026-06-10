"""Phase A features: identity, tree, ranking, sidecar, candidates, digest, AGENTS.md."""

import json
from pathlib import Path

import repo_scan


def test_detect_manifests_and_entry_points(tmp_repo: Path):
    (tmp_repo / "pyproject.toml").write_text(
        '[project]\nname = "x"\n\n[project.scripts]\nmycli = "x:main"\n'
    )
    assert "pyproject.toml" in repo_scan.detect_manifests(tmp_repo)
    entries = repo_scan.detect_entry_points(tmp_repo)
    assert any("mycli" in e for e in entries)
    assert any("main.py" in e for e in entries)


def test_readme_summary_skips_headings(tmp_repo: Path):
    (tmp_repo / "README.md").write_text(
        "# Title\n\nThis project does a specific useful thing for testing summaries nicely.\n"
    )
    summary = repo_scan.readme_summary(tmp_repo)
    assert summary.startswith("This project does")


def test_directory_tree_depth_and_excludes(tmp_repo: Path):
    (tmp_repo / "node_modules" / "junk").mkdir(parents=True)
    (tmp_repo / "src").mkdir()
    (tmp_repo / "src" / "x.py").write_text("pass\n")
    cfg = repo_scan.load_config(tmp_repo)
    tree = repo_scan.get_directory_tree(tmp_repo, cfg)
    assert "node_modules" not in tree
    assert "src/" in tree
    assert "x.py" in tree


def test_rank_files_orders_by_signals():
    line_counts = {"core.py": {"lines": 100, "bytes": 1}, "leaf.py": {"lines": 10, "bytes": 1}}
    churn = [{"file": "core.py", "commits": 9}]
    complexity = [{"file": "core.py", "name": "f", "rank": "C", "complexity": 12, "lineno": 1}]
    edges = [("leaf", "core")]
    ranking = repo_scan.rank_files(line_counts, churn, complexity, edges, top_n=5)
    assert ranking[0]["file"] == "core.py"
    assert ranking[0]["imported_by"] == 1
    assert "pagerank" in ranking[0]
    assert ranking[0]["pagerank"] > 0
    assert ranking[0]["score"] > ranking[-1]["score"] or len(ranking) == 1


# --- PageRank unit tests (per approved spec docs/specs/...-spec.md) ---------

from repo_scan.ranking import _build_file_adjacency, _pagerank


def _lc(*files):
    return {f: {"lines": 10, "bytes": 1} for f in files}


def test_pagerank_star_hub_beats_leaves():
    adjacency = {"a.py": ["hub.py"], "b.py": ["hub.py"], "c.py": ["hub.py"]}
    nodes = {"a.py", "b.py", "c.py", "hub.py"}
    pr = _pagerank(nodes, adjacency)
    assert pr["hub.py"] > pr["a.py"]
    assert abs(sum(pr.values()) - 1.0) < 1e-3  # mass conserved


def test_pagerank_chain_orders_transitively():
    # a -> b -> c -> d: equal direct in-degree for b/c/d, but PageRank
    # accumulates downstream — d above the intermediates.
    adjacency = {"a.py": ["b.py"], "b.py": ["c.py"], "c.py": ["d.py"]}
    nodes = {"a.py", "b.py", "c.py", "d.py"}
    pr = _pagerank(nodes, adjacency)
    assert pr["d.py"] > pr["c.py"] > pr["b.py"] > pr["a.py"]


def test_pagerank_empty_and_dangling():
    assert _pagerank(set(), {}) == {}
    # dangling node d has no out-edges; mass must still sum to 1
    pr = _pagerank({"a.py", "d.py"}, {"a.py": ["d.py"]})
    assert abs(sum(pr.values()) - 1.0) < 1e-3
    assert pr["d.py"] > pr["a.py"]


def test_pagerank_disconnected_components():
    # audit issue: claim about disconnected subgraphs must be tested.
    adjacency = {"a.py": ["b.py"], "x.py": ["y.py"]}
    nodes = {"a.py", "b.py", "x.py", "y.py"}
    pr = _pagerank(nodes, adjacency)
    assert all(pr[n] > 0 for n in nodes)          # nonzero within each component
    assert pr["b.py"] > pr["a.py"] and pr["y.py"] > pr["x.py"]


def test_adjacency_requires_both_endpoints_resolved():
    # audit issue: stricter than in-degree — unresolved src drops the edge.
    line_counts = _lc("core.py")
    adjacency = _build_file_adjacency([("ghost", "core"), ("core", "ghost")], line_counts)
    assert adjacency == {}


def test_rank_files_importer_only_gets_nonzero_centrality():
    # audit issue: files with outgoing edges but imported_by=0 now get a
    # nonzero structural term (was always 0 under pure in-degree).
    line_counts = _lc("app.py", "lib.py", "isolated.py")
    ranking = repo_scan.rank_files(line_counts, [], [], [("app", "lib")], top_n=5)
    by_file = {r["file"]: r for r in ranking}
    assert by_file["app.py"]["imported_by"] == 0
    assert by_file["app.py"]["pagerank"] > 0
    assert by_file["lib.py"]["pagerank"] > by_file["app.py"]["pagerank"]
    assert "isolated.py" not in by_file or by_file["isolated.py"]["pagerank"] == 0


def test_rank_files_edgeless_repo_zero_centrality():
    line_counts = _lc("a.py", "b.py")
    churn = [{"file": "a.py", "commits": 3}]
    ranking = repo_scan.rank_files(line_counts, churn, [], [], top_n=5)
    assert all(r["pagerank"] == 0 for r in ranking)
    assert ranking[0]["file"] == "a.py"  # churn still differentiates


def test_scan_writes_sidecar_json(tmp_repo_with_imports: Path):
    repo_scan.scan(tmp_repo_with_imports, quiet=True)
    sidecar = tmp_repo_with_imports / "docs" / "scan.json"
    assert sidecar.exists()
    data = json.loads(sidecar.read_text())
    assert data["schema_version"] == 1
    assert data["repo"]["name"] == "repo"
    assert ["app", "helpers"] in data["dependency_edges"]["python"]
    assert data["ranking"], "ranking should be non-empty"


def test_candidates_written_when_radar_enabled(tmp_repo: Path):
    (tmp_repo / ".repo-scan.json").write_text(json.dumps({"radar_enabled": True}))
    repo_scan.scan(tmp_repo, quiet=True)
    assert (tmp_repo / "docs" / "research" / "candidates.md").exists()


def test_candidates_not_written_by_default(tmp_repo: Path):
    repo_scan.scan(tmp_repo, quiet=True)
    assert not (tmp_repo / "docs" / "research" / "candidates.md").exists()


def test_digest_respects_budget(tmp_repo_with_imports: Path):
    cfg = repo_scan.load_config(tmp_repo_with_imports)
    cfg["digest_tokens"] = 100  # tiny budget forces truncation path
    languages = repo_scan.detect_languages(tmp_repo_with_imports, cfg)
    line_counts = repo_scan.get_line_counts(tmp_repo_with_imports, cfg)
    churn = repo_scan.get_git_churn(tmp_repo_with_imports, cfg)
    path = repo_scan.write_digest(tmp_repo_with_imports, cfg, line_counts, languages, churn, [], [], "tree")
    content = path.read_text()
    assert len(content) <= 100 * 4 + 60
    assert "repo digest" in content


def test_write_agents_md_never_overwrites(tmp_repo: Path):
    repo_scan.write_agents_md(tmp_repo)
    agents = tmp_repo / "AGENTS.md"
    assert agents.exists()
    agents.write_text("custom rules\n")
    repo_scan.write_agents_md(tmp_repo)
    assert agents.read_text() == "custom rules\n"


def test_ts_dep_edges_skip_reasons(tmp_repo: Path):
    edges, reason = repo_scan.get_ts_dep_edges(tmp_repo, [])
    assert edges == []
    assert reason == "no TS/JS files"


def test_index_has_ranking_and_structure(tmp_repo_with_imports: Path):
    repo_scan.scan(tmp_repo_with_imports, quiet=True)
    index = (tmp_repo_with_imports / "docs" / "index.md").read_text()
    assert "## Start here (ranked by importance)" in index
    assert "## Structure" in index
