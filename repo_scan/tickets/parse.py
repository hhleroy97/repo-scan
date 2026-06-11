"""Parse ticket markdown into structured dicts; derive PM-facing cards.

Vault: docs/research/analysis/2026-06-10-convert-tickets-to-most-human-friendly-t-analysis
Vault: docs/research/sources/arxiv-2411.12924
"""

import re
from pathlib import Path

from ..frontmatter import parse_frontmatter
from .constants import PLACEHOLDER_CRITERIA


def _normalize_criterion(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip().lower())


def criteria_ready(criteria: list[str]) -> bool:
    """True when at least one criterion is not a known placeholder string."""
    if not criteria:
        return False
    return any(_normalize_criterion(c) not in PLACEHOLDER_CRITERIA
               for c in criteria if c.strip())


def _strip_technical(text: str) -> str:
    """Remove backtick paths, CC parentheticals, and line-count suffixes."""

    def _backtick(m: re.Match) -> str:
        inner = m.group(1)
        return Path(inner).name if "/" in inner or "\\" in inner else inner

    text = re.sub(r"`([^`]+)`", _backtick, text)
    text = re.sub(r"\(CC\s+\d+[^)]*\)", "", text, flags=re.I)
    text = re.sub(r"\(\d+\s+lines\)", "", text, flags=re.I)
    return re.sub(r"\s+", " ", text).strip()


def _first_sentence(text: str, limit: int = 120) -> str:
    if not text:
        return ""
    sent = re.split(r"(?<=[.!?])\s+", text.strip(), maxsplit=1)[0]
    return _strip_technical(sent)[:limit]


def _parse_card_section(text: str) -> dict[str, str]:
    m = re.search(r"^## Card\n+(.+?)(?:\n##|\Z)", text, re.S | re.M)
    if not m:
        return {}
    card: dict[str, str] = {}
    for line in m.group(1).splitlines():
        for key in ("Outcome", "Story", "Title"):
            prefix = f"{key}:"
            if line.startswith(prefix):
                card[key.lower()] = line[len(prefix):].strip()
    return card


def _criteria_summary(criteria: list[str]) -> str:
    real = [c.strip() for c in criteria
            if c.strip() and _normalize_criterion(c) not in PLACEHOLDER_CRITERIA]
    return " · ".join(real[:2])


def derive_card(meta: dict, text: str) -> dict:
    """Build a PM-facing card from ticket ground truth.

    Base layer: heuristics from fingerprint kind (``refactor`` → reduce risk in
    basename, ``size`` → break up oversized basename, ``seam`` → make coupling
    explicit), else the first sentence of ``Why`` (≤120 chars). Technical
    paths and ``(CC N, …)`` / ``(N lines)`` parentheticals are stripped from
    display copy. Higher layers override: ``## Card`` fields, then frontmatter
    ``card_outcome`` / ``card_story`` / ``card_title``.
    """
    title = meta.get("title", "")
    why = meta.get("why", "")
    fingerprint = str(meta.get("fingerprint", ""))
    kind = fingerprint.split(":", 1)[0] if fingerprint else ""
    if not kind and meta.get("tags"):
        kind = str(meta["tags"][0])
    path_part = fingerprint.split(":", 1)[1] if ":" in fingerprint else ""
    basename = Path(path_part).name if path_part else ""

    if kind == "refactor":
        outcome = f"Reduce risk in {basename}" if basename else "Reduce risk in this area"
    elif kind == "size":
        outcome = f"Break up oversized {basename}" if basename else "Break up oversized file"
    elif kind == "seam":
        outcome = "Make coupling explicit"
    else:
        outcome = _first_sentence(why) or _strip_technical(title)

    card = {
        "title": title,
        "outcome": outcome,
        "story": "",
        "why_line": _first_sentence(why) or _strip_technical(why.splitlines()[0] if why else ""),
        "criteria_summary": _criteria_summary(meta.get("criteria", [])),
    }

    for key, val in _parse_card_section(text).items():
        if val:
            card[key] = val

    for fm_key, card_key in (("card_outcome", "outcome"), ("card_story", "story"),
                             ("card_title", "title")):
        if meta.get(fm_key):
            card[card_key] = str(meta[fm_key])

    return card


def parse_ticket(path: Path) -> dict | None:
    text = path.read_text(encoding="utf-8", errors="ignore")
    meta = parse_frontmatter(text)
    if not meta or "status" not in meta:
        return None
    title = next((l[2:].strip() for l in text.splitlines() if l.startswith("# ")),
                 meta.get("title", path.stem))
    meta.setdefault("id", path.stem)
    meta["title"] = meta.get("title") or title
    meta["path"] = path
    m = re.search(r"^## Why\n+(.+?)(?:\n##|\Z)", text, re.S | re.M)
    meta["why"] = m.group(1).strip() if m else ""
    checks = re.findall(r"^- \[([ x])\] (.+)$", text, re.M)
    meta["criteria"] = [c[1] for c in checks]
    meta["criteria_checked"] = [c[0] == "x" for c in checks]
    meta["criteria_ready"] = criteria_ready(meta["criteria"])
    meta["criteria_count"] = len(meta["criteria"])
    meta["card"] = derive_card(meta, text)
    meta["criteria_summary"] = meta["card"]["criteria_summary"]
    return meta
