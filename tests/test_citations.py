"""Code → vault citation scanner."""

from pathlib import Path

from repo_scan.citations import scan_citations
from repo_scan.config import DEFAULT_CONFIG


def _write(repo: Path, rel: str, text: str):
    path = repo / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def test_detects_comment_path_reference(tmp_repo: Path):
    docs = tmp_repo / "docs"
    (docs / "specs").mkdir(parents=True)
    (docs / "specs" / "foo-spec.md").write_text("---\nstatus: draft\n---\n", encoding="utf-8")
    _write(tmp_repo, "repo_scan/mod.py", "# see docs/specs/foo-spec.md\n")
    cites = scan_citations(tmp_repo, DEFAULT_CONFIG, {"repo_scan/mod.py": {"lines": 1}})
    assert any(c["target_kind"] == "spec" and c["target_id"] == "foo-spec" for c in cites)


def test_detects_wikilink_in_docstring(tmp_repo: Path):
    docs = tmp_repo / "docs" / "tickets"
    docs.mkdir(parents=True)
    (docs / "tkt-0042.md").write_text("---\ntitle: T\n---\n", encoding="utf-8")
    _write(tmp_repo, "app.py", '"""Implements [[tkt-0042]]"""\n')
    cites = scan_citations(tmp_repo, DEFAULT_CONFIG, {"app.py": {"lines": 2}})
    assert cites[0]["target_id"] == "tkt-0042"


def test_excludes_tests_directory_by_default(tmp_repo: Path):
    docs = tmp_repo / "docs" / "specs"
    docs.mkdir(parents=True)
    (docs / "foo-spec.md").write_text("---\n---\n", encoding="utf-8")
    _write(tmp_repo, "tests/test_x.py", "# spec: foo-spec\n")
    cites = scan_citations(tmp_repo, DEFAULT_CONFIG, {
        "tests/test_x.py": {"lines": 1},
        "mod.py": {"lines": 1},
    })
    assert not any(c["file"].startswith("tests/") for c in cites)


def test_unresolved_references_dropped(tmp_repo: Path):
    _write(tmp_repo, "mod.py", "# spec: missing-spec\n")
    cites = scan_citations(tmp_repo, DEFAULT_CONFIG, {"mod.py": {"lines": 1}})
    assert cites == []
