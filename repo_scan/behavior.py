"""Behavioral code analysis from git history (code-maat style).

One `git log --numstat` pass yields three signals no static analysis can see:

- change coupling: files that change together in commits — pairs with a high
  co-change degree but no import edge are hidden architectural seams
- ownership / bus factor: per-file author concentration — knowledge silos
- code age: days since last touch — stale-but-central files are risky
"""

import time
from itertools import combinations
from pathlib import Path

from .utils import run


def _parse_log(root: Path) -> list[dict]:
    """Commits as {author, ts, files} from a single git log pass."""
    out, _, code = run(
        ["git", "log", "--numstat", "--no-merges", "--no-renames",
         "--format=@%H|%ct|%ae"],
        cwd=root,
    )
    if code != 0 or not out.strip():
        return []
    commits: list[dict] = []
    current: dict | None = None
    for line in out.splitlines():
        if line.startswith("@"):
            parts = line[1:].split("|")
            if len(parts) == 3:
                current = {"author": parts[2], "ts": int(parts[1]), "files": []}
                commits.append(current)
        elif line.strip() and current is not None:
            cols = line.split("\t")
            if len(cols) == 3:
                current["files"].append(cols[2])
    return commits


def analyze_history(root: Path, cfg: dict, tracked: set[str]) -> dict:
    """Returns {"coupling": [...], "ownership": [...], "age": {...}}.

    Only files in `tracked` (the current scan's line_counts) are considered,
    so deleted files and generated docs never pollute the signals.
    """
    commits = _parse_log(root)
    max_changeset = cfg.get("coupling_max_changeset", 30)
    min_shared = cfg.get("coupling_min_shared", 4)
    min_degree = cfg.get("coupling_min_degree", 50)

    revs: dict[str, int] = {}
    pair_counts: dict[tuple[str, str], int] = {}
    authors: dict[str, dict[str, int]] = {}
    last_ts: dict[str, int] = {}

    for c in commits:
        files = sorted({f for f in c["files"] if f in tracked})
        for f in files:
            revs[f] = revs.get(f, 0) + 1
            authors.setdefault(f, {})
            authors[f][c["author"]] = authors[f].get(c["author"], 0) + 1
            last_ts[f] = max(last_ts.get(f, 0), c["ts"])
        # mass refactors (huge changesets) say nothing about logical coupling
        if 2 <= len(files) <= max_changeset:
            for a, b in combinations(files, 2):
                pair_counts[(a, b)] = pair_counts.get((a, b), 0) + 1

    coupling = []
    for (a, b), shared in pair_counts.items():
        if shared < min_shared:
            continue
        degree = round(100 * shared / ((revs[a] + revs[b]) / 2))
        if degree >= min_degree:
            coupling.append({"a": a, "b": b, "shared": shared, "degree": degree})
    coupling.sort(key=lambda x: (x["degree"], x["shared"]), reverse=True)

    ownership = []
    for f, by_author in authors.items():
        total = sum(by_author.values())
        top_author, top_n = max(by_author.items(), key=lambda x: x[1])
        ownership.append({
            "file": f,
            "commits": total,
            "authors": len(by_author),
            "top_author": top_author,
            "top_share": round(top_n / total, 2),
        })
    ownership.sort(key=lambda x: (x["top_share"], x["commits"]), reverse=True)

    now = int(time.time())
    age_days = {f: max(0, (now - ts) // 86400) for f, ts in last_ts.items()}

    return {"coupling": coupling, "ownership": ownership, "age_days": age_days}


def _norm_node(name: str) -> str:
    """Normalize file paths and dep-graph node names (dotted Python modules,
    TS relative paths) onto one key space for comparison."""
    n = name
    for ext in (".py", ".ts", ".tsx", ".js", ".jsx"):
        if n.endswith(ext):
            n = n[: -len(ext)]
            break
    n = n.replace("/", ".")
    if n.endswith(".__init__"):
        n = n[: -len(".__init__")]
    return n


def hidden_seams(coupling: list[dict], edges: list[tuple[str, str]]) -> list[dict]:
    """Coupled pairs with no import edge in either direction — candidates for
    a misplaced boundary or an implicit contract."""
    linked = set()
    for s, t in edges:
        linked.add(frozenset((_norm_node(s), _norm_node(t))))
    return [c for c in coupling
            if frozenset((_norm_node(c["a"]), _norm_node(c["b"]))) not in linked]
