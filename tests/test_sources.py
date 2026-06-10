"""Source model, frontmatter, write_source, and research index rebuild."""

from pathlib import Path

from repo_scan.config import load_config
from repo_scan.radar.sources import (
    Source,
    frontmatter,
    parse_frontmatter,
    parse_source_file,
    rebuild_research_index,
    source_id_for,
    write_source,
)


def test_frontmatter_roundtrip_with_colons_and_lists():
    block = frontmatter({
        "id": "arxiv-1",
        "url": "https://arxiv.org/abs/1",
        "title_like": "ReAct: Synergizing",
        "tags": ["paper", "agents"],
        "empty": "",
    })
    assert block.startswith("---\n") and block.endswith("\n---")
    meta = parse_frontmatter(block)
    assert meta["url"] == "https://arxiv.org/abs/1"
    assert meta["title_like"] == "ReAct: Synergizing"
    assert meta["tags"] == "paper, agents"
    assert meta["empty"] == ""


def test_write_source_emits_obsidian_frontmatter(tmp_repo: Path):
    cfg = load_config(tmp_repo)
    src = Source(id="arxiv-2", type="arxiv", url="https://arxiv.org/abs/2",
                 title="P", tags=["Multi Agent", "paper"],
                 linked_files=["repo_scan/gates.py"])
    path = write_source(tmp_repo, cfg, src)
    text = path.read_text()
    assert text.startswith("---\n")
    assert 'tags: ["multi-agent", "paper"]' in text      # slugified for Obsidian
    assert 'linked_files: ["[[repo_scan/gates.py]]"]' in text  # ghost-node link
    assert "\n# P\n" in text


def test_source_id_for():
    assert source_id_for("arxiv", "2210.03629") == "arxiv-2210.03629"
    assert source_id_for("github", "yamadashy/repomix") == "gh-yamadashy-repomix"
    assert source_id_for("url", "https://example.com/A Post!") == "url-example-com-a-post"
    assert source_id_for("file", "/tmp/My Paper.pdf") == "file-my-paper"


def test_write_source_preserves_human_notes(tmp_repo: Path):
    cfg = load_config(tmp_repo)
    src = Source(id="arxiv-1", type="arxiv", url="https://arxiv.org/abs/1",
                 title="Paper One", summary="first pass", tags=["paper"])
    path = write_source(tmp_repo, cfg, src)

    content = path.read_text().replace("_yours to annotate_\n", "MY ANNOTATION\n")
    path.write_text(content)

    src.summary = "second pass"
    write_source(tmp_repo, cfg, src)
    updated = path.read_text()
    assert "second pass" in updated
    assert "MY ANNOTATION" in updated


def test_parse_source_file_roundtrip(tmp_repo: Path):
    cfg = load_config(tmp_repo)
    src = Source(id="gh-a-b", type="github", url="https://github.com/a/b",
                 title="a/b — thing", tags=["repo", "python"], relevance="rel")
    path = write_source(tmp_repo, cfg, src)
    meta = parse_source_file(path)
    assert meta["id"] == "gh-a-b"
    assert meta["type"] == "github"
    assert meta["tags"] == "repo, python"
    assert meta["title"] == "a/b — thing"


def test_rebuild_research_index(tmp_repo: Path):
    cfg = load_config(tmp_repo)
    write_source(tmp_repo, cfg, Source(id="arxiv-1", type="arxiv", url="u",
                                       title="Paper", tags=["paper", "agents"]))
    write_source(tmp_repo, cfg, Source(id="gh-x-y", type="github", url="u2",
                                       title="x/y", tags=["repo"]))
    rebuild_research_index(tmp_repo, cfg)

    index = (tmp_repo / "docs" / "research" / "index.md").read_text()
    assert "[[sources/arxiv-1\\|Paper]]" in index
    assert "[[sources/gh-x-y\\|x/y]]" in index

    tags = (tmp_repo / "docs" / "research" / "tags.md").read_text()
    assert "## agents" in tags
    assert "## repo" in tags


def test_rebuild_research_index_empty(tmp_repo: Path):
    cfg = load_config(tmp_repo)
    rebuild_research_index(tmp_repo, cfg)
    index = (tmp_repo / "docs" / "research" / "index.md").read_text()
    assert "none yet" in index


def test_rebuild_research_index_truncates_long_title(tmp_repo: Path):
    """Single-token titles >90 chars truncate at char 90 (no word boundary)."""
    cfg = load_config(tmp_repo)
    long_title = "x" * 95
    expected_display = "x" * 90 + "…"
    write_source(tmp_repo, cfg, Source(id="long-1", type="file", url="u",
                                       title=long_title, tags=["paper"]))
    rebuild_research_index(tmp_repo, cfg)
    index = (tmp_repo / "docs" / "research" / "index.md").read_text()
    assert f"[[sources/long-1\\|{expected_display}]]" in index


def test_rebuild_research_index_one_source_multiple_tags(tmp_repo: Path):
    cfg = load_config(tmp_repo)
    write_source(tmp_repo, cfg, Source(id="multi-1", type="arxiv", url="u",
                                       title="Multi Tag Paper",
                                       tags=["alpha", "beta", "gamma"]))
    rebuild_research_index(tmp_repo, cfg)
    tags_md = (tmp_repo / "docs" / "research" / "tags.md").read_text()
    for tag in ("alpha", "beta", "gamma"):
        assert f"## {tag}" in tags_md
        assert "[[sources/multi-1\\|Multi Tag Paper]]" in tags_md


def test_parse_frontmatter_missing_block():
    assert parse_frontmatter("# Just a heading\n\nno frontmatter here.") == {}


def test_parse_frontmatter_skips_malformed_lines():
    block = "---\nvalid: ok\nthis line has no colon\nalso: fine\n---\n"
    meta = parse_frontmatter(block)
    assert meta == {"valid": "ok", "also": "fine"}
