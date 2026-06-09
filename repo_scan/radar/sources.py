"""Source model and docs/research/ writers.

Every ingested source normalizes to one Source and one markdown file at
docs/research/sources/{id}.md with a parseable key-value frontmatter block.
"""

import re
from dataclasses import dataclass, field, asdict
from pathlib import Path

from ..utils import now_iso, ok, write_doc


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
    generated = "\n".join([
        f"# {source.title}",
        "",
        "```source",
        f"id: {source.id}",
        f"type: {source.type}",
        f"url: {source.url}",
        f"raw_url: {source.raw_url or source.url}",
        f"tags: {', '.join(source.tags)}",
        f"linked_files: {', '.join(source.linked_files)}",
        f"relevance: {source.relevance}",
        f"ingested_at: {source.ingested_at}",
        "```",
        "",
        "## Summary",
        "",
        source.summary or "_pending — run radar with an LLM backend to summarize_",
        "",
        "## Key claims",
        "",
        claims,
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
    """Parse the ```source block back into a dict (for index rebuilds)."""
    meta: dict = {}
    text = path.read_text(encoding="utf-8", errors="ignore")
    m = re.search(r"```source\n(.*?)```", text, re.S)
    if not m:
        return meta
    for line in m.group(1).splitlines():
        if ":" in line:
            key, _, value = line.partition(":")
            meta[key.strip()] = value.strip()
    title = text.splitlines()[0].lstrip("# ").strip() if text.splitlines() else path.stem
    meta["title"] = title
    return meta


def rebuild_research_index(root: Path, cfg: dict):
    """Regenerate research/index.md and research/tags.md from source files."""
    research = root / cfg["docs_dir"] / "research"
    research.mkdir(parents=True, exist_ok=True)
    sources_dir = research / "sources"
    entries = []
    if sources_dir.is_dir():
        for f in sorted(sources_dir.glob("*.md")):
            meta = parse_source_file(f)
            if meta:
                entries.append(meta)
    entries.sort(key=lambda m: m.get("ingested_at", ""), reverse=True)

    lines = [
        "# Research index",
        f"_Rebuilt {now_iso()} — {len(entries)} source(s)_",
        "",
        "| Source | Type | Tags | Ingested |",
        "|--------|------|------|----------|",
    ]
    for m in entries:
        sid = m.get("id", "?")
        lines.append(f"| [[sources/{sid}\\|{m.get('title', sid)}]] | {m.get('type', '?')} | "
                     f"{m.get('tags', '')} | {m.get('ingested_at', '')} |")
    if not entries:
        lines.append("| _none yet — run `radar ingest <ref>`_ | | | |")
    lines.append("")
    write_doc(research / "index.md", "\n".join(lines), root)

    tag_map: dict[str, list[dict]] = {}
    for m in entries:
        for tag in [t.strip() for t in m.get("tags", "").split(",") if t.strip()]:
            tag_map.setdefault(tag, []).append(m)

    tag_lines = ["# Research tags", f"_Rebuilt {now_iso()}_", ""]
    for tag in sorted(tag_map):
        tag_lines.append(f"## {tag}")
        tag_lines.append("")
        for m in tag_map[tag]:
            tag_lines.append(f"- [[sources/{m.get('id', '?')}\\|{m.get('title', '?')}]]")
        tag_lines.append("")
    if not tag_map:
        tag_lines.append("_no tagged sources yet_\n")
    write_doc(research / "tags.md", "\n".join(tag_lines), root)
