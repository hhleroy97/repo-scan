"""Defaults and .repo-scan.json loading.

Hub/daemon keys and defaults live in ``repo_scan.hub.settings`` (imported
below); they are merged into ``DEFAULT_CONFIG`` and validated separately from
``RADAR_CONFIG_KEYS``.

Vault: docs/tickets/tkt-0016, docs/tickets/tkt-0020, docs/tickets/tkt-0024
Vault: docs/research/analysis/2026-06-10-hidden-seam-repo-scan-config-py-repo-sca-analysis
Vault: docs/research/analysis/2026-06-10-hidden-seam-pyproject-toml-setup-py-100-analysis
Vault: docs/research/sources/url-wiki-apidesign-org-wiki-configurationobject
Vault: docs/research/sources/url-packaging-python-org-en-latest-guides-modernize-setup-py-pro
Vault: docs/research/sources/url-packaging-python-org-en-latest-discussions-single-source-ver
Vault: docs/research/sources/gh-pypa-sampleproject
Spec:  docs/specs/2026-06-10-hidden-seam-repo-scan-config-py-repo-sca-spec
Spec:  docs/specs/2026-06-10-hidden-seam-pyproject-toml-setup-py-100-spec
"""

import json
from pathlib import Path

from .hub.settings import HUB_CONFIG_KEYS, HUB_DEFAULTS
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
DEFAULT_CONFIG.update(HUB_DEFAULTS)

# Keys owned by radar (B-phases) — valid in .repo-scan.json, unused by scan.
_RADAR_CONFIG_KEYS = {
    "gates", "llm_cli", "llm_timeout", "llm_heartbeat_seconds",
    # act stage (spec implementation)
    "act_enabled", "act_timeout", "act_fix_rounds", "test_cmd", "test_timeout",
    # model routing + parallelism
    "llm_roles", "repo_snapshot_max_chars",
    # PR workflow
    "act_open_pr", "pr_auto_remediate",
    # governance: budgets, path policy, per-kind autonomy, acceptance tests
    "budget_daily_tokens", "max_acts_per_day", "protected_paths",
    "gates_by_kind", "require_tests_for_kinds",
}
RADAR_CONFIG_KEYS = _RADAR_CONFIG_KEYS - HUB_CONFIG_KEYS


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
            known = set(DEFAULT_CONFIG) | RADAR_CONFIG_KEYS | HUB_CONFIG_KEYS
            unknown = set(overrides) - known
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
