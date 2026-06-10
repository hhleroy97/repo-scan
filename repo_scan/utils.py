"""Shared helpers: subprocess, terminal output, git metadata."""

import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

# ---------------------------------------------------------------------------
# Terminal output helpers (no external deps)
# ---------------------------------------------------------------------------

RESET  = "\033[0m"
BOLD   = "\033[1m"
DIM    = "\033[2m"
GREEN  = "\033[32m"
YELLOW = "\033[33m"
RED    = "\033[31m"
CYAN   = "\033[36m"
WHITE  = "\033[37m"

def _supports_color() -> bool:
    return hasattr(sys.stdout, "isatty") and sys.stdout.isatty()

def fmt(text: str, *codes: str) -> str:
    if not _supports_color():
        return text
    return "".join(codes) + text + RESET

def info(msg: str):  print(fmt(f"  {msg}", DIM))
# Pictographs/emoji render as tofu boxes in many Obsidian/WSL font setups,
# so generated markdown must stay emoji-free. External text (GitHub repo
# descriptions etc.) is sanitized with this before it enters the docs.
_EMOJI_RE = re.compile(
    "["
    "\U0001F000-\U0001FAFF"   # pictographs, emoticons, symbols
    "\U00002600-\U000027BF"   # misc symbols + dingbats
    "\U0001F1E6-\U0001F1FF"   # regional indicators (flags)
    "\U00002B00-\U00002BFF"   # arrows/stars block (⭐ etc.)
    "\U0000FE00-\U0000FE0F"   # variation selectors
    "\U0000200D"              # zero-width joiner
    "]+"
)


def strip_emoji(text: str) -> str:
    return re.sub(r"  +", " ", _EMOJI_RE.sub("", text)).strip()


def ok(msg: str):    print(fmt(f"  ✓ {msg}", GREEN))
def warn(msg: str):  print(fmt(f"  ⚠ {msg}", YELLOW))
def err(msg: str):   print(fmt(f"  ✗ {msg}", RED))
def step(msg: str):  print(fmt(f"\n{msg}", BOLD))
def header(msg: str):
    bar = "─" * len(msg)
    print(fmt(f"\n{bar}\n{msg}\n{bar}", BOLD + CYAN))


# ---------------------------------------------------------------------------
# Subprocess + filesystem
# ---------------------------------------------------------------------------

def run(cmd: list[str], cwd: Path = None, timeout: int = 30) -> tuple[str, str, int]:
    try:
        result = subprocess.run(
            cmd, cwd=str(cwd) if cwd else None,
            capture_output=True, text=True, timeout=timeout,
        )
        return result.stdout or "", result.stderr or "", result.returncode
    except subprocess.TimeoutExpired:
        return "", "timeout", 1
    except Exception as e:
        return "", str(e), 1


def tool_available(name: str) -> bool:
    return subprocess.run(["which", name], capture_output=True).returncode == 0


def ensure_dirs(root: Path, cfg: dict):
    docs = root / cfg["docs_dir"]
    for d in ["reports", "architecture", "research"]:
        (docs / d).mkdir(parents=True, exist_ok=True)


def write_doc(path: Path, content: str, root: Path):
    path.write_text(content, encoding="utf-8")
    try:
        rel = path.relative_to(root)
    except ValueError:
        rel = path
    ok(str(rel))


def now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")


def now_date() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


# ---------------------------------------------------------------------------
# Git metadata
# ---------------------------------------------------------------------------

def git_root(path: Path) -> Path | None:
    out, _, code = run(["git", "rev-parse", "--show-toplevel"], cwd=path)
    return Path(out.strip()) if code == 0 else None


def git_remote_url(root: Path) -> str:
    out, _, code = run(["git", "remote", "get-url", "origin"], cwd=root)
    return out.strip() if code == 0 else "unknown"


def git_branch(root: Path) -> str:
    out, _, code = run(["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd=root)
    return out.strip() if code == 0 else "unknown"


def git_last_commit(root: Path) -> str:
    out, _, code = run(["git", "log", "-1", "--pretty=%h %s"], cwd=root)
    return out.strip() if code == 0 else "unknown"
