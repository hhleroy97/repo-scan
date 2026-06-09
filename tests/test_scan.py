"""Behavior lock for the repo_scan monolith (pre/post Phase A and the A2 split)."""

import json
from pathlib import Path

import repo_scan


def test_scan_writes_expected_files(tmp_repo: Path):
    repo_scan.scan(tmp_repo, quiet=True)
    docs = tmp_repo / "docs"
    for rel in [
        "index.md",
        "reports/health.md",
        "reports/dependencies.md",
        "reports/calls.md",
        "architecture/dependency-graph.md",
    ]:
        assert (docs / rel).exists(), f"missing {rel}"
    assert (docs / "research").is_dir()


def test_load_config_defaults_and_override(tmp_repo: Path):
    cfg = repo_scan.load_config(tmp_repo)
    assert cfg["line_warn"] == 300
    (tmp_repo / ".repo-scan.json").write_text(json.dumps({"line_warn": 100}))
    cfg = repo_scan.load_config(tmp_repo)
    assert cfg["line_warn"] == 100
    assert cfg["line_crit"] == 600  # untouched defaults survive


def test_load_config_bad_json_falls_back(tmp_repo: Path):
    (tmp_repo / ".repo-scan.json").write_text("{not json")
    cfg = repo_scan.load_config(tmp_repo)
    assert cfg == repo_scan.DEFAULT_CONFIG | {}


def test_write_default_config_idempotent(tmp_repo: Path, capsys):
    repo_scan.write_default_config(tmp_repo)
    first = (tmp_repo / ".repo-scan.json").read_text()
    repo_scan.write_default_config(tmp_repo)
    assert (tmp_repo / ".repo-scan.json").read_text() == first


def test_detect_languages_buckets(tmp_repo_with_imports: Path):
    cfg = repo_scan.load_config(tmp_repo_with_imports)
    langs = repo_scan.detect_languages(tmp_repo_with_imports, cfg)
    names = {f.name for f in langs["py"]}
    assert names == {"main.py", "helpers.py", "app.py"}
    assert langs["ts"] == []
    assert langs["c"] == []


def test_python_dep_graph_detects_intra_repo_imports(tmp_repo_with_imports: Path):
    cfg = repo_scan.load_config(tmp_repo_with_imports)
    py_files = repo_scan.detect_languages(tmp_repo_with_imports, cfg)["py"]
    mermaid = repo_scan.get_python_dep_graph_mermaid(tmp_repo_with_imports, py_files, cfg)
    assert mermaid is not None
    assert mermaid.startswith("graph TD")
    assert 'app["app"] --> helpers["helpers"]' in mermaid


def test_python_dep_graph_none_when_no_imports(tmp_repo: Path):
    cfg = repo_scan.load_config(tmp_repo)
    py_files = repo_scan.detect_languages(tmp_repo, cfg)["py"]
    assert repo_scan.get_python_dep_graph_mermaid(tmp_repo, py_files, cfg) is None


def test_git_churn_counts(tmp_repo_with_imports: Path):
    cfg = repo_scan.load_config(tmp_repo_with_imports)
    churn = repo_scan.get_git_churn(tmp_repo_with_imports, cfg)
    by_file = {c["file"]: c["commits"] for c in churn}
    assert by_file["main.py"] == 1
    assert by_file["app.py"] == 1


def test_install_hook_creates_and_is_idempotent(tmp_repo: Path):
    repo_scan.install_hook(tmp_repo)
    hook = tmp_repo / ".git" / "hooks" / "pre-commit"
    assert hook.exists()
    content = hook.read_text()
    assert content.count("# --- repo-scan pre-commit hook ---") == 1
    repo_scan.install_hook(tmp_repo)
    assert hook.read_text().count("# --- repo-scan pre-commit hook ---") == 1


def test_install_hook_appends_to_existing(tmp_repo: Path):
    hook = tmp_repo / ".git" / "hooks" / "pre-commit"
    hook.write_text("#!/bin/sh\necho existing\n")
    hook.chmod(0o755)
    repo_scan.install_hook(tmp_repo)
    content = hook.read_text()
    assert content.startswith("#!/bin/sh\necho existing")
    assert "# --- repo-scan pre-commit hook ---" in content


def test_index_contains_wikilinks(tmp_repo: Path):
    repo_scan.scan(tmp_repo, quiet=True)
    index = (tmp_repo / "docs" / "index.md").read_text()
    for link in ["[[reports/health]]", "[[reports/dependencies]]", "[[reports/calls]]"]:
        assert link in index


def test_handoff_flag_writes_handoff(tmp_repo: Path):
    repo_scan.scan(tmp_repo, quiet=True, include_handoff=True)
    assert (tmp_repo / "docs" / "HANDOFF.md").exists()
