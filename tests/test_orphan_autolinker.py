"""Tests for orphan analysis auto-linker (transitive linking from sources)."""

from pathlib import Path

from repo_scan.provenance import autolink_orphan_analyses


def _setup(tmp_path: Path, sources: dict[str, str], analyses: dict[str, str]) -> Path:
    root = tmp_path
    docs = root / "docs"

    src_dir = docs / "research" / "sources"
    src_dir.mkdir(parents=True)
    for name, content in sources.items():
        (src_dir / name).write_text(content)

    ana_dir = docs / "research" / "analysis"
    ana_dir.mkdir(parents=True)
    for name, content in analyses.items():
        (ana_dir / name).write_text(content)

    return root


def test_propagates_linked_files(tmp_path):
    (tmp_path / "repo_scan").mkdir()
    (tmp_path / "repo_scan" / "foo.py").write_text("pass")

    root = _setup(tmp_path,
        sources={"src-a.md": '---\nid: src-a\nlinked_files: ["repo_scan/foo.py"]\n---\n# S\n'},
        analyses={"test-analysis.md": '---\ntype: analysis\nsources: ["src-a"]\n---\n# A\n'},
    )
    updated = autolink_orphan_analyses(root, {"docs_dir": "docs"})
    assert "test-analysis.md" in updated

    text = (root / "docs/research/analysis/test-analysis.md").read_text()
    assert "repo_scan/foo.py" in text


def test_skips_already_linked(tmp_path):
    (tmp_path / "repo_scan").mkdir()
    (tmp_path / "repo_scan" / "foo.py").write_text("pass")

    root = _setup(tmp_path,
        sources={"src-a.md": '---\nid: src-a\nlinked_files: ["repo_scan/foo.py"]\n---\n# S\n'},
        analyses={"test-analysis.md": '---\ntype: analysis\nsources: ["src-a"]\nlinked_files: ["repo_scan/foo.py"]\n---\n# A\n'},
    )
    updated = autolink_orphan_analyses(root, {"docs_dir": "docs"})
    assert updated == []


def test_empty_sources_no_crash(tmp_path):
    root = _setup(tmp_path,
        sources={},
        analyses={"test-analysis.md": '---\ntype: analysis\n---\n# A\n'},
    )
    updated = autolink_orphan_analyses(root, {"docs_dir": "docs"})
    assert updated == []
