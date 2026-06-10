"""Vault provenance scoring and coverage."""

import json
from pathlib import Path

from repo_scan.config import DEFAULT_CONFIG
from repo_scan.provenance import score_node, thin_citations, vault_coverage


def _setup_chain(tmp_repo: Path):
    docs = tmp_repo / "docs"
    (docs / "tickets").mkdir(parents=True)
    (docs / "specs").mkdir(parents=True)
    (docs / "research" / "analysis").mkdir(parents=True)
    (docs / "research" / "sources").mkdir(parents=True)
    (docs / "tickets" / "tkt-0001.md").write_text(
        "---\ntitle: Fix\nstatus: in-progress\n---\n## Evidence\n[[seam-spec]]\n",
        encoding="utf-8",
    )
    (docs / "specs" / "seam-spec.md").write_text(
        "---\nstatus: approved\nanalysis: [[seam-analysis]]\nlinked_files: [repo_scan/mod.py]\n---\n",
        encoding="utf-8",
    )
    (docs / "research" / "analysis" / "seam-analysis.md").write_text(
        "# A\n- [[sources/paper-1]]\n",
        encoding="utf-8",
    )
    (docs / "research" / "sources" / "paper-1.md").write_text(
        "---\ntitle: Paper\nlinked_files: [repo_scan/mod.py]\n---\nbody\n",
        encoding="utf-8",
    )
    scan = {
        "files": {"repo_scan/mod.py": {"lines": 10}},
        "ranking": [{"file": "repo_scan/mod.py", "score": 5}],
        "behavior": {"age_days": {"repo_scan/mod.py": 1}},
        "citations": [{
            "file": "repo_scan/mod.py",
            "target_kind": "spec",
            "target_id": "seam-spec",
            "line": 1,
        }],
    }
    (docs / "scan.json").write_text(json.dumps(scan), encoding="utf-8")
    return scan


def test_score_full_chain_scores_three(tmp_repo: Path):
    """Max provenance score is 3 (E+L+C); fresh is vanity and not scored."""
    scan = _setup_chain(tmp_repo)
    from repo_scan.citations import citation_index
    cite_idx = citation_index(scan["citations"])
    node = {"id": "spec:seam-spec", "kind": "spec", "label": "seam-spec",
            "doc": "specs/seam-spec.md"}
    result = score_node(node, tmp_repo, DEFAULT_CONFIG, scan, cite_idx)
    assert result["score"] == 3
    assert "evidence" in result["signals"]
    assert "linked" in result["signals"]
    assert "cited" in result["signals"]


def test_missing_linked_files_drops_signal(tmp_repo: Path):
    docs = tmp_repo / "docs" / "specs"
    docs.mkdir(parents=True)
    (docs / "orphan-spec.md").write_text("---\nstatus: draft\n---\n", encoding="utf-8")
    scan = {"files": {}, "citations": []}
    node = {"id": "spec:orphan-spec", "kind": "spec", "doc": "specs/orphan-spec.md"}
    result = score_node(node, tmp_repo, DEFAULT_CONFIG, scan, {})
    assert "linked" not in result["signals"]
    assert result["score"] < 3


def test_stale_doc_loses_fresh_signal(tmp_repo: Path):
    docs = tmp_repo / "docs" / "research" / "sources"
    docs.mkdir(parents=True)
    path = docs / "old.md"
    path.write_text("---\nlinked_files: [repo_scan/hot.py]\n---\nnotes\n", encoding="utf-8")
    import os
    import time
    old = time.time() - 60 * 86400
    os.utime(path, (old, old))
    scan = {"files": {"repo_scan/hot.py": {"lines": 1}},
            "behavior": {"age_days": {"repo_scan/hot.py": 0}},
            "citations": []}
    node = {"id": "source:old", "kind": "source", "doc": "research/sources/old.md"}
    result = score_node(node, tmp_repo, DEFAULT_CONFIG, scan, {})
    assert "fresh" not in result["signals"]
    assert result.get("stale_days") is not None


def test_vault_coverage_counts_orphans_by_kind(tmp_repo: Path):
    scan = _setup_chain(tmp_repo)
    (tmp_repo / "docs" / "specs" / "lonely-spec.md").write_text(
        "---\nstatus: draft\n---\n", encoding="utf-8",
    )
    cov = vault_coverage(tmp_repo, DEFAULT_CONFIG, scan, scan["citations"])
    assert cov["docs"] >= 4
    assert cov["coverage_pct"] < 1.0
    assert sum(cov["orphans_by_kind"].values()) >= 1


def test_untracked_code_excludes_tests_and_docs(tmp_repo: Path):
    scan = {
        "files": {
            "repo_scan/core.py": {"lines": 10},
            "tests/test_core.py": {"lines": 5},
        },
        "ranking": [
            {"file": "repo_scan/core.py", "score": 10},
            {"file": "tests/test_core.py", "score": 1},
        ],
        "citations": [],
    }
    cov = vault_coverage(tmp_repo, DEFAULT_CONFIG, scan, [])
    assert "tests/test_core.py" not in cov["untracked_code"]
    assert "repo_scan/core.py" in cov["untracked_code"]


def test_thin_citations_returns_low_count_files():
    cites = [
        {"file": "a.py", "target_kind": "spec", "target_id": "x"},
        {"file": "b.py", "target_kind": "spec", "target_id": "y"},
        {"file": "b.py", "target_kind": "ticket", "target_id": "z"},
        {"file": "c.py", "target_kind": "spec", "target_id": "w"},
    ]
    result = thin_citations(cites, threshold=1)
    files = [r["file"] for r in result]
    assert "a.py" in files
    assert "c.py" in files
    assert "b.py" not in files  # b has 2 citations
