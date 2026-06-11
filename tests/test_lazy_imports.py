"""Verify core modules load without pulling in higher-layer clusters."""

import subprocess
import sys
import textwrap


def test_core_scanner_import_isolation():
    """``import repo_scan.scanner`` must not eagerly load radar, hub, or tickets."""
    script = textwrap.dedent("""\
        import sys
        import repo_scan.scanner
        loaded = set(sys.modules)
        for bad in ("repo_scan.radar", "repo_scan.hub", "repo_scan.tickets"):
            hits = [m for m in loaded if m.startswith(bad)]
            assert not hits, f"{bad} eagerly loaded: {hits}"
    """)
    result = subprocess.run(
        [sys.executable, "-c", script],
        capture_output=True, text=True,
    )
    assert result.returncode == 0, result.stderr
