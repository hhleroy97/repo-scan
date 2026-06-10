---

kanban-plugin: board

---

## Proposed

- [ ] [[tkt-0017|Hidden seam: repo_scan/radar/gates.py <-> repo_scan/radar/pipeline.py (53% coupled)]]
- [ ] [[tkt-0018|Hidden seam: repo_scan/hub/daemon.py <-> tests/test_act.py (70% coupled)]]
- [ ] [[tkt-0019|Hidden seam: repo_scan/hub/daemon.py <-> tests/test_hub.py (60% coupled)]]
- [ ] [[tkt-0020|Knowledge silo: repo_scan/config.py (hartley.leroy1997@gmail.com owns 100%)]]
- [ ] [[tkt-0021|Knowledge silo: repo_scan/radar/llm.py (hartley.leroy1997@gmail.com owns 100%)]]
- [ ] [[tkt-0022|Knowledge silo: repo_scan/writers.py (hartley.leroy1997@gmail.com owns 100%)]]

## Approved

- [ ] [[tkt-0014|Hidden seam: repo_scan/hub/server.py <-> repo_scan/hub/ui.py (88% coupled)]]
- [ ] [[tkt-0015|Hidden seam: repo_scan/radar/cli.py <-> repo_scan/radar/gates.py (80% coupled)]]
- [ ] [[tkt-0016|Hidden seam: repo_scan/config.py <-> repo_scan/hub/daemon.py (58% coupled)]]

## In progress


## Done

- [x] [[tkt-0001|Refactor repo_scan/writers.py (CC 52, 7 commits, untested)]]
- [x] [[tkt-0002|Refactor repo_scan/scanner.py (CC 27, 8 commits, untested)]]
- [x] [[tkt-0003|Refactor repo_scan/graphs.py (CC 56, 3 commits, untested)]]
- [x] [[tkt-0004|Refactor repo_scan/languages.py (CC 18, 3 commits, untested)]]
- [x] [[tkt-0005|Refactor repo_scan/radar/sources.py (CC 14, 3 commits, untested)]]
- [x] [[tkt-0006|Refactor repo_scan/radar/pipeline.py (CC 11, 3 commits)]]
- [x] [[tkt-0007|Hidden seam: pyproject.toml <-> setup.py (100% coupled)]]
- [x] [[tkt-0008|Hidden seam: repo_scan/scanner.py <-> repo_scan/writers.py (67% coupled)]]
- [x] [[tkt-0009|Refactor tests/test_radar_pipeline.py (CC 19, 4 commits, untested)]]
- [x] [[tkt-0010|Add a list for the open tickets to the now page]]
- [x] [[tkt-0011|Convert tickets to most human friendly/tech leas project manager terms in. The approval/ticket cards . Retain current ticket as ground truth and have these ticket be abstractions of that ground truth]]
- [x] [[tkt-0012|I want to add a more robust way to visualize changes out ogther a list of low hanging options we could include in the tickets such as simple visual diagrams as aid or soemthinf]]
- [x] [[tkt-0013|Refactor repo_scan/hub/daemon.py (CC 38, 11 commits, untested)]]

## Rejected


%% kanban:settings
```
{"kanban-plugin":"board"}
```
%%
