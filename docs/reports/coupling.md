# Change coupling
_Generated 2026-06-11 15:13 UTC_

Files that change together (≥4 shared commits, ≥50% degree).
Coupled pairs **without** an import edge are hidden seams — an implicit
contract the dependency graph can't see.

```mermaid
graph TD
  repo_scan_config_py["config.py"]
  repo_scan_graphs_py["graphs.py"]
  repo_scan_hub_daemon_py["daemon.py"]
  repo_scan_hub_prs_py["prs.py"]
  repo_scan_hub_server_py["server.py"]
  repo_scan_hub_state_py["state.py"]
  repo_scan_languages_py["languages.py"]
  repo_scan_radar_act_py["act.py"]
  repo_scan_radar_cli_py["cli.py"]
  repo_scan_radar_gates_py["gates.py"]
  repo_scan_radar_llm_py["llm.py"]
  repo_scan_radar_pipeline_py["pipeline.py"]
  repo_scan_radar_research_py["research.py"]
  repo_scan_radar_sources_py["sources.py"]
  repo_scan_scanner_py["scanner.py"]
  repo_scan_writers_py["writers.py"]
  tests_test_act_py["test_act.py"]
  tests_test_prs_py["test_prs.py"]
  tests_test_radar_pipeline_py["test_radar_pipeli…"]
  repo_scan_hub_prs_py --> tests_test_prs_py
  repo_scan_radar_cli_py --> repo_scan_radar_gates_py
  repo_scan_graphs_py --> repo_scan_languages_py
  repo_scan_radar_pipeline_py --> tests_test_radar_pipeline_py
  repo_scan_scanner_py --> repo_scan_writers_py
  repo_scan_hub_daemon_py --> tests_test_act_py
  repo_scan_radar_pipeline_py --> repo_scan_radar_research_py
  repo_scan_graphs_py --> repo_scan_scanner_py
  repo_scan_config_py --> repo_scan_hub_daemon_py
  repo_scan_radar_gates_py --> repo_scan_radar_pipeline_py
  repo_scan_radar_gates_py --> tests_test_radar_pipeline_py
  repo_scan_graphs_py --> repo_scan_writers_py
  repo_scan_radar_act_py --> repo_scan_radar_gates_py
  repo_scan_radar_research_py --> repo_scan_radar_sources_py
  repo_scan_hub_state_py --> repo_scan_radar_gates_py
  repo_scan_hub_server_py --> repo_scan_hub_state_py
  repo_scan_radar_act_py --> repo_scan_radar_llm_py
  repo_scan_radar_act_py --> tests_test_act_py
  repo_scan_hub_state_py --> repo_scan_radar_act_py
  repo_scan_hub_state_py --> repo_scan_radar_llm_py
linkStyle 0 stroke:#95a5a6,stroke-width:1px
linkStyle 1 stroke:#95a5a6,stroke-width:1px
linkStyle 2 stroke:#c0392b,stroke-width:2px,stroke-dasharray: 5 5
linkStyle 3 stroke:#95a5a6,stroke-width:1px
linkStyle 4 stroke:#95a5a6,stroke-width:1px
linkStyle 5 stroke:#c0392b,stroke-width:2px,stroke-dasharray: 5 5
linkStyle 6 stroke:#95a5a6,stroke-width:1px
linkStyle 7 stroke:#95a5a6,stroke-width:1px
linkStyle 8 stroke:#c0392b,stroke-width:2px,stroke-dasharray: 5 5
linkStyle 9 stroke:#95a5a6,stroke-width:1px
linkStyle 10 stroke:#c0392b,stroke-width:2px,stroke-dasharray: 5 5
linkStyle 11 stroke:#95a5a6,stroke-width:1px
linkStyle 12 stroke:#95a5a6,stroke-width:1px
linkStyle 13 stroke:#95a5a6,stroke-width:1px
linkStyle 14 stroke:#95a5a6,stroke-width:1px
linkStyle 15 stroke:#95a5a6,stroke-width:1px
linkStyle 16 stroke:#95a5a6,stroke-width:1px
linkStyle 17 stroke:#95a5a6,stroke-width:1px
linkStyle 18 stroke:#95a5a6,stroke-width:1px
linkStyle 19 stroke:#95a5a6,stroke-width:1px
```

> [!warning] 4 hidden seam(s): coupled in history, no import edge
> - `repo_scan/graphs.py` ↔ `repo_scan/languages.py` (77% over 5 commits)
> - `repo_scan/hub/daemon.py` ↔ `tests/test_act.py` (62% over 8 commits)
> - `repo_scan/config.py` ↔ `repo_scan/hub/daemon.py` (57% over 10 commits)
> - `repo_scan/radar/gates.py` ↔ `tests/test_radar_pipeline.py` (56% over 5 commits)

| File A | File B | Shared commits | Degree | Import edge |
|--------|--------|----------------|--------|-------------|
| `repo_scan/hub/prs.py` | `tests/test_prs.py` | 4 | 89% | yes |
| `repo_scan/radar/cli.py` | `repo_scan/radar/gates.py` | 7 | 78% | yes |
| `repo_scan/graphs.py` | `repo_scan/languages.py` | 5 | 77% | **none — seam** |
| `repo_scan/radar/pipeline.py` | `tests/test_radar_pipeline.py` | 8 | 64% | yes |
| `repo_scan/scanner.py` | `repo_scan/writers.py` | 9 | 62% | yes |
| `repo_scan/hub/daemon.py` | `tests/test_act.py` | 8 | 62% | **none — seam** |
| `repo_scan/radar/pipeline.py` | `repo_scan/radar/research.py` | 7 | 58% | yes |
| `repo_scan/graphs.py` | `repo_scan/scanner.py` | 7 | 58% | yes |
| `repo_scan/config.py` | `repo_scan/hub/daemon.py` | 10 | 57% | **none — seam** |
| `repo_scan/radar/gates.py` | `repo_scan/radar/pipeline.py` | 7 | 56% | yes |
| `repo_scan/radar/gates.py` | `tests/test_radar_pipeline.py` | 5 | 56% | **none — seam** |
| `repo_scan/graphs.py` | `repo_scan/writers.py` | 5 | 53% | yes |
| `repo_scan/radar/act.py` | `repo_scan/radar/gates.py` | 5 | 53% | yes |
| `repo_scan/radar/research.py` | `repo_scan/radar/sources.py` | 4 | 53% | yes |
| `repo_scan/hub/state.py` | `repo_scan/radar/gates.py` | 4 | 53% | yes |
| `repo_scan/hub/server.py` | `repo_scan/hub/state.py` | 6 | 52% | yes |
| `repo_scan/radar/act.py` | `repo_scan/radar/llm.py` | 5 | 50% | yes |
| `repo_scan/radar/act.py` | `tests/test_act.py` | 5 | 50% | yes |
| `repo_scan/hub/state.py` | `repo_scan/radar/act.py` | 4 | 50% | yes |
| `repo_scan/hub/state.py` | `repo_scan/radar/llm.py` | 4 | 50% | yes |
