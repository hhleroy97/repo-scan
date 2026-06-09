"""RADAR — research-to-implementation loop layered on the repo-scan docs/ base.

Pipeline: Research → Analyze → Gate 1 → Draft → Audit → Gate 2 → Record.
"""

from .sources import Source, source_id_for, write_source, rebuild_research_index
