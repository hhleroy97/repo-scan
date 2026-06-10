"""Source fetchers. All stdlib; trafilatura/pymupdf enhance when installed.

Fetch functions do I/O; parse functions are pure so tests can exercise them
with canned payloads. Every fetcher returns (Source, full_text) or raises
FetchError with a human-readable reason.
"""

import json
import re
import urllib.error
import urllib.request
from html.parser import HTMLParser
from pathlib import Path

from .sources import Source, source_id_for

FETCH_TIMEOUT = 30
USER_AGENT = "repo-scan-radar/0.2 (+https://github.com/hhleroy97/repo-scan)"


class FetchError(Exception):
    pass


def _http_get(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=FETCH_TIMEOUT) as resp:
            return resp.read()
    except (urllib.error.URLError, TimeoutError, OSError) as e:
        raise FetchError(f"fetch failed for {url}: {e}") from e


# ---------------------------------------------------------------------------
# arXiv
# ---------------------------------------------------------------------------

def parse_arxiv_atom(xml_text: str, arxiv_id: str) -> tuple[Source, str]:
    def _first(tag: str) -> str:
        m = re.search(rf"<{tag}[^>]*>(.*?)</{tag}>", xml_text, re.S)
        return re.sub(r"\s+", " ", m.group(1)).strip() if m else ""

    entry = re.search(r"<entry>(.*?)</entry>", xml_text, re.S)
    if not entry:
        raise FetchError(f"arXiv returned no entry for {arxiv_id}")
    body = entry.group(1)
    title = re.sub(r"\s+", " ", re.search(r"<title>(.*?)</title>", body, re.S).group(1)).strip()
    summary_m = re.search(r"<summary>(.*?)</summary>", body, re.S)
    abstract = re.sub(r"\s+", " ", summary_m.group(1)).strip() if summary_m else ""
    authors = re.findall(r"<name>(.*?)</name>", body)

    source = Source(
        id=source_id_for("arxiv", arxiv_id),
        type="arxiv",
        url=f"https://arxiv.org/abs/{arxiv_id}",
        raw_url=f"https://arxiv.org/pdf/{arxiv_id}",
        title=title,
        summary=abstract,
        tags=["paper"],
    )
    text = f"{title}\n\nAuthors: {', '.join(authors)}\n\n{abstract}"
    return source, text


def fetch_arxiv(arxiv_id: str) -> tuple[Source, str]:
    xml = _http_get(f"http://export.arxiv.org/api/query?id_list={arxiv_id}").decode("utf-8", "ignore")
    return parse_arxiv_atom(xml, arxiv_id)


# ---------------------------------------------------------------------------
# GitHub
# ---------------------------------------------------------------------------

def parse_github_repo(api_json: dict, readme_text: str, owner_repo: str) -> tuple[Source, str]:
    desc = (api_json.get("description") or "GitHub repository").strip()
    if len(desc) > 80:
        desc = desc[:80].rsplit(" ", 1)[0] + "…"
    source = Source(
        id=source_id_for("github", owner_repo),
        type="github",
        url=api_json.get("html_url", f"https://github.com/{owner_repo}"),
        title=f"{owner_repo} — {desc}",
        summary=api_json.get("description") or "",
        tags=["repo"] + ([api_json["language"].lower()] if api_json.get("language") else []),
    )
    stats = (f"stars: {api_json.get('stargazers_count', '?')}, "
             f"forks: {api_json.get('forks_count', '?')}, "
             f"language: {api_json.get('language', '?')}, "
             f"topics: {', '.join(api_json.get('topics', []))}")
    return source, f"{stats}\n\n{readme_text}"


def fetch_github(owner_repo: str) -> tuple[Source, str]:
    api = json.loads(_http_get(f"https://api.github.com/repos/{owner_repo}").decode("utf-8", "ignore"))
    readme = ""
    for branch in [api.get("default_branch", "main"), "master"]:
        try:
            readme = _http_get(
                f"https://raw.githubusercontent.com/{owner_repo}/{branch}/README.md"
            ).decode("utf-8", "ignore")
            break
        except FetchError:
            continue
    return parse_github_repo(api, readme[:20000], owner_repo)


# ---------------------------------------------------------------------------
# Web articles
# ---------------------------------------------------------------------------

class _TextExtractor(HTMLParser):
    """Crude stdlib fallback when trafilatura is not installed."""

    SKIP = {"script", "style", "nav", "footer", "header", "aside"}

    def __init__(self):
        super().__init__()
        self.chunks: list[str] = []
        self.title = ""
        self._skip_depth = 0
        self._in_title = False

    def handle_starttag(self, tag, attrs):
        if tag in self.SKIP:
            self._skip_depth += 1
        if tag == "title":
            self._in_title = True

    def handle_endtag(self, tag):
        if tag in self.SKIP and self._skip_depth:
            self._skip_depth -= 1
        if tag == "title":
            self._in_title = False

    def handle_data(self, data):
        if self._in_title and not self.title:
            self.title = data.strip()
        elif not self._skip_depth:
            text = data.strip()
            if len(text) > 2:
                self.chunks.append(text)


def html_to_text(html: str) -> tuple[str, str]:
    """Returns (title, text). Pure function, fallback extractor."""
    parser = _TextExtractor()
    try:
        parser.feed(html)
    except Exception:
        pass
    return parser.title, "\n".join(parser.chunks)


def fetch_url(url: str) -> tuple[Source, str]:
    html = _http_get(url).decode("utf-8", "ignore")

    text = ""
    title = ""
    try:
        import trafilatura  # optional enhancement
        text = trafilatura.extract(html) or ""
        meta = trafilatura.extract_metadata(html)
        title = (meta.title if meta else "") or ""
    except ImportError:
        pass
    if not text:
        title_fb, text = html_to_text(html)
        title = title or title_fb

    source = Source(
        id=source_id_for("url", url),
        type="url",
        url=url,
        title=title or url,
        tags=["article"],
    )
    return source, text[:40000].replace("\x00", "")


# ---------------------------------------------------------------------------
# Local files
# ---------------------------------------------------------------------------

def fetch_file(path_str: str) -> tuple[Source, str]:
    path = Path(path_str).expanduser().resolve()
    if not path.exists():
        raise FetchError(f"file not found: {path}")

    if path.suffix.lower() == ".pdf":
        try:
            import fitz  # pymupdf, optional
            doc = fitz.open(str(path))
            text = "\n".join(page.get_text() for page in doc)
        except ImportError:
            raise FetchError("PDF ingestion needs pymupdf — pip install pymupdf")
    else:
        text = path.read_text(encoding="utf-8", errors="ignore")

    source = Source(
        id=source_id_for("file", str(path)),
        type="file",
        url=str(path),
        title=path.name,
        tags=["local"],
    )
    return source, text[:40000].replace("\x00", "")


# ---------------------------------------------------------------------------
# Dispatch
# ---------------------------------------------------------------------------

def fetch(ref: str) -> tuple[Source, str]:
    """Dispatch on a `type:value` reference (arxiv:, github:, url:, file:)."""
    kind, _, value = ref.partition(":")
    if kind == "arxiv" and value:
        return fetch_arxiv(value)
    if kind == "github" and value:
        return fetch_github(value)
    if kind == "url" and value:
        return fetch_url(value)
    if kind == "file" and value:
        return fetch_file(value)
    if ref.startswith(("http://", "https://")):
        return fetch_url(ref)
    raise FetchError(f"unrecognized reference: {ref!r} — use arxiv:ID, github:owner/repo, url:..., file:...")
