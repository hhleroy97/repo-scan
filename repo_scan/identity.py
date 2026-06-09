"""Repo identity: manifests, entry points, README summary, directory tree."""

import json
from pathlib import Path

KNOWN_MANIFESTS = [
    "pyproject.toml", "setup.py", "requirements.txt", "package.json",
    "Cargo.toml", "go.mod", "Makefile", "CMakeLists.txt", "Dockerfile",
    "docker-compose.yml", "Gemfile", "composer.json",
]


def detect_manifests(root: Path) -> list[str]:
    return [m for m in KNOWN_MANIFESTS if (root / m).exists()]


def detect_entry_points(root: Path) -> list[str]:
    """Best-effort entry points from common manifests. No parsing deps."""
    entries: list[str] = []

    pyproject = root / "pyproject.toml"
    if pyproject.exists():
        in_scripts = False
        for line in pyproject.read_text(errors="ignore").splitlines():
            stripped = line.strip()
            if stripped.startswith("["):
                in_scripts = stripped == "[project.scripts]"
                continue
            if in_scripts and "=" in stripped:
                name, _, target = stripped.partition("=")
                entries.append(f"`{name.strip()}` → {target.strip().strip(chr(34))} (pyproject)")

    pkg_json = root / "package.json"
    if pkg_json.exists():
        try:
            data = json.loads(pkg_json.read_text(errors="ignore"))
            if isinstance(data.get("main"), str):
                entries.append(f"`{data['main']}` (package.json main)")
            bins = data.get("bin")
            if isinstance(bins, str):
                entries.append(f"`{bins}` (package.json bin)")
            elif isinstance(bins, dict):
                for name, target in bins.items():
                    entries.append(f"`{name}` → {target} (package.json bin)")
        except json.JSONDecodeError:
            pass

    for candidate in ["main.py", "app.py", "manage.py", "main.go", "src/main.rs", "src/index.ts", "index.js"]:
        if (root / candidate).exists():
            entries.append(f"`{candidate}` (convention)")

    return entries


def readme_summary(root: Path, max_chars: int = 280) -> str:
    for name in ["README.md", "README.rst", "README.txt", "README"]:
        readme = root / name
        if not readme.exists():
            continue
        for block in readme.read_text(errors="ignore").split("\n\n"):
            text = " ".join(
                line.strip() for line in block.splitlines()
                if line.strip() and not line.strip().startswith(("#", "!", "[", "<", "---", "```"))
            )
            if len(text) > 40:
                return text[:max_chars] + ("…" if len(text) > max_chars else "")
    return ""


def get_directory_tree(root: Path, cfg: dict, max_entries: int = 150) -> str:
    """Depth-capped ASCII tree honoring exclude_dirs."""
    skip = set(cfg["exclude_dirs"])
    max_depth = cfg.get("tree_depth", 3)
    lines = [root.name + "/"]
    count = 0

    def walk(d: Path, prefix: str, depth: int):
        nonlocal count
        if depth > max_depth or count >= max_entries:
            return
        try:
            entries = sorted(d.iterdir(), key=lambda p: (p.is_file(), p.name.lower()))
        except OSError:
            return
        entries = [e for e in entries if e.name not in skip and not (e.name.startswith(".") and e.name not in {".repo-scan.json", ".gitignore"})]
        for i, e in enumerate(entries):
            if count >= max_entries:
                lines.append(prefix + "└── …")
                return
            last = i == len(entries) - 1
            lines.append(f"{prefix}{'└── ' if last else '├── '}{e.name}{'/' if e.is_dir() else ''}")
            count += 1
            if e.is_dir():
                walk(e, prefix + ("    " if last else "│   "), depth + 1)

    walk(root, "", 1)
    return "\n".join(lines)
