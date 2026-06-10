"""Dependency graph helpers (relative-import resolution)."""

from pathlib import Path

from repo_scan.config import DEFAULT_CONFIG
from repo_scan.graphs import get_python_dep_edges


def test_relative_import_resolves_intra_package_edge(tmp_path: Path):
    """``from .writers`` in scanner resolves to ``repo_scan.writers``."""
    pkg = tmp_path / "repo_scan"
    pkg.mkdir()
    (pkg / "__init__.py").write_text("")
    (pkg / "writers.py").write_text('"""writers."""\n')
    (pkg / "scanner.py").write_text(
        '"""scanner."""\nfrom .writers import write_health_report\n'
    )
    py_files = list(pkg.glob("*.py")) + [pkg / "__init__.py"]
    edges = get_python_dep_edges(tmp_path, py_files, DEFAULT_CONFIG)
    assert ("repo_scan.scanner", "repo_scan.writers") in edges
