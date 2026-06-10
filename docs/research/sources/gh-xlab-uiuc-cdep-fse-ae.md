---
id: "gh-xlab-uiuc-cdep-fse-ae"
type: "github"
url: "https://github.com/xlab-uiuc/cdep-fse-ae"
raw_url: "https://github.com/xlab-uiuc/cdep-fse-ae"
tags: ["bytecode", "cloud-systems", "configuration", "csv-output", "dependency-analysis", "distributed-systems", "fse-2020", "hadoop", "html", "java", "repo", "research-artifact", "static-analysis", "taint-tracking"]
linked_files: ["repo_scan/behavior.py"]
relevance: "repo-scan already surfaces implicit coupling between modules (e.g. config.py and hub/daemon.py); cDep’s taxonomy and static-analysis approach could inform future rules or reports that detect when configuration knobs are logically entangled across packages or subsystems."
ingested_at: "2026-06-10 17:15 UTC"
---

# xlab-uiuc/cdep-fse-ae — Configuration dependency analysis for cloud software

## Summary

cDep is a static analysis tool from ESEC/FSE 2020 that discovers configuration dependencies within and across software components by analyzing Java bytecode (Java and Scala) via taint tracking and dependency-handling modules. It targets large cloud/datacenter stacks such as Hadoop, HBase, Spark, and ZooKeeper, and outputs labeled pairs of interdependent configuration parameters with dependency type and source location. The repository ships reproducible Docker workflows, paper datasets, and empirical findings on intra- and inter-component config coupling.

## Key claims

- Configuration parameters in cloud systems have explicit dependency relationships that can be discovered automatically from bytecode rather than documented manually
- cDep identifies five dependency types: control, value relationship, overwrite, default value, and behavioral dependencies between configuration parameters
- Dependencies exist both within a single component (intra-component) and across components in a distributed stack (inter-component)
- Static taint tracking over Java bytecode (via Jimple) can pinpoint the class, method, and statement where a configuration dependency is enforced
- Empirical study on Hadoop-based stacks and OpenStack produced labeled datasets of real configuration dependencies, including one-off edge cases
- Analysis is reproducible via Docker and Maven builds, with results exported as CSV rows of parameter A, parameter B, dependency type, class, method, and Jimple statement

## Notes

_yours to annotate_
