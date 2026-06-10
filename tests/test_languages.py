"""Characterization tests for repo_scan.languages (tkt-0004).

Monkeypatches tool_available and run (not subprocess) so tokei vs fallback
paths are deterministic. Covers skip-rule asymmetry between detect_languages
and get_line_counts, and the extension-filter gap between tokei and fallback.
"""

import json
from pathlib import Path
import pytest

from repo_scan.config import DEFAULT_CONFIG
from repo_scan.languages import (
    LOCKFILES,
    detect_languages,
    get_line_counts,
)
import repo_scan.languages as languages


CFG = dict(DEFAULT_CONFIG)


def _make_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "main.py").write_text("line1\nline2\nline3\n")
    (repo / "app.ts").write_text("const x = 1;\n")
    (repo / "util.c").write_text("int main() {}\n")
    (repo / "readme.md").write_text("# readme\n\nbody\n")
    return repo


def _tokei_json(root: Path, reports: list[dict]) -> str:
    """Build language-keyed tokei JSON matching get_line_counts' parser."""
    abs_reports = []
    for r in reports:
        name = r["name"]
        if not Path(name).is_absolute():
            name = str(root / name)
        abs_reports.append({**r, "name": name})
    return json.dumps({"Python": {"reports": abs_reports}})


def _stub_tokei(monkeypatch, *, available: bool, stdout: str = "", code: int = 0):
    monkeypatch.setattr(languages, "tool_available", lambda name: available and name == "tokei")
    monkeypatch.setattr(languages, "run", lambda cmd, cwd=None, timeout=30: (stdout, "", code))


# --- tokei path ---


def test_tokei_path_uses_stats_code_not_raw_lines(tmp_path, monkeypatch):
    repo = _make_repo(tmp_path)
    payload = _tokei_json(repo, [{"name": "main.py", "stats": {"code": 42}}])
    _stub_tokei(monkeypatch, available=True, stdout=payload, code=0)

    counts = get_line_counts(repo, CFG)

    assert counts["main.py"]["lines"] == 42


def test_tokei_unavailable_uses_fallback_splitlines(tmp_path, monkeypatch):
    repo = _make_repo(tmp_path)
    _stub_tokei(monkeypatch, available=False)

    counts = get_line_counts(repo, CFG)

    assert counts["main.py"]["lines"] == 3


def test_tokei_malformed_json_falls_back(tmp_path, monkeypatch):
    repo = _make_repo(tmp_path)
    _stub_tokei(monkeypatch, available=True, stdout="{not json", code=0)

    counts = get_line_counts(repo, CFG)

    assert counts["main.py"]["lines"] == 3


def test_tokei_missing_keys_falls_back(tmp_path, monkeypatch):
    repo = _make_repo(tmp_path)
    _stub_tokei(monkeypatch, available=True, stdout='{"Python": {"reports": [{}]}}', code=0)

    counts = get_line_counts(repo, CFG)

    assert counts["main.py"]["lines"] == 3


def test_tokei_nonzero_exit_falls_back(tmp_path, monkeypatch):
    repo = _make_repo(tmp_path)
    payload = _tokei_json(repo, [{"name": "main.py", "stats": {"code": 99}}])
    _stub_tokei(monkeypatch, available=True, stdout=payload, code=1)

    counts = get_line_counts(repo, CFG)

    assert counts["main.py"]["lines"] == 3


def test_tokei_path_keeps_absolute_path_outside_root(tmp_path, monkeypatch):
    repo = _make_repo(tmp_path)
    outside = tmp_path / "outside.py"
    outside.write_text("x\n")
    payload = json.dumps(
        {"Python": {"reports": [{"name": str(outside), "stats": {"code": 7}}]}}
    )
    _stub_tokei(monkeypatch, available=True, stdout=payload, code=0)

    counts = get_line_counts(repo, CFG)

    assert counts[str(outside)]["lines"] == 7


def test_tokei_path_counts_non_code_extensions(tmp_path, monkeypatch):
    """Tokei branch has no TS/Py/C extension filter; fallback does."""
    repo = _make_repo(tmp_path)
    payload = _tokei_json(repo, [{"name": "readme.md", "stats": {"code": 5}}])
    _stub_tokei(monkeypatch, available=True, stdout=payload, code=0)

    counts = get_line_counts(repo, CFG)

    assert "readme.md" in counts
    assert counts["readme.md"]["lines"] == 5


# --- fallback path ---


def test_fallback_extension_filter(tmp_path, monkeypatch):
    repo = _make_repo(tmp_path)
    (repo / "data.json").write_text("{\n  \"a\": 1\n}\n")
    _stub_tokei(monkeypatch, available=False)

    counts = get_line_counts(repo, CFG)

    assert "data.json" not in counts
    assert "main.py" in counts


def test_fallback_oserror_skips_file(tmp_path, monkeypatch):
    repo = _make_repo(tmp_path)
    _stub_tokei(monkeypatch, available=False)
    bad = repo / "main.py"
    original_read = Path.read_text

    def _read(self, *a, **kw):
        if self == bad:
            raise OSError("permission denied")
        return original_read(self, *a, **kw)

    monkeypatch.setattr(Path, "read_text", _read)

    counts = get_line_counts(repo, CFG)

    assert "main.py" not in counts
    assert "app.ts" in counts


# --- skip rules: get_line_counts ---


@pytest.mark.parametrize(
    "subdir,rel_name,expect_in_counts",
    [
        ("node_modules", "node_modules/pkg.py", False),
        ("docs", "docs/generated.py", False),
        (None, "package-lock.json", False),
    ],
    ids=["exclude_dir", "docs_dir", "lockfile"],
)
def test_get_line_counts_skip_rules(tmp_path, monkeypatch, subdir, rel_name, expect_in_counts):
    repo = _make_repo(tmp_path)
    if subdir:
        target = repo / subdir
        target.mkdir(parents=True)
        (target / Path(rel_name).name).write_text("skipme\n")
    else:
        (repo / rel_name).write_text("lock\n" * 10)
    _stub_tokei(monkeypatch, available=False)

    counts = get_line_counts(repo, CFG)

    assert (rel_name in counts) == expect_in_counts


@pytest.mark.parametrize("lockfile", sorted(LOCKFILES))
def test_get_line_counts_skips_all_lockfiles(tmp_path, monkeypatch, lockfile):
    repo = _make_repo(tmp_path)
    (repo / lockfile).write_text("locked\n")
    _stub_tokei(monkeypatch, available=False)

    counts = get_line_counts(repo, CFG)

    assert lockfile not in counts


# --- skip rules: detect_languages (exclude_dirs only) ---


def test_detect_languages_skips_exclude_dirs(tmp_path):
    repo = _make_repo(tmp_path)
    vendored = repo / "node_modules" / "pkg"
    vendored.mkdir(parents=True)
    (vendored / "dep.py").write_text("x\n")

    langs = detect_languages(repo, CFG)

    assert all("node_modules" not in str(p) for p in langs["py"])


def test_detect_languages_does_not_skip_docs_dir(tmp_path):
    repo = _make_repo(tmp_path)
    docs = repo / CFG["docs_dir"]
    docs.mkdir()
    (docs / "note.py").write_text("x\n")

    langs = detect_languages(repo, CFG)

    assert any(p.name == "note.py" for p in langs["py"])


def test_detect_languages_buckets_by_extension(tmp_path):
    repo = _make_repo(tmp_path)

    langs = detect_languages(repo, CFG)

    names = {f.name for f in langs["py"]}
    assert "main.py" in names
    assert {f.name for f in langs["ts"]} == {"app.ts"}
    assert {f.name for f in langs["c"]} == {"util.c"}


def test_detect_languages_returns_absolute_paths(tmp_path):
    repo = _make_repo(tmp_path)

    langs = detect_languages(repo, CFG)

    for bucket in langs.values():
        for p in bucket:
            assert p.is_absolute()


def test_get_line_counts_relative_path_keys(tmp_path, monkeypatch):
    repo = _make_repo(tmp_path)
    _stub_tokei(monkeypatch, available=False)

    counts = get_line_counts(repo, CFG)

    for key in counts:
        assert not Path(key).is_absolute()


def test_get_line_counts_bytes_from_stat(tmp_path, monkeypatch):
    repo = _make_repo(tmp_path)
    _stub_tokei(monkeypatch, available=False)

    counts = get_line_counts(repo, CFG)

    assert counts["main.py"]["bytes"] == (repo / "main.py").stat().st_size


def test_tokei_bytes_zero_when_file_missing(tmp_path, monkeypatch):
    repo = _make_repo(tmp_path)
    payload = _tokei_json(repo, [{"name": "ghost.py", "stats": {"code": 1}}])
    _stub_tokei(monkeypatch, available=True, stdout=payload, code=0)

    counts = get_line_counts(repo, CFG)

    assert counts["ghost.py"]["lines"] == 1
    assert counts["ghost.py"]["bytes"] == 0
