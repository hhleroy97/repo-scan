"""Git pre-commit hook installer."""

import sys
from pathlib import Path

from .utils import err, ok, warn

HOOK_SCRIPT = """\

# --- repo-scan pre-commit hook ---
REPO_ROOT="$(git rev-parse --show-toplevel)"
if command -v repo-scan &>/dev/null; then
    echo "repo-scan: scanning..."
    repo-scan "$REPO_ROOT" --quiet
    git add "$REPO_ROOT/docs/" 2>/dev/null
    echo "repo-scan: docs/ updated"
elif [ -f "$REPO_ROOT/scripts/repo_scan.py" ]; then
    echo "repo-scan: scanning (script mode)..."
    python "$REPO_ROOT/scripts/repo_scan.py" "$REPO_ROOT"
    git add "$REPO_ROOT/docs/" 2>/dev/null
fi
# --- end repo-scan ---
"""


def install_hook(root: Path):
    git_dir = root / ".git"
    if not git_dir.exists():
        err("Not a git repository")
        sys.exit(1)

    hook_path = git_dir / "hooks" / "pre-commit"

    if hook_path.exists():
        if "repo-scan" in hook_path.read_text():
            warn("Hook already installed — skipping")
            return
        with hook_path.open("a") as f:
            f.write(HOOK_SCRIPT)
        ok(f"Appended to existing pre-commit hook at {hook_path}")
    else:
        hook_path.write_text("#!/bin/sh" + HOOK_SCRIPT)
        hook_path.chmod(0o755)
        ok(f"Installed pre-commit hook at {hook_path}")
