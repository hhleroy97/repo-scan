# Dependency graph
_Generated 2026-06-10 00:21 UTC_

_Node color = PageRank tier: red = hub, amber = mid, gray = leaf._

## TypeScript / JavaScript

_Skipped: no TS/JS files_

## Python

```mermaid
graph TD
  tests_test_phase_a["test_phase_a"] --> repo_scan_radar_cli["cli"]
  tests_test_phase_a["test_phase_a"] --> repo_scan_ranking["ranking"]
  tests_test_radar_ingest["test_radar_ingest"] --> repo_scan_config["config"]
  tests_test_radar_ingest["test_radar_ingest"] --> repo_scan_radar_fetchers["fetchers"]
  tests_test_radar_ingest["test_radar_ingest"] --> repo_scan_radar_sources["sources"]
  tests_test_visuals["test_visuals"] --> repo_scan_radar_cli["cli"]
  tests_test_visuals["test_visuals"] --> repo_scan_graphs["graphs"]
  tests_test_visuals["test_visuals"] --> repo_scan_utils["utils"]
  tests_test_visuals["test_visuals"] --> repo_scan_writers["writers"]
  tests_test_scan["test_scan"] --> repo_scan_radar_cli["cli"]
  tests_test_radar_pipeline["test_radar_pipeline"] --> repo_scan_config["config"]
  tests_test_radar_pipeline["test_radar_pipeline"] --> repo_scan_radar_pipeline["pipeline"]
  tests_test_radar_llm["test_radar_llm"] --> repo_scan_config["config"]
  tests_test_radar_llm["test_radar_llm"] --> repo_scan_radar_llm["llm"]
  tests_test_radar_llm["test_radar_llm"] --> repo_scan_radar_research["research"]
  tests_test_radar_llm["test_radar_llm"] --> repo_scan_radar_sources["sources"]
  tests_test_radar_gates["test_radar_gates"] --> repo_scan_config["config"]
  tests_test_radar_gates["test_radar_gates"] --> repo_scan_radar_gates["gates"]
  tests_test_portability["test_portability"] --> repo_scan_radar_cli["cli"]
  tests_test_portability["test_portability"] --> repo_scan_config["config"]
  tests_test_portability["test_portability"] --> repo_scan_graphs["graphs"]
  tests_test_portability["test_portability"] --> repo_scan_languages["languages"]
  tests_test_radar_full["test_radar_full"] --> repo_scan_config["config"]
  tests_test_radar_full["test_radar_full"] --> repo_scan_radar_pipeline["pipeline"]
  tests_test_radar_full["test_radar_full"] --> repo_scan_radar_cli["cli"]
  classDef hot fill:#e74c3c,stroke:#922b21,color:#fff
  classDef warm fill:#f5b041,stroke:#b9770e,color:#1a1a1a
  classDef cold fill:#d6dbdf,stroke:#85929e,color:#1a1a1a
  class repo_scan_config,repo_scan_radar_cli hot
  class repo_scan_graphs,repo_scan_languages,repo_scan_radar_fetchers,repo_scan_radar_gates,repo_scan_radar_pipeline,repo_scan_radar_sources,repo_scan_ranking,repo_scan_writers,tests_test_radar_pipeline warm
  class repo_scan_radar_llm,repo_scan_radar_research,repo_scan_utils,tests_test_phase_a,tests_test_portability,tests_test_radar_full,tests_test_radar_gates,tests_test_radar_ingest,tests_test_radar_llm,tests_test_scan,tests_test_visuals cold
```
