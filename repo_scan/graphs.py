"""Dependency and call graph generation (Mermaid output)."""

import json
from pathlib import Path

from .utils import run, tool_available


def edges_to_mermaid(edges: list[tuple[str, str]]) -> str | None:
    """Render (src_module, dst_module) edges as a Mermaid graph."""
    if not edges:
        return None
    seen = set()
    lines = ["graph TD"]
    for s, t in edges:
        if (s, t) not in seen:
            seen.add((s, t))
            sl = s.replace(".", "_").replace("/", "_").replace("-", "_")
            tl = t.replace(".", "_").replace("/", "_").replace("-", "_")
            lines.append(f'  {sl}["{s.split(".")[-1].split("/")[-1]}"] --> {tl}["{t.split(".")[-1].split("/")[-1]}"]')
    return "\n".join(lines) if len(lines) > 1 else None


def get_ts_dep_edges(root: Path, ts_files: list[Path]) -> tuple[list[tuple[str, str]], str]:
    """TS/JS dependency edges via `madge --json` (madge >= 6 has no --mermaid).

    Returns (edges_as_relative_paths, skip_reason). Reason is "" on success.
    """
    if not ts_files:
        return [], "no TS/JS files"
    if not tool_available("madge"):
        return [], "madge not installed — npm install -g madge"
    src_candidates = ["src", "app", "lib", "."]
    src_dir = next((root / d for d in src_candidates if (root / d).is_dir()), root)
    out, _, code = run(["madge", "--json", str(src_dir)], cwd=root)
    if code != 0 or not out.strip():
        return [], "madge produced no output"
    try:
        graph = json.loads(out)
    except json.JSONDecodeError:
        return [], "madge output was not valid JSON"
    edges = [(src, dst) for src, deps in graph.items() for dst in deps]
    return edges, "" if edges else "no imports between files detected"


def get_python_dep_edges(root: Path, py_files: list[Path], cfg: dict) -> list[tuple[str, str]]:
    """Intra-repo Python import edges as (src_module, dst_module) pairs."""
    if not py_files:
        return []
    skip = set(cfg["exclude_dirs"])
    repo_modules: set[str] = set()
    for f in py_files:
        try:
            rel = f.relative_to(root)
            parts = list(rel.parts)
            if parts[-1] == "__init__.py":
                parts = parts[:-1]
            else:
                parts[-1] = parts[-1][:-3]
            repo_modules.add(".".join(parts))
        except ValueError:
            pass

    edges: list[tuple[str, str]] = []
    for f in py_files:
        if any(p in skip for p in f.parts):
            continue
        try:
            src = f.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        try:
            rel = f.relative_to(root)
            parts = list(rel.parts)
            if parts[-1] != "__init__.py":
                parts[-1] = parts[-1][:-3]
            src_mod = ".".join(parts)
        except ValueError:
            continue
        for line in src.splitlines():
            line = line.strip()
            imported = None
            if line.startswith("from ") and " import " in line:
                imported = line.split()[1].lstrip(".")
            elif line.startswith("import "):
                imported = line.split()[1].split(".")[0]
            if imported:
                for mod in repo_modules:
                    if mod == imported or mod.startswith(imported + "."):
                        edges.append((src_mod, mod))
                        break
    return edges


def get_python_dep_graph_mermaid(root: Path, py_files: list[Path], cfg: dict) -> str | None:
    return edges_to_mermaid(get_python_dep_edges(root, py_files, cfg))


def get_c_call_graph_mermaid(root: Path, c_files: list[Path]) -> str | None:
    if not tool_available("cflow") or not c_files:
        return None
    c_paths = [str(f) for f in c_files[:30]]
    out, _, code = run(["cflow", "--depth=3"] + c_paths, cwd=root)
    if code != 0 or not out.strip():
        return None
    lines = ["graph TD"]
    stack: list[str] = []
    seen: set[tuple[str, str]] = set()
    for line in out.splitlines():
        stripped = line.lstrip()
        if not stripped:
            continue
        depth = (len(line) - len(stripped)) // 4
        name = stripped.split("(")[0].strip().replace(" ", "_")
        if not name:
            continue
        stack = stack[:depth]
        if stack:
            edge = (stack[-1], name)
            if edge not in seen:
                seen.add(edge)
                lines.append(f'  {stack[-1]} --> {name}')
        stack.append(name)
    return "\n".join(lines) if len(lines) > 1 else None
