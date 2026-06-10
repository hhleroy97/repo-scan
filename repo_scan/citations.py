"""Code → vault citation scanner (scan-time, no deps)."""

from __future__ import annotations

import re
from pathlib import Path

_WIKILINK_RE = re.compile(r"\[\[([^\]|#]+)")
_DOC_PATH_RE = re.compile(
    r"docs/(?:specs/([^\s\]|#]+\-spec)|tickets/(tkt-\d{4})|research/sources/([^\s\]|#]+)|research/analysis/([^\s\]|#]+))"
)
_SPEC_TAG_RE = re.compile(r"#\s*spec:\s*([a-zA-Z0-9_-]+-spec)", re.I)
_TICKET_TAG_RE = re.compile(r"#\s*ticket:\s*(tkt-\d{4})", re.I)
_MAX_PER_FILE = 20
_VAULT_KINDS = frozenset({"ticket", "spec", "analysis", "source"})


def _resolve_target(root: Path, cfg: dict, kind: str, key: str) -> tuple[str, str] | None:
    """Return (target_kind, target_id) when the vault artifact exists."""
    docs = root / cfg["docs_dir"]
    paths = {
        "ticket": docs / "tickets" / f"{key}.md",
        "spec": docs / "specs" / f"{key}.md",
        "analysis": docs / "research" / "analysis" / f"{key}.md",
        "source": docs / "research" / "sources" / f"{key}.md",
    }
    if kind not in paths or not paths[kind].exists():
        return None
    return kind, key


def _stem_target(root: Path, cfg: dict, stem: str) -> tuple[str, str] | None:
    stem = stem.strip()
    if stem.startswith("tkt-"):
        return _resolve_target(root, cfg, "ticket", stem)
    if stem.endswith("-spec"):
        return _resolve_target(root, cfg, "spec", stem)
    if stem.startswith("research/sources/") or stem.startswith("sources/"):
        return _resolve_target(root, cfg, "source", stem.split("/")[-1])
    if stem.startswith("research/analysis/"):
        return _resolve_target(root, cfg, "analysis", stem.split("/")[-1])
    return None


def _scan_file(root: Path, cfg: dict, rel: str, text: str,
               seen: set[tuple[str, str, str, int]]) -> list[dict]:
    rows: list[dict] = []
    docs_prefix = cfg["docs_dir"] + "/"

    def add(line_no: int, kind: str, key: str):
        if len(rows) >= _MAX_PER_FILE:
            return
        resolved = _resolve_target(root, cfg, kind, key)
        if not resolved:
            return
        sig = (rel, resolved[0], resolved[1], line_no)
        if sig in seen:
            return
        seen.add(sig)
        rows.append({
            "file": rel,
            "target_kind": resolved[0],
            "target_id": resolved[1],
            "line": line_no,
        })

    for i, line in enumerate(text.splitlines(), 1):
        if len(rows) >= _MAX_PER_FILE:
            break
        for m in _DOC_PATH_RE.finditer(line):
            if m.group(1):
                add(i, "spec", m.group(1))
            elif m.group(2):
                add(i, "ticket", m.group(2))
            elif m.group(3):
                add(i, "source", m.group(3))
            elif m.group(4):
                add(i, "analysis", m.group(4))
        for m in _SPEC_TAG_RE.finditer(line):
            add(i, "spec", m.group(1))
        for m in _TICKET_TAG_RE.finditer(line):
            add(i, "ticket", m.group(1))
        for m in _WIKILINK_RE.finditer(line):
            hit = _stem_target(root, cfg, m.group(1))
            if hit:
                add(i, hit[0], hit[1])
    return rows


def scan_citations(root: Path, cfg: dict, line_counts: dict,
                   *, include_tests: bool = False) -> list[dict]:
    """Walk Python sources; return citation rows for scan.json."""
    docs_dir = cfg["docs_dir"] + "/"
    seen: set[tuple[str, str, str, int]] = set()
    out: list[dict] = []
    for rel in sorted(line_counts):
        if not rel.endswith(".py"):
            continue
        if rel.startswith(docs_dir):
            continue
        if not include_tests and (
            rel.startswith("tests/") or "/tests/" in rel or rel.startswith("test_")
        ):
            continue
        path = root / rel
        if not path.is_file():
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        out.extend(_scan_file(root, cfg, rel, text, seen))
    return out


def citation_index(citations: list[dict]) -> dict[tuple[str, str], list[str]]:
    """Map (target_kind, target_id) → citing code file paths."""
    idx: dict[tuple[str, str], list[str]] = {}
    for row in citations:
        key = (row["target_kind"], row["target_id"])
        idx.setdefault(key, [])
        if row["file"] not in idx[key]:
            idx[key].append(row["file"])
    return idx
