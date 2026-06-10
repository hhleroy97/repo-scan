"""Tests for provenance_lint — linked_files linter."""

from pathlib import Path

from repo_scan.provenance_lint import lint


def _setup(tmp_path: Path, docs: dict[str, str]) -> Path:
    root = tmp_path
    dd = root / "docs"
    for rel, content in docs.items():
        p = dd / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content)
    return root


def test_lint_clean(tmp_path):
    (tmp_path / "repo_scan" / "foo.py").parent.mkdir(parents=True)
    (tmp_path / "repo_scan" / "foo.py").write_text("pass")
    root = _setup(tmp_path, {
        "tickets/tkt-0001.md": '---\nid: tkt-0001\nlinked_files: ["repo_scan/foo.py"]\n---\n# T\n',
    })
    issues = lint(root, {"docs_dir": "docs"})
    assert issues == []


def test_lint_missing_linked_files(tmp_path):
    root = _setup(tmp_path, {
        "tickets/tkt-0001.md": "---\nid: tkt-0001\n---\n# T\n",
    })
    issues = lint(root, {"docs_dir": "docs"})
    assert len(issues) == 1
    assert issues[0]["problem"] == "missing_linked_files"


def test_lint_broken_link(tmp_path):
    root = _setup(tmp_path, {
        "tickets/tkt-0001.md": '---\nid: tkt-0001\nlinked_files: ["nonexistent.py"]\n---\n# T\n',
    })
    issues = lint(root, {"docs_dir": "docs"})
    assert len(issues) == 1
    assert issues[0]["problem"] == "broken_link"
    assert "nonexistent.py" in issues[0]["detail"]


def test_lint_specs_and_sources(tmp_path):
    (tmp_path / "repo_scan" / "bar.py").parent.mkdir(parents=True)
    (tmp_path / "repo_scan" / "bar.py").write_text("pass")
    root = _setup(tmp_path, {
        "specs/foo-spec.md": '---\ntype: spec\nlinked_files: ["repo_scan/bar.py"]\n---\n# S\n',
        "research/sources/gh-foo.md": '---\nid: gh-foo\nlinked_files: ["repo_scan/bar.py"]\n---\n# X\n',
    })
    issues = lint(root, {"docs_dir": "docs"})
    assert issues == []
