"""Stdlib HTTP server for the mobile dashboard.

Single user, low traffic: ThreadingHTTPServer is plenty, and it keeps the
runtime zero-dependency. Reads come straight from the vault; writes go
through the same decision inbox and ticket APIs the CLI uses, so the
dashboard is just another surface — never a second source of truth.

Auth is a per-repo bearer token (docs/<docs_dir>/.radar/token). Pair with
Tailscale (or any private network) for remote access; do not expose this
server to the open internet.
"""

import json
import queue
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

SSE_HEARTBEAT_SECONDS = 15

from ..config import VERSION
from ..utils import git_branch, header, info, ok
from .contract import (
    API_DOC,
    API_EVENTS,
    API_GATE,
    API_PR_PREFIX,
    API_STATE,
    API_TICKET,
    API_TICKET_NEW,
    HubState,
    TICKET_ACTION_STATUSES,
)
from .settings import cfg_hub
from .state import get_token, load_events, load_runs, submit_decision
from .ui import DASHBOARD_HTML

ACTIVITY_ROWS = 10

# changes on every server start; the dashboard reloads itself when it sees a
# new value, so phones never run stale JS after a hub restart
BOOT_ID = str(int(time.time()))


def _read_json(root: Path, rel: str) -> dict:
    path = root / rel
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def build_state(root: Path, cfg: dict) -> HubState:
    """Everything the dashboard renders, in one payload (see ``HubState``)."""
    from ..tickets import load_tickets
    docs = root / cfg["docs_dir"]

    scan = _read_json(root, f"{cfg['docs_dir']}/scan.json")
    summary = {}
    if scan:
        files = scan.get("files", {})
        summary = {
            "generated_at": scan.get("generated_at"),
            "files": len(files),
            "lines": sum(s.get("lines", 0) for s in files.values()),
            "hotspots": len(scan.get("complexity", [])),
            "critical": sum(1 for s in files.values()
                            if s.get("lines", 0) >= cfg.get("line_crit", 600)),
            "languages": scan.get("languages", {}),
        }

    gates = []
    pending = docs / "research" / "pending"
    if pending.exists():
        for path in sorted(pending.glob("*.json")):
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                continue
            payload = data.get("payload", {})
            gates.append({
                "gate": data.get("gate"),
                "written_at": data.get("written_at"),
                "summary": payload.get("summary", ""),
                "problem": payload.get("problem", ""),
                "detail": payload.get("detail", {}),
            })

    tickets = []
    for t in load_tickets(root, cfg):
        row = {k: t.get(k) for k in ("id", "status", "title", "priority", "why",
                                      "criteria", "criteria_checked", "criteria_count",
                                      "criteria_ready", "criteria_summary")}
        row["card"] = t.get("card", {})
        row["doc"] = f"tickets/{t['id']}.md"
        # kind lives in the fingerprint prefix, e.g. "refactor:path/to/file"
        row["kind"] = str(t.get("fingerprint", "")).split(":", 1)[0] or None
        tickets.append(row)

    from .gate_drawer import enrich_gate
    gates = [enrich_gate(root, cfg, g, tickets) for g in gates]

    activity = []
    decisions = docs / "research" / "decisions.md"
    if decisions.exists():
        rows = [l for l in decisions.read_text(encoding="utf-8").splitlines()
                if l.startswith("|") and "---" not in l][1:]
        for row in rows[-ACTIVITY_ROWS:][::-1]:
            cells = [c.strip() for c in row.strip("|").split("|")]
            if len(cells) >= 4:
                activity.append({"when": cells[0], "gate": cells[1],
                                 "decision": cells[2], "summary": cells[3]})

    from ..radar.llm import usage_summary
    from .prs import list_open_prs
    from .state import active_runs
    all_runs = load_runs(root, cfg)[::-1]
    live = [{k: r.get(k) for k in ("id", "problem", "ticket", "kind", "status",
                                    "stage", "stage_detail", "gate", "updated_at")}
            for r in active_runs(root, cfg)]
    return {
        "version": VERSION,
        "boot": BOOT_ID,
        "repo": {"name": root.name, "branch": git_branch(root)},
        "now": time.strftime("%Y-%m-%d %H:%M UTC", time.gmtime()),
        "scan": summary,
        "gates": gates,
        "tickets": tickets,
        "runs": all_runs[:10],
        "live_runs": live,
        "activity": activity,
        "events": load_events(root, cfg, limit=15)[::-1],
        "usage": usage_summary(root, cfg),
        "prs": list_open_prs(root, cfg),
    }


def _safe_doc(root: Path, cfg: dict, rel: str) -> str | None:
    """Read a markdown doc strictly inside the docs dir."""
    docs = (root / cfg["docs_dir"]).resolve()
    target = (docs / rel).resolve()
    if not str(target).startswith(str(docs) + "/") or target.suffix != ".md":
        return None
    if not target.exists():
        return None
    return target.read_text(encoding="utf-8", errors="ignore")


def make_handler(root: Path, cfg: dict, token: str):
    class Handler(BaseHTTPRequestHandler):
        server_version = f"repo-scan-hub/{VERSION}"

        def log_message(self, fmt, *args):  # keep the terminal quiet
            pass

        # --- plumbing ---------------------------------------------------
        def _authed(self) -> bool:
            q = parse_qs(urlparse(self.path).query)
            if q.get("token", [None])[0] == token:
                return True
            if self.headers.get("X-Radar-Token") == token:
                return True
            cookies = self.headers.get("Cookie", "")
            return f"radar_token={token}" in cookies

        def _send(self, code: int, body: bytes, ctype: str,
                  extra: dict | None = None):
            self.send_response(code)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            for k, v in (extra or {}).items():
                self.send_header(k, v)
            self.end_headers()
            self.wfile.write(body)

        def _json(self, data: dict, code: int = 200, extra: dict | None = None):
            self._send(code, json.dumps(data).encode("utf-8"),
                       "application/json; charset=utf-8", extra)

        def _deny(self):
            self._json({"error": "unauthorized"}, 401)

        def _sse_write(self, chunk: bytes):
            self.wfile.write(chunk)
            self.wfile.flush()

        def _sse_events(self):
            """Stream hub changes as Server-Sent Events (stdlib, no deps)."""
            from .events import subscribe, unsubscribe

            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream; charset=utf-8")
            self.send_header("Cache-Control", "no-cache")
            self.send_header("Connection", "keep-alive")
            self.end_headers()
            q = subscribe()
            try:
                self._sse_write(
                    f"data: {json.dumps({'type': 'connected', 'boot': BOOT_ID})}\n\n"
                    .encode("utf-8"))
                while True:
                    try:
                        event = q.get(timeout=SSE_HEARTBEAT_SECONDS)
                        self._sse_write(
                            f"data: {json.dumps(event, separators=(',', ':'))}\n\n"
                            .encode("utf-8"))
                    except queue.Empty:
                        self._sse_write(b": heartbeat\n\n")
            except (BrokenPipeError, ConnectionResetError, OSError):
                pass
            finally:
                unsubscribe(q)

        # --- routes -----------------------------------------------------
        def do_GET(self):
            url = urlparse(self.path)
            if not self._authed():
                return self._deny()

            if url.path == "/":
                # landing via ?token=... sets the cookie so links stay clean
                extra = {}
                q = parse_qs(url.query)
                if q.get("token", [None])[0] == token:
                    extra["Set-Cookie"] = (f"radar_token={token}; Path=/; "
                                           "HttpOnly; SameSite=Strict; Max-Age=31536000")
                return self._send(200, DASHBOARD_HTML.encode("utf-8"),
                                  "text/html; charset=utf-8", extra)

            if url.path == API_STATE:
                return self._json(build_state(root, cfg))

            if url.path == API_EVENTS:
                return self._sse_events()

            if url.path == API_DOC:
                rel = parse_qs(url.query).get("path", [""])[0]
                text = _safe_doc(root, cfg, rel)
                if text is None:
                    return self._json({"error": "not found"}, 404)
                return self._json({"path": rel, "text": text})

            self._json({"error": "not found"}, 404)

        def do_POST(self):
            if not self._authed():
                return self._deny()
            length = int(self.headers.get("Content-Length", 0) or 0)
            try:
                body = json.loads(self.rfile.read(length) or b"{}")
            except json.JSONDecodeError:
                return self._json({"error": "bad json"}, 400)
            url = urlparse(self.path)

            if url.path == API_GATE:
                gate = str(body.get("gate", ""))
                problem = str(body.get("problem", ""))
                decision = str(body.get("decision", ""))
                comment = str(body.get("comment", ""))[:500]
                if not (gate and problem and decision in ("approve", "reject")):
                    return self._json({"error": "gate, problem, decision required"}, 400)
                submit_decision(root, cfg, gate, problem, decision,
                                comment=comment, source="dashboard")
                return self._json({"ok": True})

            if url.path == f"{API_PR_PREFIX}merge":
                from .prs import merge_pr
                try:
                    number = int(body.get("number", 0))
                except (TypeError, ValueError):
                    number = 0
                if not number:
                    return self._json({"error": "number required"}, 400)
                done, msg = merge_pr(root, cfg, number)
                return self._json({"ok": done, "message": msg},
                                  200 if done else 502)

            if url.path == f"{API_PR_PREFIX}update":
                from .prs import remediate_pr
                try:
                    number = int(body.get("number", 0))
                except (TypeError, ValueError):
                    number = 0
                if not number:
                    return self._json({"error": "number required"}, 400)
                result = remediate_pr(root, cfg, number)
                # always 200 when we have a body — ok means merge-ready, not
                # request failure; the phone needs diagnosis either way
                return self._json(result, 200 if result.get("diagnosis") is not None
                                  or result.get("message") else 502)

            if url.path == API_TICKET_NEW:
                from ..tickets import new_ticket
                title = str(body.get("title", "")).strip()
                if not title:
                    return self._json({"error": "title required"}, 400)
                criteria = [str(c).strip() for c in body.get("criteria", [])
                            if str(c).strip()]
                try:
                    t = new_ticket(
                        root, cfg, title,
                        why=str(body.get("why", ""))[:2000],
                        priority=str(body.get("priority", "medium")),
                        criteria=criteria,
                        kind=str(body.get("kind", "feature"))[:30] or "feature")
                except ValueError as e:
                    return self._json({"error": str(e)[:200]}, 400)
                return self._json({"ok": True, "id": t["id"], "status": t["status"]})

            if url.path == API_TICKET:
                from ..tickets import load_tickets, set_ticket_status
                tid = str(body.get("id", ""))
                action = str(body.get("action", ""))
                if not (tid and action in TICKET_ACTION_STATUSES):
                    return self._json({"error": "id and valid action required"}, 400)
                if action == "approve":
                    ticket = next((t for t in load_tickets(root, cfg)
                                   if t["id"] == tid), None)
                    if ticket and not ticket.get("criteria_ready"):
                        return self._json(
                            {"error": "acceptance criteria required before approving"}, 400)
                try:
                    set_ticket_status(root, cfg, tid, TICKET_ACTION_STATUSES[action])
                except Exception as e:
                    return self._json({"error": str(e)[:200]}, 400)
                return self._json({"ok": True})

            self._json({"error": "not found"}, 404)

        def do_PATCH(self):
            if not self._authed():
                return self._deny()
            length = int(self.headers.get("Content-Length", 0) or 0)
            try:
                body = json.loads(self.rfile.read(length) or b"{}")
            except json.JSONDecodeError:
                return self._json({"error": "bad json"}, 400)
            url = urlparse(self.path)

            if url.path == API_TICKET:
                from ..tickets import update_ticket_criteria
                tid = str(body.get("id", ""))
                raw = body.get("criteria")
                if not tid or not isinstance(raw, list):
                    return self._json({"error": "id and criteria list required"}, 400)
                criteria = [str(c).strip() for c in raw if str(c).strip()]
                try:
                    ticket = update_ticket_criteria(root, cfg, tid, criteria)
                except Exception as e:
                    return self._json({"error": str(e)[:200]}, 400)
                return self._json({
                    "ok": True,
                    "criteria_ready": ticket.get("criteria_ready"),
                    "criteria_count": ticket.get("criteria_count"),
                })

            self._json({"error": "not found"}, 404)

    return Handler


def cmd_serve(root: Path, cfg: dict, host: str | None = None,
              port: int | None = None, with_daemon: bool = True) -> int:
    header("radar serve")
    host = host or str(cfg.get("serve_host", "0.0.0.0"))
    port = int(port or cfg_hub(cfg, "serve_port"))
    token = get_token(root, cfg)

    if with_daemon:
        from .daemon import cmd_daemon
        t = threading.Thread(target=cmd_daemon, args=(root, cfg), daemon=True)
        t.start()
        info("daemon thread running (scans, loops, gate resume)")

    httpd = ThreadingHTTPServer((host, port), make_handler(root, cfg, token))
    shown = "localhost" if host in ("0.0.0.0", "::") else host
    ok(f"dashboard: http://{shown}:{port}/?token={token}")
    info("on Tailscale, replace the host with this machine's tailnet name/IP")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        info("server stopped")
    return 0
