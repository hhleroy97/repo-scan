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
    "repo_snapshot_max_chars": 2500,
    # behavioral analysis (change coupling / ownership / age)
    "coupling_min_shared": 4,
    "coupling_min_degree": 50,
    "coupling_max_changeset": 30,
    "silo_min_share": 0.9,
    "stale_days": 180,
    # auto-generated tickets
    "tickets_enabled": True,
    "tickets_max_new_per_scan": 5,
    "ticket_diagrams_enabled": True,
    "diagram_max_coupling_edges": 20,
    "diagram_max_ticket_neighbors": 4,
}

# Keys owned by radar (B-phases) — valid in .repo-scan.json, unused by scan.
RADAR_CONFIG_KEYS = {
    "gates", "llm_cli", "llm_timeout", "llm_heartbeat_seconds",
    # hub (daemon + dashboard)
    "serve_host", "serve_port", "daemon_poll_seconds", "daemon_scan_hours",
    "ntfy_topic", "ntfy_server", "dashboard_url",
    # act stage (spec implementation)
    "act_enabled", "act_timeout", "act_fix_rounds", "test_cmd", "test_timeout",
    # model routing + parallelism
    "llm_roles", "max_parallel_acts", "max_parallel_loops",
    "repo_snapshot_max_chars",
    # PR workflow
    "act_open_pr", "pr_auto_remediate",
    # governance: budgets, path policy, per-kind autonomy, acceptance tests
    "budget_daily_tokens", "max_acts_per_day", "protected_paths",
    "gates_by_kind", "require_tests_for_kinds",
    # vault auto-commit after runs/scans (default on)
    "vault_autocommit",
}


def load_config(root: Path) -> dict:
    cfg = DEFAULT_CONFIG.copy()
    # .repo-scan.local.json: machine-private overrides (ntfy topic, hosts)
    # that must never be committed — merged after the shared config
    for name in (".repo-scan.json", ".repo-scan.local.json"):
        config_file = root / name
        if not config_file.exists():
            continue
        try:
            overrides = json.loads(config_file.read_text())
            unknown = set(overrides) - set(DEFAULT_CONFIG) - RADAR_CONFIG_KEYS
            if unknown:
                warn(f"{name} unknown keys ignored by scan: {', '.join(sorted(unknown))}")
            cfg.update(overrides)
        except json.JSONDecodeError as e:
            warn(f"{name} parse error: {e} — ignoring it")
    return cfg


def write_default_config(root: Path):
    config_file = root / ".repo-scan.json"
    if config_file.exists():
        print(f"  .repo-scan.json already exists, skipping")
        return
    config_file.write_text(json.dumps(DEFAULT_CONFIG, indent=2) + "\n")
    print(f"  wrote .repo-scan.json — edit thresholds and excluded dirs as needed")
