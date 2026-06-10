"""Hub and daemon scheduler config keys and defaults.

Single source for hub-owned ``.repo-scan.json`` keys consumed by ``load_config``
and hub runtime (daemon, server, notifications). Radar/act/governance keys stay
in ``repo_scan.config.RADAR_CONFIG_KEYS``.

``serve_host`` asymmetry: ``server.cmd_serve`` binds ``0.0.0.0`` when the key
is absent; the daemon builds notification dashboard URLs only when
``serve_host`` is explicitly set — do not unify those behaviors via one default.
"""

HUB_CONFIG_KEYS = frozenset({
    "serve_host",
    "serve_port",
    "daemon_poll_seconds",
    "daemon_scan_hours",
    "ntfy_topic",
    "ntfy_server",
    "dashboard_url",
    "vault_autocommit",
    "max_parallel_acts",
    "max_parallel_loops",
})

HUB_DEFAULTS: dict = {
    "serve_port": 8800,
    "daemon_poll_seconds": 20,
    "daemon_scan_hours": 6,
    "ntfy_server": "https://ntfy.sh",
    "vault_autocommit": True,
    "max_parallel_acts": 2,
    "max_parallel_loops": 2,
}


def cfg_hub(cfg: dict, key: str):
    """Return a hub config value, falling back to ``HUB_DEFAULTS`` when absent."""
    return cfg.get(key, HUB_DEFAULTS.get(key))
