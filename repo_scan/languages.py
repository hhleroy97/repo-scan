"""Language detection and line counting.

Vault: docs/tickets/tkt-0004
Spec:  docs/specs/2026-06-10-refactor-repo-scan-languages-py-cc-18-3-spec
"""

import json
from pathlib import Path

from .utils import run, tool_available

TS_EXTENSIONS = {".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs"}
PY_EXTENSIONS = {".py"}
C_EXTENSIONS  = {".c", ".h", ".cpp", ".cc", ".cxx", ".hpp"}

# Machine-generated files that pollute line counts, health alerts, and ranking
LOCKFILES = {
    "package-lock.json", "yarn.lock", "pnpm-lock.yaml", "bun.lockb",
    "poetry.lock", "uv.lock", "Pipfile.lock",
    "Cargo.lock", "composer.lock", "Gemfile.lock", "go.sum",
}


def _should_skip(
    rel: Path, cfg: dict, *, skip_docs: bool, skip_lockfiles: bool,
) -> bool:
    skip_dirs = set(cfg["exclude_dirs"])
    if skip_docs:
        skip_dirs.add(cfg["docs_dir"])
    if any(p in skip_dirs for p in rel.parts):
        return True
    return skip_lockfiles and rel.name in LOCKFILES


def detect_languages(root: Path, cfg: dict) -> dict[str, list[Path]]:
    buckets: dict[str, list[Path]] = {"ts": [], "py": [], "c": []}
    for f in root.rglob("*"):
        if not f.is_file():
            continue
        rel = f.relative_to(root)
        if _should_skip(rel, cfg, skip_docs=False, skip_lockfiles=False):
            continue
        ext = f.suffix.lower()
        if ext in TS_EXTENSIONS:
            buckets["ts"].append(f)
        elif ext in PY_EXTENSIONS:
            buckets["py"].append(f)
        elif ext in C_EXTENSIONS:
            buckets["c"].append(f)
    return buckets


def _iter_tokei_reports(data: dict):
    for lang_data in data.values():
        for report in lang_data.get("reports", []):
            yield report


def _tokei_entry(root: Path, report: dict) -> tuple[str, dict]:
    path = Path(report["name"])
    try:
        rel = path.relative_to(root)
    except ValueError:
        rel = path
    return str(rel), {
        "lines": report["stats"]["code"],
        "bytes": path.stat().st_size if path.exists() else 0,
    }


def _parse_tokei_json(
    out: str, root: Path, cfg: dict,
) -> dict[str, dict] | None:
    try:
        data = json.loads(out)
    except json.JSONDecodeError:
        return None
    counts: dict[str, dict] = {}
    for report in _iter_tokei_reports(data):
        try:
            path = Path(report["name"])
            rel = path.relative_to(root)
        except ValueError:
            rel = path
        except KeyError:
            return None
        if _should_skip(rel, cfg, skip_docs=True, skip_lockfiles=True):
            continue
        try:
            key, entry = _tokei_entry(root, report)
        except KeyError:
            return None
        counts[key] = entry
    return counts


def _fallback_line_counts(root: Path, cfg: dict) -> dict[str, dict]:
    counts: dict[str, dict] = {}
    all_exts = TS_EXTENSIONS | PY_EXTENSIONS | C_EXTENSIONS
    for f in root.rglob("*"):
        if not f.is_file():
            continue
        rel = f.relative_to(root)
        if _should_skip(rel, cfg, skip_docs=True, skip_lockfiles=True):
            continue
        if f.suffix.lower() not in all_exts:
            continue
        try:
            n = len(f.read_text(encoding="utf-8", errors="ignore").splitlines())
            counts[str(rel)] = {"lines": n, "bytes": f.stat().st_size}
        except OSError:
            pass
    return counts


def get_line_counts(root: Path, cfg: dict) -> dict[str, dict]:
    if tool_available("tokei"):
        out, _, code = run(["tokei", "--output", "json"], cwd=root)
        if code == 0:
            counts = _parse_tokei_json(out, root, cfg)
            if counts is not None:
                return counts
    return _fallback_line_counts(root, cfg)
