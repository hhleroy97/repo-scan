import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))


def _git(args: list[str], cwd: Path):
    subprocess.run(["git"] + args, cwd=cwd, check=True, capture_output=True)


@pytest.fixture
def tmp_repo(tmp_path: Path) -> Path:
    """A minimal git repo with one Python file and one commit."""
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(["init", "-q"], repo)
    _git(["config", "user.email", "t@t.com"], repo)
    _git(["config", "user.name", "T"], repo)
    (repo / "main.py").write_text("def hello():\n    pass\n")
    _git(["add", "."], repo)
    _git(["commit", "-qm", "init"], repo)
    return repo


@pytest.fixture
def tmp_repo_with_imports(tmp_repo: Path) -> Path:
    """tmp_repo plus an intra-repo import chain (app -> helpers)."""
    (tmp_repo / "helpers.py").write_text("def go():\n    pass\n")
    (tmp_repo / "app.py").write_text("import helpers\n\ndef run():\n    helpers.go()\n")
    _git(["add", "."], tmp_repo)
    _git(["commit", "-qm", "add imports"], tmp_repo)
    return tmp_repo
