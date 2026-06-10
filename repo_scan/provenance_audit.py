"""radar audit-provenance — vault coverage audit with regression detection.

Vault: docs/changelog/2026-06-11-dashboard-improvements

Reports coverage histogram, missing signals per doc, untracked code,
and optionally checks for regression against the last scan.json baseline.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from .citations import scan_citations
from .config import load_config
from .provenance import autolink_orphan_analyses, vault_coverage
from .provenance_lint import lint
from .utils import git_root


def _color(text: str, code: str) -> str:
    return f"\033[{code}m{text}\033[0m"


def _green(t: str) -> str:
    return _color(t, "32")


def _red(t: str) -> str:
    return _color(t, "31")


def _yellow(t: str) -> str:
    return _color(t, "33")


def _bold(t: str) -> str:
    return _color(t, "1")


def _load_baseline(root: Path, cfg: dict) -> dict | None:
    sj = root / cfg["docs_dir"] / "scan.json"
    if not sj.exists():
        return None
    try:
        data = json.loads(sj.read_text(encoding="utf-8"))
        return data.get("vault_health")
    except (json.JSONDecodeError, KeyError):
        return None


def audit(root: Path, cfg: dict, *, fix: bool = False,
          fail_on_regression: bool = False) -> int:
    """Run the full provenance audit.  Returns 0=ok, 1=regression/issues."""
    sj_path = root / cfg["docs_dir"] / "scan.json"
    if not sj_path.exists():
        print(_red("No scan.json found — run `repo-scan` first"))
        return 1

    scan = json.loads(sj_path.read_text(encoding="utf-8"))
    lc = {f: d.get("lines", 0) for f, d in (scan.get("files") or {}).items()}
    cites = scan_citations(root, cfg, lc)
    cov = vault_coverage(root, cfg, scan=scan, citations=cites)

    # ── Summary ──────────────────────────────────────────
    pct = round(cov["coverage_pct"] * 100, 1)
    print(_bold("Vault provenance audit"))
    print()
    print(f"  docs:           {cov['docs']}")
    print(f"  healthy (3/3):  {_green(str(cov['healthy']))}")
    print(f"  coverage:       {_green(f'{pct}%') if pct >= 50 else _yellow(f'{pct}%')}")
    print(f"  knowledge debt: {cov['knowledge_debt']}")
    print(f"  untracked code: {cov['untracked_code_count']}")
    print()

    # ── Histogram ────────────────────────────────────────
    hist = cov["score_histogram"]
    total = cov["docs"]
    print(_bold("Score histogram"))
    for score in sorted(hist, key=int):
        n = hist[score]
        bar = "█" * int(n / max(total, 1) * 40)
        label = _green(f"{n:>4}") if int(score) == 3 else f"{n:>4}"
        print(f"  score {score}: {label} {bar}")
    print()

    # ── By kind ──────────────────────────────────────────
    orphans = cov.get("orphans_by_kind", {})
    if orphans:
        print(_bold("Orphans by kind"))
        for kind in sorted(orphans):
            print(f"  {kind}: {orphans[kind]}")
        print()

    # ── Missing signals detail ───────────────────────────
    orphan_list = cov.get("orphans", [])
    if orphan_list:
        print(_bold(f"Docs missing signals ({len(orphan_list)})"))
        for o in orphan_list[:20]:
            missing = [s for s in ("evidence", "linked", "cited") if s in o.get("missing", [])]
            print(f"  [{o['score']}] {o['id']}  missing={missing}")
        if len(orphan_list) > 20:
            print(f"  ... and {len(orphan_list) - 20} more")
        print()

    # ── Untracked code ───────────────────────────────────
    untracked = cov.get("untracked_code", [])
    if untracked:
        print(_bold(f"Untracked code ({len(untracked)} files)"))
        for f in untracked[:10]:
            print(f"  {f}")
        print()

    # ── Lint issues ──────────────────────────────────────
    lint_issues = lint(root, cfg)
    broken = [i for i in lint_issues if i["problem"] == "broken_link"]
    if broken:
        print(_red(f"Broken linked_files ({len(broken)})"))
        for i in broken[:10]:
            print(f"  {i['file']}: {i['detail']}")
        print()

    # ── Auto-fix: orphan analysis linker ─────────────────
    if fix:
        linked = autolink_orphan_analyses(root, cfg)
        if linked:
            print(_green(f"Auto-linked {len(linked)} analysis doc(s)"))
            for name in linked:
                print(f"  {name}")
            print()

    # ── Regression check (#4) ────────────────────────────
    baseline = _load_baseline(root, cfg)
    regression = False
    if baseline:
        prev_pct = baseline.get("coverage_pct", 0)
        prev_healthy = baseline.get("healthy", 0)
        delta_pct = round((cov["coverage_pct"] - prev_pct) * 100, 1)
        delta_healthy = cov["healthy"] - prev_healthy

        print(_bold("vs last scan.json baseline"))
        arrow_pct = _green(f"+{delta_pct}%") if delta_pct >= 0 else _red(f"{delta_pct}%")
        arrow_h = _green(f"+{delta_healthy}") if delta_healthy >= 0 else _red(str(delta_healthy))
        print(f"  coverage:  {round(prev_pct * 100, 1)}% → {pct}%  ({arrow_pct})")
        print(f"  healthy:   {prev_healthy} → {cov['healthy']}  ({arrow_h})")

        if delta_pct < 0:
            regression = True
            print(_red("\n  ⚠ Coverage regression detected"))

        if delta_healthy < 0:
            regression = True
            print(_red(f"  ⚠ Lost {abs(delta_healthy)} healthy doc(s)"))
        print()

    if regression and fail_on_regression:
        print(_red("FAIL: coverage regressed (--fail-on-regression)"))
        return 1

    return 0


def main() -> int:
    import argparse
    parser = argparse.ArgumentParser(description="Vault provenance audit")
    parser.add_argument("--repo", default=".", help="Repo root")
    parser.add_argument("--fix", action="store_true",
                        help="Auto-link orphan analyses from source linked_files")
    parser.add_argument("--fail-on-regression", action="store_true",
                        help="Exit 1 if coverage dropped vs last scan.json")
    args = parser.parse_args()

    root = git_root(Path(args.repo).resolve()) or Path(args.repo).resolve()
    cfg = load_config(root)
    return audit(root, cfg, fix=args.fix, fail_on_regression=args.fail_on_regression)


if __name__ == "__main__":
    sys.exit(main())
