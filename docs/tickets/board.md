---

kanban-plugin: board

---

## Proposed

- [ ] [[tkt-0014|Hidden seam: repo_scan/hub/server.py <-> repo_scan/hub/ui.py (88% coupled)]]
- [ ] [[tkt-0015|Hidden seam: repo_scan/radar/cli.py <-> repo_scan/radar/gates.py (80% coupled)]]
- [ ] [[tkt-0016|Hidden seam: repo_scan/config.py <-> repo_scan/hub/daemon.py (58% coupled)]]
- [ ] [[tkt-0017|Hidden seam: repo_scan/radar/gates.py <-> repo_scan/radar/pipeline.py (53% coupled)]]

## Approved


## In progress

- [ ] [[tkt-0006|Refactor repo_scan/radar/pipeline.py (CC 11, 3 commits)]]
- [ ] [[tkt-0012|I want to add a more robust way to visualize changes out ogther a list of low hanging options we could include in the tickets such as simple visual diagrams as aid or soemthinf]]
- [ ] [[tkt-0013|Refactor repo_scan/hub/daemon.py (CC 38, 11 commits, untested)]]

## Done

- [x] [[tkt-0001|Refactor repo_scan/writers.py (CC 52, 7 commits, untested)]]
- [x] [[tkt-0002|Refactor repo_scan/scanner.py (CC 27, 8 commits, untested)]]
- [x] [[tkt-0003|Refactor repo_scan/graphs.py (CC 56, 3 commits, untested)]]
- [x] [[tkt-0004|Refactor repo_scan/languages.py (CC 18, 3 commits, untested)]]
- [x] [[tkt-0005|Refactor repo_scan/radar/sources.py (CC 14, 3 commits, untested)]]
- [x] [[tkt-0007|Hidden seam: pyproject.toml <-> setup.py (100% coupled)]]
- [x] [[tkt-0008|Hidden seam: repo_scan/scanner.py <-> repo_scan/writers.py (67% coupled)]]
- [x] [[tkt-0009|Refactor tests/test_radar_pipeline.py (CC 19, 4 commits, untested)]]
- [x] [[tkt-0010|Add a list for the open tickets to the now page]]
- [x] [[tkt-0011|Convert tickets to most human friendly/tech leas project manager terms in. The approval/ticket cards . Retain current ticket as ground truth and have these ticket be abstractions of that ground truth]]

## Rejected


%% kanban:settings
```
{"kanban-plugin":"board"}
```
%%
