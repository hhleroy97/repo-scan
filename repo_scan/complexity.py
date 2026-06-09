"""Python complexity via radon (optional tool)."""

import json
from pathlib import Path

from .utils import run, tool_available


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
