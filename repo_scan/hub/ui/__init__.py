"""The dashboard: one self-contained mobile-first HTML page.

No build step, no framework, no CDN — everything inline so it works on a
phone over Tailscale with zero external requests. ``DASHBOARD_HTML`` is the
template plus ``contract.js_contract_block()`` at ``/* __HUB_CONTRACT__ */``.
The page polls ``API_STATE`` and renders four tabs: Now (open-ticket summary,
stats, runs, agent feed), Gates, Tickets, Activity.

Ticket cards use three-tier disclosure (aligned with ``OPEN_STATUSES`` on the
Now tab and Tickets tab): glance row (``card.outcome``, ``card.why_line``,
status, priority, criteria count), tap-to-expand checklist (and inline
criteria editor when not ready), then full markdown via ``openDoc``.
"""

from ..contract import js_contract_block

from ._activity import _FRAGMENT as _activity
from ._css import _FRAGMENT as _css
from ._head import _FRAGMENT as _head
from ._now import _FRAGMENT as _now
from ._prs_gates import _FRAGMENT as _prs_gates
from ._runtime import _FRAGMENT as _runtime
from ._shell import _FRAGMENT as _shell
from ._tickets import _FRAGMENT as _tickets

_DASHBOARD_TEMPLATE = "".join(
    (_head, _css, _shell, _runtime, _now, _prs_gates, _tickets, _activity)
)

DASHBOARD_HTML = _DASHBOARD_TEMPLATE.replace(
    "/* __HUB_CONTRACT__ */", js_contract_block(),
)
