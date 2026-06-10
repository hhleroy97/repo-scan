"""Test-presence heuristic: which source files have any test signal."""

from pathlib import Path

import repo_scan
from repo_scan.tests_map import find_tested_files, is_test_file


def test_is_test_file():
    assert is_test_file("tests/test_ranking.py")
    assert is_test_file("src/__tests__/App.tsx")
    assert is_test_file("src/App.test.tsx")
    assert is_test_file("src/foo.spec.ts")
    assert is_test_file("pkg/util_test.go")
    assert not is_test_file("src/App.tsx")
    assert not is_test_file("repo_scan/scanner.py")
    assert not is_test_file("src/contest.py")  # 'test' inside a word doesn't count


def test_find_tested_files_python_layout():
    files = ["repo_scan/ranking.py", "repo_scan/scanner.py", "tests/test_ranking.py"]
    tested = find_tested_files(files)
    assert "repo_scan/ranking.py" in tested
    assert "repo_scan/scanner.py" not in tested
    assert "tests/test_ranking.py" not in tested  # test files aren't 'tested'


def test_find_tested_files_ts_layout():
    files = ["src/App.tsx", "src/App.test.tsx", "src/ui/PageSection.tsx"]
    tested = find_tested_files(files)
    assert "src/App.tsx" in tested
    assert "src/ui/PageSection.tsx" not in tested


def test_index_files_match_on_parent_dir():
    files = ["src/sections/about/index.tsx", "tests/about.test.tsx", "src/other/index.tsx"]
    tested = find_tested_files(files)
    assert "src/sections/about/index.tsx" in tested
    assert "src/other/index.tsx" not in tested


def test_scan_emits_tests_column_and_candidate_boost(tmp_repo_with_imports: Path):
    (tmp_repo_with_imports / "tests").mkdir()
    (tmp_repo_with_imports / "tests" / "test_helpers.py").write_text(
        "import helpers\n\ndef test_go():\n    helpers.go()\n")
    repo_scan.scan(tmp_repo_with_imports, quiet=True)
    index = (tmp_repo_with_imports / "docs" / "index.md").read_text()
    assert "| Tests |" in index
    helpers_row = next(l for l in index.splitlines() if l.startswith("| `helpers.py`"))
    assert "| yes |" in helpers_row
    app_row = next(l for l in index.splitlines() if l.startswith("| `app.py`"))
    assert "| **no** |" in app_row
