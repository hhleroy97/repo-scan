"""Pre-commit linked_files linter for vault docs.

Vault: docs/changelog/2026-06-11-dashboard-improvements

Checks that vault docs (tickets, specs, analyses, sources) have
``linked_files`` frontmatter pointing to files that exist in the repo.
Exit code 0 = pass, 1 = issues found.

Usage as a git pre-commit hook::

    python -m repo_scan.provenance_lint [--fix]

Or via .pre-commit-config.yaml::

    - repo: local
      hooks:
        - id: linked-files-lint
          name: vault linked_files check
          entry: python -m repo_scan.provenance_lint
          language: python
          pass_filenames: false
          stages: [commit]
"""

from __future__ import annotations

import sys
from pathlib import Path

from .config import load_config
from .radar.sources import parse_frontmatter


_VAULT_PATTERNS = (
    ("tickets", "tkt-*.md"),
    ("specs", "*-spec.md"),
    ("research/analysis", "*-analysis.md"),
    ("research/sources", "*.md"),
)


def _parse_linked(fm: dict) -> list[str]:
    raw = str(fm.get("linked_files", "") or "")
    if not raw or raw == "[]":
        return []
    if raw.startswith("["):
        parts = [p.strip().strip("[]\"'") for p in raw[1:-1].split(",")]
    else:
        parts = [p.strip().strip("[]\"'") for p in raw.split(",")]
    return [p for p in parts if p]


def lint(root: Path, cfg: dict) -> list[dict]:
    """Return a list of issues: [{file, problem, detail}]."""
    docs = root / cfg["docs_dir"]
    issues: list[dict] = []

    for subdir, glob in _VAULT_PATTERNS:
        base = docs / subdir
        if not base.is_dir():
            continue
        for path in sorted(base.glob(glob)):
            text = path.read_text(encoding="utf-8", errors="ignore")
            fm = parse_frontmatter(text)
            linked = _parse_linked(fm)

            if not linked:
                issues.append({
                    "file": str(path.relative_to(root)),
                    "problem": "missing_linked_files",
                    "detail": "no linked_files in frontmatter",
                })
                continue

            for lf in linked:
                if not (root / lf).exists():
                    issues.append({
                        "file": str(path.relative_to(root)),
                        "problem": "broken_link",
                        "detail": f"linked_files references missing file: {lf}",
                    })
    return issues


def main() -> int:
    from .utils import git_root
    root = git_root(Path.cwd()) or Path.cwd()
    cfg = load_config(root)

    issues = lint(root, cfg)
    if not issues:
        print("vault lint: all docs have valid linked_files")
        return 0

    missing = [i for i in issues if i["problem"] == "missing_linked_files"]
    broken = [i for i in issues if i["problem"] == "broken_link"]

    if missing:
        print(f"\n{len(missing)} doc(s) missing linked_files:")
        for i in missing[:15]:
            print(f"  {i['file']}")
        if len(missing) > 15:
            print(f"  ... and {len(missing) - 15} more")

    if broken:
        print(f"\n{len(broken)} broken linked_files reference(s):")
        for i in broken:
            print(f"  {i['file']}: {i['detail']}")

    print(f"\nTotal: {len(issues)} issue(s)")
    return 1


if __name__ == "__main__":
    sys.exit(main())
