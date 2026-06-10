---
id: "url-githits-sse-stdlib-dashboard"
type: "url"
url: "https://app.githits.com/solutions/f294544e-72ac-4c89-a9a4-3f2391b43344"
raw_url: "https://github.com/tinygrad/tinygrad/blob/master/tinygrad/viz/serve.py"
tags: ["sse", "stdlib", "dashboard", "live-updates", "hub", "deferred"]
linked_files: ["repo_scan/hub/server.py", "repo_scan/hub/ui.py"]
relevance: "Reference for Phase 3 SSE on the hub — Phase 1 uses enhanced polling + stage_detail first; this pattern shows ThreadingHTTPServer + /events stream + EventSource client without new dependencies."
ingested_at: "2026-06-10 16:00 UTC"
---

# GitHits — Python stdlib SSE live dashboard

## Summary

GitHits example: `ThreadingHTTPServer` serves HTML dashboard and `/events` SSE endpoint; background thread pushes JSON into a `queue.Queue`; clients use `EventSource` with heartbeat comments on timeout. Fits repo-scan's **no new dependencies** constraint for `radar serve`. **Deferred to Phase 3** — Phase 1 improves Now tab with existing `/api/state` fields first.

## Key claims

- `text/event-stream` + `data: {json}\n\n` + flush per event.
- Heartbeat `: comment\n\n` keeps connections alive through proxies.
- `ThreadingHTTPServer` handles concurrent SSE + API clients.
- Client reconnect on `onerror` is standard browser behavior.

## GitHits provenance

- `get_example` query: "Python stdlib HTTP server Server-Sent Events SSE live dashboard push updates"
- solution_id: `f294544e-72ac-4c89-a9a4-3f2391b43344`
- References: tinygrad/viz/serve.py, ai-engineering-from-scratch MCP transports, dayna_ss/ui/sse_server.py (MIT)

## Notes

_yours to annotate — Phase 3: fan out `append_event` / gate decisions to SSE subscribers; Phase 1: 3s poll when runs active._
