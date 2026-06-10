"""Complexity analysis: radon for Python, lizard for everything else.

radon gives Python the nicer letter ranks; lizard (pip install lizard) covers
TS/TSX/JS/C/Java/Go etc. so non-Python repos still get complexity signal —
without it, candidates.md is empty on every frontend repo."""

import csv
import io
import json
from pathlib import Path

from .utils import run, tool_available

# radon's rank scale, applied to lizard CCN values for a consistent column
_RANK_THRESHOLDS = [(41, "F"), (31, "E"), (21, "D"), (11, "C"), (6, "B"), (1, "A")]


def _ccn_rank(ccn: int) -> str:
    for threshold, rank in _RANK_THRESHOLDS:
        if ccn >= threshold:
            return rank
    return "A"


def _min_ccn(min_rank: str) -> int:
    for threshold, rank in _RANK_THRESHOLDS:
        if rank == min_rank.upper():
            return threshold
    return 11  # default: rank C


def get_python_complexity(root: Path, py_files: list[Path], cfg: dict) -> list[dict]:
    if not tool_available("radon") or not py_files:
        return []
    out, _, code = run(["radon", "cc", "--json", "--min", cfg["complexity_min_rank"], str(root)], cwd=root)
    if code != 0 or not out.strip():
        return []
    results = []
    try:
        data = json.loads(out)
        for filepath, functions in data.items():
            try:
                rel = str(Path(filepath).relative_to(root))
            except ValueError:
                rel = filepath
            for fn in functions:
                results.append({
                    "file": rel,
                    "name": fn.get("name", "?"),
                    "rank": fn.get("rank", "?"),
                    "complexity": fn.get("complexity", 0),
                    "lineno": fn.get("lineno", 0),
                })
    except (json.JSONDecodeError, KeyError):
        pass
    return sorted(results, key=lambda x: x["complexity"], reverse=True)


def get_lizard_complexity(root: Path, cfg: dict, skip_python: bool = False) -> list[dict]:
    """Function complexity for non-Python (and optionally Python) files via
    lizard. Returns the same row shape as get_python_complexity."""
    if not tool_available("lizard"):
        return []
    cmd = ["lizard", "--csv"]
    for d in set(cfg["exclude_dirs"]) | {cfg["docs_dir"]}:
        cmd += ["-x", f"*/{d}/*"]
    cmd.append(str(root))
    out, _, code = run(cmd, cwd=root)
    if not out.strip():
        return []

    min_ccn = _min_ccn(cfg.get("complexity_min_rank", "C"))
    results = []
    for row in csv.reader(io.StringIO(out)):
        # NLOC, CCN, tokens, params, length, location, file, function, long_name, start, end
        if len(row) < 10:
            continue
        try:
            ccn, lineno = int(row[1]), int(row[9])
        except ValueError:
            continue
        filepath = row[6]
        try:
            rel = str(Path(filepath).relative_to(root))
        except ValueError:
            rel = filepath
        if skip_python and rel.endswith(".py"):
            continue
        if ccn < min_ccn:
            continue
        results.append({
            "file": rel,
            "name": row[7],
            "rank": _ccn_rank(ccn),
            "complexity": ccn,
            "lineno": lineno,
        })
    return sorted(results, key=lambda x: x["complexity"], reverse=True)


def get_complexity(root: Path, py_files: list[Path], cfg: dict) -> list[dict]:
    """Merged complexity: radon for Python when available, lizard for the rest
    (and for Python too if radon is missing)."""
    py_rows = get_python_complexity(root, py_files, cfg)
    lizard_rows = get_lizard_complexity(root, cfg, skip_python=bool(py_rows) or bool(
        py_files and tool_available("radon")))
    return sorted(py_rows + lizard_rows, key=lambda x: x["complexity"], reverse=True)
