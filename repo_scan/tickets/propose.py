"""Build scan-signal ticket proposals (pure: cfg + signal dicts)."""


def propose_from_scan(cfg: dict, *, line_counts: dict, ranking: list,
                      churn: list, complexity: list, tested: set,
                      behavior: dict, seams: list) -> list[dict]:
    """Build ticket proposals from every scan signal, strongest first."""
    churn_by_file = {c["file"]: c["commits"] for c in churn}
    cc_by_file: dict[str, int] = {}
    for item in complexity:
        cc_by_file[item["file"]] = cc_by_file.get(item["file"], 0) + item["complexity"]

    proposals: list[dict] = []

    # 1. refactor: high churn x high complexity (untested = high priority)
    for f in sorted(set(churn_by_file) & set(cc_by_file),
                    key=lambda f: churn_by_file[f] * cc_by_file[f], reverse=True):
        untested = f not in tested
        proposals.append({
            "fingerprint": f"refactor:{f}",
            "title": f"Refactor {f} (CC {cc_by_file[f]}, {churn_by_file[f]} commits"
                     + (", untested)" if untested else ")"),
            "priority": "high" if untested else "medium",
            "tags": ["refactor"],
            "evidence": ["[[reports/health]]", "[[research/candidates]]"],
            "why": f"`{f}` is both high-churn ({churn_by_file[f]} commits) and "
                   f"high-complexity (total CC {cc_by_file[f]})"
                   + (" with no matching test file." if untested else "."),
            "criteria": [
                "Complexity of every function below rank C",
                *(["Test file exists and passes"] if untested else []),
                "Trend delta confirms complexity drop",
            ],
        })

    # 2. hidden seams: coupled in history, no import edge
    for s in seams:
        proposals.append({
            "fingerprint": f"seam:{s['a']}+{s['b']}",
            "title": f"Hidden seam: {s['a']} <-> {s['b']} ({s['degree']}% coupled)",
            "priority": "medium",
            "tags": ["architecture"],
            "evidence": ["[[reports/coupling]]"],
            "why": f"`{s['a']}` and `{s['b']}` changed together in {s['shared']} commits "
                   f"({s['degree']}% degree) but share no import edge — an implicit "
                   "contract the dependency graph can't see.",
            "criteria": ["Make the dependency explicit (shared module or import)",
                         "Coupling degree drops below threshold in coupling.md"],
        })

    # 3. size: files over the critical line threshold
    crit = cfg["line_crit"]
    for f, s in sorted(line_counts.items(), key=lambda x: x[1]["lines"], reverse=True):
        if s["lines"] >= crit:
            proposals.append({
                "fingerprint": f"size:{f}",
                "title": f"Split {f} ({s['lines']} lines)",
                "priority": "medium",
                "tags": ["refactor"],
                "evidence": ["[[reports/health]]"],
                "why": f"`{f}` is {s['lines']} lines — past the {crit}-line critical "
                       "threshold where files become hard to navigate and review.",
                "criteria": [f"No resulting file above {cfg['line_warn']} lines",
                             "All tests still pass"],
            })

    # 4. stale hubs: top-ranked files untouched for a long time
    age = behavior.get("age_days", {})
    stale_days = cfg.get("stale_days", 180)
    for r in ranking[:5]:
        f = r["file"]
        if age.get(f, 0) >= stale_days:
            proposals.append({
                "fingerprint": f"stale:{f}",
                "title": f"Review stale hub {f} ({age[f]} days untouched)",
                "priority": "low",
                "tags": ["maintenance"],
                "evidence": ["[[index]]", "[[reports/health]]"],
                "why": f"`{f}` ranks in the top 5 by importance but hasn't changed in "
                       f"{age[f]} days — high-risk surface if a change is ever needed.",
                "criteria": ["Confirm tests cover current behavior",
                             "Document any implicit invariants"],
            })

    # 5. knowledge silos — only meaningful with more than one contributor
    all_authors = {o["top_author"] for o in behavior.get("ownership", [])}
    if len(all_authors) > 1:
        silo_share = cfg.get("silo_min_share", 0.9)
        for o in behavior.get("ownership", []):
            if o["top_share"] >= silo_share and o["authors"] == 1 and o["commits"] >= 5:
                proposals.append({
                    "fingerprint": f"silo:{o['file']}",
                    "title": f"Knowledge silo: {o['file']} ({o['top_author']} owns 100%)",
                    "priority": "low",
                    "tags": ["bus-factor"],
                    "evidence": ["[[reports/health]]"],
                    "why": f"`{o['file']}` has {o['commits']} commits, all by one author "
                           "— a bus-factor risk.",
                    "criteria": ["Pair/review the next change with a second person",
                                 "Add or expand docs for this area"],
                })
    return proposals
