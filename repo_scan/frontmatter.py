"""Minimal YAML frontmatter (write + parse) — stdlib only, flat keys.

Extracted from ``radar/sources.py`` so lower layers (tickets, vault) can
use frontmatter without importing radar.

Vault: docs/changelog/2026-06-11-boundary-hardening
Vault: docs/research/sources/gh-eyeseast-python-frontmatter
Spec:  docs/specs/2026-06-10-refactor-repo-scan-radar-sources-py-cc-1-spec
"""

from __future__ import annotations

import re


def slugify(text: str, max_len: int = 60) -> str:
    """Lowercase text to URL-safe slug, truncated to *max_len* chars."""
    slug = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return slug[:max_len].rstrip("-") or "untitled"


def _yaml_value(value) -> str:
    if isinstance(value, list):
        return "[" + ", ".join(_yaml_value(v) for v in value) + "]"
    text = str(value)
    return '"' + text.replace('"', "'") + '"' if text else '""'


def frontmatter(fields: dict) -> str:
    """Render a flat dict as a YAML frontmatter block. Strings are quoted so
    colons in URLs/titles never break parsing; lists use flow style."""
    lines = ["---"]
    for key, value in fields.items():
        lines.append(f"{key}: {_yaml_value(value)}")
    lines.append("---")
    return "\n".join(lines)


def parse_frontmatter(text: str) -> dict:
    """Parse a flat frontmatter block back into strings (lists → 'a, b')."""
    meta: dict = {}
    m = re.match(r"---\n(.*?)\n---", text, re.S)
    if not m:
        return meta
    for line in m.group(1).splitlines():
        if ":" not in line:
            continue
        key, _, value = line.partition(":")
        value = value.strip()
        if value.startswith("[") and value.endswith("]"):
            items = [v.strip().strip('"') for v in value[1:-1].split(",")]
            value = ", ".join(v for v in items if v)
        else:
            value = value.strip('"')
        meta[key.strip()] = value
    return meta
