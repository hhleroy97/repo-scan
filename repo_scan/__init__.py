"""repo-scan — repo intelligence tool.

Public API re-exported from the module structure so existing imports
(`import repo_scan; repo_scan.scan(...)`) and the `repo_scan:main` console
entry point keep working after the A2 monolith split.
"""

from .churn import get_git_churn
from .cli import check_deps, main
from .complexity import get_python_complexity
from .config import DEFAULT_CONFIG, VERSION, load_config, write_default_config
from .digest import write_digest
from .graphs import (
    edges_to_mermaid,
    get_c_call_graph_mermaid,
    get_python_dep_edges,
    get_python_dep_graph_mermaid,
    get_ts_dep_edges,
)
from .handoff import write_handoff
from .hooks import HOOK_SCRIPT, install_hook
from .identity import (
    KNOWN_MANIFESTS,
    detect_entry_points,
    detect_manifests,
    get_directory_tree,
    readme_summary,
)
from .languages import (
    C_EXTENSIONS,
    PY_EXTENSIONS,
    TS_EXTENSIONS,
    detect_languages,
    get_line_counts,
)
from .ranking import rank_files
from .scanner import scan
from .utils import (
    ensure_dirs,
    err,
    git_branch,
    git_last_commit,
    git_remote_url,
    git_root,
    info,
    now_date,
    now_iso,
    ok,
    run,
    step,
    tool_available,
    warn,
    write_doc,
)
from .writers import (
    AGENTS_TEMPLATE,
    write_agents_md,
    write_call_report,
    write_candidates,
    write_dep_report,
    write_health_report,
    write_index,
    write_scan_json,
)

__version__ = VERSION
