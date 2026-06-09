"""Defaults and .repo-scan.json loading."""

import json
from pathlib import Path

from .utils import warn

VERSION = "0.2.0"

DEFAULT_CONFIG = {
    "line_warn": 300,
    "line_crit": 600,
    "complexity_min_rank": "C",
    "churn_top_n": 20,
    "exclude_dirs": [
        "node_modules", ".git", "__pycache__", ".venv", "venv",
        "dist", "build", ".next", "target", ".mypy_cache",
        ".pytest_cache", "coverage", ".turbo", "out"
    ],
    "docs_dir": "docs",
    "radar_enabled": False,
    "tree_depth": 3,
    "rank_top_n": 15,
    "digest_tokens": 4000,
}

# Keys owned by radar (B-phases) — valid in .repo-scan.json, unused by scan.
RADAR_CONFIG_KEYS = {"gates", "llm_cli"}


def load_config(root: Path) -> dict:
    cfg = DEFAULT_CONFIG.copy()
    config_file = root / ".repo-scan.json"
    if config_file.exists():
        try:
            overrides = json.loads(config_file.read_text())
            unknown = set(overrides) - set(DEFAULT_CONFIG) - RADAR_CONFIG_KEYS
            if unknown:
                warn(f".repo-scan.json unknown keys ignored by scan: {', '.join(sorted(unknown))}")
            cfg.update(overrides)
        except json.JSONDecodeError as e:
            warn(f".repo-scan.json parse error: {e} — using defaults")
    return cfg


def write_default_config(root: Path):
    config_file = root / ".repo-scan.json"
    if config_file.exists():
        print(f"  .repo-scan.json already exists, skipping")
        return
    config_file.write_text(json.dumps(DEFAULT_CONFIG, indent=2) + "\n")
    print(f"  wrote .repo-scan.json — edit thresholds and excluded dirs as needed")
