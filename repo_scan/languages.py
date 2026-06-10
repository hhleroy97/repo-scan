"""Language detection and line counting."""

import json
from pathlib import Path

from .utils import run, tool_available

TS_EXTENSIONS = {".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs"}
PY_EXTENSIONS = {".py"}
C_EXTENSIONS  = {".c", ".h", ".cpp", ".cc", ".cxx", ".hpp"}


def detect_languages(root: Path, cfg: dict) -> dict[str, list[Path]]:
    skip = set(cfg["exclude_dirs"])
    buckets: dict[str, list[Path]] = {"ts": [], "py": [], "c": []}
    for f in root.rglob("*"):
        if not f.is_file():
            continue
        if any(p in skip for p in f.parts):
            continue
        ext = f.suffix.lower()
        if ext in TS_EXTENSIONS:
            buckets["ts"].append(f)
        elif ext in PY_EXTENSIONS:
            buckets["py"].append(f)
        elif ext in C_EXTENSIONS:
            buckets["c"].append(f)
    return buckets


def get_line_counts(root: Path, cfg: dict) -> dict[str, dict]:
    counts = {}
    # the generated docs tree is the tool's own output — never audit it
    skip = set(cfg["exclude_dirs"]) | {cfg["docs_dir"]}

    if tool_available("tokei"):
        out, _, code = run(["tokei", "--output", "json"], cwd=root)
        if code == 0:
            try:
                data = json.loads(out)
                for lang_data in data.values():
                    for report in lang_data.get("reports", []):
                        path = Path(report["name"])
                        try:
                            rel = path.relative_to(root)
                        except ValueError:
                            rel = path
                        if any(p in skip for p in rel.parts):
                            continue
                        counts[str(rel)] = {
                            "lines": report["stats"]["code"],
                            "bytes": path.stat().st_size if path.exists() else 0,
                        }
                return counts
            except (json.JSONDecodeError, KeyError):
                pass

    all_exts = TS_EXTENSIONS | PY_EXTENSIONS | C_EXTENSIONS
    for f in root.rglob("*"):
        if not f.is_file():
            continue
        if any(p in skip for p in f.parts):
            continue
        if f.suffix.lower() not in all_exts:
            continue
        try:
            n = len(f.read_text(encoding="utf-8", errors="ignore").splitlines())
            counts[str(f.relative_to(root))] = {"lines": n, "bytes": f.stat().st_size}
        except OSError:
            pass

    return counts
