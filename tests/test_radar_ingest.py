"""B1: Source model, fetch parsers (no network), research index rebuild."""

from pathlib import Path

import pytest

from repo_scan.config import load_config
from repo_scan.radar.fetchers import (
    FetchError,
    fetch_file,
    html_to_text,
    parse_arxiv_atom,
    parse_github_repo,
)
from repo_scan.radar.sources import (
    Source,
    parse_source_file,
    rebuild_research_index,
    source_id_for,
    write_source,
)

ARXIV_ATOM = """<?xml version="1.0"?>
<feed xmlns="http://www.w3.org/2005/Atom">
  <entry>
    <title>ReAct: Synergizing Reasoning and Acting
      in Language Models</title>
    <summary>We explore the use of LLMs to generate
      both reasoning traces and task-specific actions.</summary>
    <author><name>Shunyu Yao</name></author>
    <author><name>Jeffrey Zhao</name></author>
  </entry>
</feed>"""


def test_source_id_for():
    assert source_id_for("arxiv", "2210.03629") == "arxiv-2210.03629"
    assert source_id_for("github", "yamadashy/repomix") == "gh-yamadashy-repomix"
    assert source_id_for("url", "https://example.com/A Post!") == "url-example-com-a-post"
    assert source_id_for("file", "/tmp/My Paper.pdf") == "file-my-paper"


def test_parse_arxiv_atom():
    source, text = parse_arxiv_atom(ARXIV_ATOM, "2210.03629")
    assert source.id == "arxiv-2210.03629"
    assert source.title.startswith("ReAct: Synergizing")
    assert "reasoning traces" in source.summary
    assert "Shunyu Yao" in text
    assert source.url == "https://arxiv.org/abs/2210.03629"


def test_parse_arxiv_atom_no_entry():
    with pytest.raises(FetchError):
        parse_arxiv_atom("<feed></feed>", "0000.00000")


def test_parse_github_repo():
    api = {
        "html_url": "https://github.com/yamadashy/repomix",
        "description": "Pack your codebase into AI-friendly formats",
        "language": "TypeScript",
        "stargazers_count": 20000,
        "forks_count": 500,
        "topics": ["ai", "llm"],
    }
    source, text = parse_github_repo(api, "# Repomix\nreadme body", "yamadashy/repomix")
    assert source.id == "gh-yamadashy-repomix"
    assert "TypeScript" in text and "readme body" in text
    assert "typescript" in source.tags


def test_html_to_text_skips_script_and_finds_title():
    html = ("<html><head><title>My Post</title><script>evil()</script></head>"
            "<body><nav>menu</nav><p>Real content here.</p></body></html>")
    title, text = html_to_text(html)
    assert title == "My Post"
    assert "Real content" in text
    assert "evil" not in text
    assert "menu" not in text


def test_fetch_file_text(tmp_path: Path):
    f = tmp_path / "notes.md"
    f.write_text("# Notes\nimportant finding\n")
    source, text = fetch_file(str(f))
    assert source.type == "file"
    assert "important finding" in text


def test_fetch_file_missing():
    with pytest.raises(FetchError):
        fetch_file("/nonexistent/path.md")


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
