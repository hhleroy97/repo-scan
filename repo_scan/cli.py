"""repo-scan CLI entry point."""

import argparse
import sys
from pathlib import Path

from .config import VERSION, load_config, write_default_config
from .hooks import install_hook
from .scanner import run_digest, scan
from .utils import err, header, ok, step, tool_available, warn
from .writers import write_agents_md


def check_deps():
    tools = {
        "tokei":  "brew install tokei  OR  cargo install tokei",
        "madge":  "npm install -g madge",
        "radon":  "pip install radon",
        "cflow":  "brew install cflow  OR  apt install cflow",
        "git":    "(should already be installed)",
    }
    header("Dependency check")
    for tool, install in tools.items():
        if tool_available(tool):
            ok(f"{tool:<10} available")
        else:
            warn(f"{tool:<10} missing — {install}")
    print()


def main():
    parser = argparse.ArgumentParser(
        description="repo-scan — repo intelligence tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("repo_path", nargs="?", default=".", help="Repo root (default: cwd)")
    parser.add_argument("--version",       action="version", version=f"repo-scan {VERSION}")
    parser.add_argument("--init",          action="store_true", help="Write default .repo-scan.json to repo")
    parser.add_argument("--init-agents",   action="store_true", help="Write AGENTS.md scaffold to repo root")
    parser.add_argument("--install-hook",  action="store_true", help="Install git pre-commit hook")
    parser.add_argument("--check-deps",    action="store_true", help="Check required tools")
    parser.add_argument("--handoff",       action="store_true", help="Generate docs/HANDOFF.md bootstrap doc")
    parser.add_argument("--digest",        action="store_true", help="Write docs/digest.md single-file LLM context")
    parser.add_argument("--quiet",         action="store_true", help="Minimal output (for hook use)")
    args = parser.parse_args()

    root = Path(args.repo_path).resolve()
    if not root.exists():
        err(f"Path not found: {root}")
        sys.exit(1)

    if args.check_deps:
        check_deps()
        return

    if args.install_hook:
        install_hook(root)
        return

    if args.init:
        step("Writing config")
        write_default_config(root)
        return

    if args.init_agents:
        step("Writing AGENTS.md")
        write_agents_md(root)
        return

    if args.digest:
        path = run_digest(root)
        ok(f"wrote {path.relative_to(root)}")
        return

    scan(root, quiet=args.quiet, include_handoff=args.handoff)


if __name__ == "__main__":
    main()
