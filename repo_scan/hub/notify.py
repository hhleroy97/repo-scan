"""Best-effort push notifications via ntfy (https://ntfy.sh).

Opt-in: set "ntfy_topic" in .repo-scan.json (pick a long random topic name —
it is effectively the password). Self-hosters can point "ntfy_server"
elsewhere. Failures never break the loop; notifications are a luxury.
"""

import json
import urllib.request

from ..utils import info


def notify(cfg: dict, title: str, message: str, priority: str = "default",
           tags: list[str] | None = None, click: str | None = None) -> bool:
    topic = cfg.get("ntfy_topic")
    if not topic:
        return False
    server = str(cfg.get("ntfy_server", "https://ntfy.sh")).rstrip("/")
    body = {
        "topic": topic,
        "title": title,
        "message": message,
        "priority": {"default": 3, "high": 4, "low": 2}.get(priority, 3),
    }
    if tags:
        body["tags"] = tags
    if click:
        body["click"] = click
    data = json.dumps(body).encode("utf-8")
    last_err = None
    for attempt in (1, 2):  # one retry: transient TLS/connect hiccups are common
        try:
            req = urllib.request.Request(
                server, data=data,
                headers={"Content-Type": "application/json"}, method="POST",
            )
            with urllib.request.urlopen(req, timeout=10) as resp:
                return 200 <= resp.status < 300
        except Exception as e:
            last_err = e
    info(f"ntfy notification failed (ignored): {last_err}")
    return False
