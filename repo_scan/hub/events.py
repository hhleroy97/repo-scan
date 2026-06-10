"""SSE fan-out for the mobile dashboard — stdlib only.

Subscribers get a queue per open ``/api/events`` connection. State changes
(append_event, run updates, gate decisions) call ``broadcast()`` so phones
refresh without waiting on the poll interval.
"""

import queue
import threading
from typing import Any

_LOCK = threading.Lock()
_SUBSCRIBERS: list[queue.Queue] = []


def subscribe() -> queue.Queue:
    """Register an SSE client; caller must ``unsubscribe`` when done."""
    q: queue.Queue = queue.Queue(maxsize=64)
    with _LOCK:
        _SUBSCRIBERS.append(q)
    return q


def unsubscribe(q: queue.Queue):
    with _LOCK:
        if q in _SUBSCRIBERS:
            _SUBSCRIBERS.remove(q)


def broadcast(event: dict[str, Any]):
    """Push one JSON event to every live SSE connection (non-blocking)."""
    with _LOCK:
        targets = list(_SUBSCRIBERS)
    for q in targets:
        try:
            q.put_nowait(event)
        except queue.Full:
            pass


def subscriber_count() -> int:
    with _LOCK:
        return len(_SUBSCRIBERS)
