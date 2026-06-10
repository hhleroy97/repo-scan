"""B1: Fetch parsers (no network) — arxiv, github, file, html."""

from pathlib import Path

import pytest

from repo_scan.radar.fetchers import (
    FetchError,
    fetch_file,
    html_to_text,
    parse_arxiv_atom,
    parse_github_repo,
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
