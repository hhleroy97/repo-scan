"""Source model and docs/research/ writers.

Every ingested source normalizes to one Source and one markdown file at
docs/research/sources/{id}.md with YAML frontmatter, so Obsidian graph view
and Dataview see real tags and properties instead of opaque code blocks.
Index and tags markdown are rebuilt from source files via private helpers.
"""

import re
from dataclasses import dataclass, field, asdict
from pathlib import Path

from ..utils import now_iso, ok, strip_emoji, write_doc


# ---------------------------------------------------------------------------
# Minimal YAML frontmatter (write + parse) — stdlib only, flat keys
# ---------------------------------------------------------------------------

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


@dataclass
class Source:
    id: str
    type: str               # arxiv | github | url | file
    url: str
    title: str
    summary: str = ""
    key_claims: list[str] = field(default_factory=list)
    relevance: str = ""
    tags: list[str] = field(default_factory=list)
    linked_files: list[str] = field(default_factory=list)
    ingested_at: str = ""
    raw_url: str = ""

    def __post_init__(self):
        if not self.ingested_at:
            self.ingested_at = now_iso()


def slugify(text: str, max_len: int = 60) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return slug[:max_len].rstrip("-") or "untitled"


def source_id_for(source_type: str, ref: str) -> str:
    if source_type == "arxiv":
        return f"arxiv-{ref.replace('/', '-')}"
    if source_type == "github":
        return f"gh-{ref.replace('/', '-')}"
    if source_type == "file":
        return f"file-{slugify(Path(ref).stem)}"
    return f"url-{slugify(ref.split('//')[-1])}"


def _sources_dir(root: Path, cfg: dict) -> Path:
    return root / cfg["docs_dir"] / "research" / "sources"


def write_source(root: Path, cfg: dict, source: Source) -> Path:
    """Write one source markdown file. Never overwrites human annotations:
    if the file exists, only the generated block above the Notes heading is
    replaced and everything from `## Notes` down is preserved."""
    sources_dir = _sources_dir(root, cfg)
    sources_dir.mkdir(parents=True, exist_ok=True)
    path = sources_dir / f"{source.id}.md"

    claims = "\n".join(f"- {c}" for c in source.key_claims) or "_none extracted yet_"
    tags = [slugify(t, 30) for t in source.tags]
    linked = [f if f.startswith("[[") else f"[[{f}]]" for f in source.linked_files]
    generated = "\n".join([
        frontmatter({
            "id": source.id,
            "type": source.type,
            "url": source.url,
            "raw_url": source.raw_url or source.url,
            "tags": tags,
            "linked_files": linked,
            "relevance": source.relevance,
            "ingested_at": source.ingested_at,
        }),
        "",
        f"# {strip_emoji(source.title)}",
        "",
        "## Summary",
        "",
        source.summary or "_pending — run radar with an LLM backend to summarize_",
        "",
        "## Key claims",
        "",
        claims,
        "",
        "",
    ])

    notes = "## Notes\n\n_yours to annotate_\n"
    if path.exists():
        existing = path.read_text(encoding="utf-8")
        marker = existing.find("## Notes")
        if marker != -1:
            notes = existing[marker:]

    write_doc(path, generated + notes, root)
    return path


def parse_source_file(path: Path) -> dict:
    """Parse a source note's frontmatter back into a dict (for index rebuilds)."""
    text = path.read_text(encoding="utf-8", errors="ignore")
    meta = parse_frontmatter(text)
    if not meta:
        return meta
    title = next((line[2:].strip() for line in text.splitlines() if line.startswith("# ")),
                 path.stem)
    meta["title"] = strip_emoji(title)
    return meta


def _collect_source_entries(sources_dir: Path) -> list[dict]:
    """Parse *.md files under sources_dir; return meta dicts newest-first.

    Returns [] when sources_dir is missing or not a directory. Skips files
    where parse_source_file yields empty meta.
    """
    entries: list[dict] = []
    if not sources_dir.is_dir():
        return entries
    for f in sorted(sources_dir.glob("*.md")):
        meta = parse_source_file(f)
        if meta:
            entries.append(meta)
    entries.sort(key=lambda m: m.get("ingested_at", ""), reverse=True)
    return entries


def _render_index_markdown(entries: list[dict]) -> str:
    """Build research/index.md body: table of wikilinked sources."""
    lines = [
        "# Research index",
        f"_Rebuilt {now_iso()} — {len(entries)} source(s)_",
        "",
        "| Source | Type | Tags | Ingested |",
        "|--------|------|------|----------|",
    ]
    for m in entries:
        sid = m.get("id", "?")
        title = m.get("title", sid)
        if len(title) > 90:
            title = title[:90].rsplit(" ", 1)[0] + "…"
        lines.append(f"| [[sources/{sid}\\|{title}]] | {m.get('type', '?')} | "
                     f"{m.get('tags', '')} | {m.get('ingested_at', '')} |")
    if not entries:
        lines.append("| _none yet — run `radar ingest <ref>`_ | | | |")
    lines.append("")
    return "\n".join(lines)


def _build_tag_map(entries: list[dict]) -> dict[str, list[dict]]:
    """Group source meta dicts by comma-split frontmatter tags."""
    tag_map: dict[str, list[dict]] = {}
    for m in entries:
        for tag in [t.strip() for t in m.get("tags", "").split(",") if t.strip()]:
            tag_map.setdefault(tag, []).append(m)
    return tag_map


def _render_tags_markdown(tag_map: dict[str, list[dict]]) -> str:
    """Build research/tags.md body: sorted ## sections with wikilink bullets."""
    tag_lines = ["# Research tags", f"_Rebuilt {now_iso()}_", ""]
    for tag in sorted(tag_map):
        tag_lines.append(f"## {tag}")
        tag_lines.append("")
        for m in tag_map[tag]:
            tag_lines.append(f"- [[sources/{m.get('id', '?')}\\|{m.get('title', '?')}]]")
        tag_lines.append("")
    if not tag_map:
        tag_lines.append("_no tagged sources yet_\n")
    return "\n".join(tag_lines)


def rebuild_research_index(root: Path, cfg: dict):
    """Regenerate research/index.md and research/tags.md from source files.

    Delegates to _collect_source_entries and markdown render helpers; output
    paths and Obsidian wikilink format are unchanged.
    """
    research = root / cfg["docs_dir"] / "research"
    research.mkdir(parents=True, exist_ok=True)
    sources_dir = research / "sources"
    entries = _collect_source_entries(sources_dir)
    write_doc(research / "index.md", _render_index_markdown(entries), root)
    write_doc(research / "tags.md", _render_tags_markdown(_build_tag_map(entries)), root)
