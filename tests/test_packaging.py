"""Packaging manifest and pyproject-only install contract (tkt-0007)."""

import subprocess
import sys
from importlib.metadata import entry_points
from pathlib import Path

import pytest

from repo_scan.behavior import analyze_history, hidden_seams
from repo_scan.config import DEFAULT_CONFIG

REPO_ROOT = Path(__file__).resolve().parent.parent

# Fields formerly duplicated in setup.py; pyproject.toml is the sole manifest.
_EXPECTED_NAME = "repo-scan"
_EXPECTED_VERSION = "0.2.0"
_EXPECTED_PYTHON = ">=3.10"
_EXPECTED_SCRIPTS = {
    "repo-scan": "repo_scan:main",
    "radar": "repo_scan.radar.cli:main",
}
_EXPECTED_PACKAGES = ["repo_scan", "repo_scan.radar", "repo_scan.hub"]
_EXPECTED_DEV = ["pytest>=8", "syrupy>=5", "radon", "lizard"]


def _load_pyproject(path: Path) -> dict:
    """Parse pyproject.toml; tomllib on 3.11+, line-based checks on 3.10."""
    raw = path.read_bytes()
    if sys.version_info >= (3, 11):
        import tomllib

        return tomllib.loads(raw.decode("utf-8"))
    text = raw.decode()
    assert f'name = "{_EXPECTED_NAME}"' in text
    assert f'version = "{_EXPECTED_VERSION}"' in text
    assert f'requires-python = "{_EXPECTED_PYTHON}"' in text
    for script, target in _EXPECTED_SCRIPTS.items():
        assert f'{script} = "{target}"' in text
    for pkg in _EXPECTED_PACKAGES:
        assert f'"{pkg}"' in text
    for dep in _EXPECTED_DEV:
        assert dep in text
    return {}


def _commit(repo: Path, files: dict[str, str], msg: str = "c"):
    for name, content in files.items():
        (repo / name).write_text(content)
    subprocess.run(["git", "add", "."], cwd=repo, check=True, capture_output=True)
    subprocess.run(
        ["git", "-c", "user.name=T", "-c", "user.email=t@t.com", "commit", "-qm", msg],
        cwd=repo,
        check=True,
        capture_output=True,
    )


def test_packaging_manifest_is_pyproject_only():
    """Packaging metadata lives only in pyproject.toml (no setup.py)."""
    assert not (REPO_ROOT / "setup.py").exists()
    pyproject = REPO_ROOT / "pyproject.toml"
    assert pyproject.exists()

    data = _load_pyproject(pyproject)
    if data:
        project = data["project"]
        assert project["name"] == _EXPECTED_NAME
        assert project["version"] == _EXPECTED_VERSION
        assert project["requires-python"] == _EXPECTED_PYTHON
        assert project["scripts"] == _EXPECTED_SCRIPTS
        assert project["optional-dependencies"]["dev"] == _EXPECTED_DEV
        assert data["tool"]["setuptools"]["packages"] == _EXPECTED_PACKAGES


def test_hidden_seam_absent_after_setup_removal(tmp_path: Path):
    """Without setup.py, pyproject.toml cannot form a hidden seam pair."""
    repo = tmp_path / "pkg"
    repo.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=repo, check=True, capture_output=True)
    pyproject = '[project]\nname = "x"\nversion = "0.1.0"\n'
    for i in range(5):
        _commit(
            repo,
            {"pyproject.toml": f'{pyproject}# rev {i}\n', "lib.py": f"x = {i}\n"},
            f"pair {i}",
        )
    tracked = {"pyproject.toml", "lib.py"}
    result = analyze_history(repo, DEFAULT_CONFIG, tracked)
    seam_paths = {frozenset((c["a"], c["b"])) for c in result["coupling"]}
    assert frozenset(("pyproject.toml", "setup.py")) not in seam_paths
    seams = hidden_seams(result["coupling"], [])
    assert not any(
        frozenset((s["a"], s["b"])) == frozenset(("pyproject.toml", "setup.py"))
        for s in seams
    )


def test_console_scripts_registered():
    """Editable install exposes repo-scan and radar console entry points."""
    names = {ep.name for ep in entry_points(group="console_scripts")}
    assert "repo-scan" in names
    assert "radar" in names
