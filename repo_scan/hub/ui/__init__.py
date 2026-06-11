"""The dashboard: one self-contained mobile-first HTML page.

No build step, no framework, no CDN — everything inline so it works on a
phone over Tailscale with zero external requests. ``DASHBOARD_HTML`` is the
template plus ``contract.js_contract_block()`` at ``/* __HUB_CONTRACT__ */``.

Vault: docs/tickets/tkt-0023, docs/tickets/tkt-0025
Vault: docs/research/analysis/2026-06-10-split-repo-scan-hub-ui-py-706-lines-repo-analysis
Vault: docs/research/analysis/2026-06-10-add-a-list-for-the-open-tickets-to-the-n-analysis
Vault: docs/research/sources/arxiv-2605.02741
Spec:  docs/specs/2026-06-10-split-repo-scan-hub-ui-py-706-lines-repo-spec
Spec:  docs/specs/2026-06-10-add-a-list-for-the-open-tickets-to-the-n-spec
The page polls ``API_STATE`` and renders five tabs: Now (open-ticket summary,
stats, runs, agent feed), Gates, Tickets, Activity, Dashboard (vault audit,
then graph controls — miss filters, layer tabs, zoom toolbar — tight with the
provenance canvas and legend, then context panels below — agentic loop,
untracked queue, and provenance tools).

Ticket cards use three-tier disclosure (aligned with ``OPEN_STATUSES`` on the
Now tab and Tickets tab): glance row (``card.outcome``, ``card.why_line``,
status, priority, criteria count), tap-to-expand checklist (and inline
criteria editor when not ready), then full markdown via ``openDoc``.
"""

from ..contract import js_contract_block

from ._activity import _FRAGMENT as _activity
from ._css import _FRAGMENT as _css
from ._graph_dashboard import _FRAGMENT as _graph_dashboard
from ._graph_loop import _FRAGMENT as _graph_loop
from ._graph import _FRAGMENT as _graph
from ._graph_events import _FRAGMENT as _graph_events
from ._graph_sim import _FRAGMENT as _graph_sim
from ._graph_views import _FRAGMENT as _graph_views
from ._graph_views2 import _FRAGMENT as _graph_views2
from ._graph_chain import _FRAGMENT as _graph_chain
from ._head import _FRAGMENT as _head
from ._now import _FRAGMENT as _now
from ._prs_gates import _FRAGMENT as _prs_gates
from ._runtime import _FRAGMENT as _runtime
from ._shell import _FRAGMENT as _shell
from ._tickets import _FRAGMENT as _tickets

_DASHBOARD_TEMPLATE = "".join(
    (_head, _css, _shell, _runtime, _now, _prs_gates, _tickets,
     _graph_dashboard, _graph_loop, _graph, _graph_events, _graph_sim,
     _graph_views, _graph_views2, _graph_chain, _activity)
)

DASHBOARD_HTML = _DASHBOARD_TEMPLATE.replace(
    "/* __HUB_CONTRACT__ */", js_contract_block(),
)
