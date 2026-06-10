---
type: "spec"
problem: "Hidden seam: repo_scan/config.py <-> repo_scan/hub/daemon.py (58% coupled). `repo_scan/config.py` and `repo_scan/hub/daemon.py` changed together in 7 commits (58% degree) but share no import edge — an implicit contract the dependency graph can't see. Acceptance criteria: Make the dependency explicit (shared module or import); Coupling degree drops below threshold in coupling.md. Research current best practices and draft a spec for this work."
status: "approved"
audit_verdict: "revise"
analysis: "[[2026-06-10-hidden-seam-repo-scan-config-py-repo-sca-analysis]]"
drafted_at: "2026-06-10 17:31 UTC"
linked_files: ["repo_scan/config.py", "repo_scan/hub/daemon.py", "repo_scan/hub/notify.py", "repo_scan/hub/server.py", "repo_scan/hub/settings.py"]
---

# Spec — Hidden seam: repo_scan/config.py <-> repo_scan/hub/daemon.py (58% coupled). `repo_scan/config.py` and `repo_scan/hub/daemon.py` changed together in 7 commits (58% degree) but share no import edge — an implicit contract the dependency graph can't see. Acceptance criteria: Make the dependency explicit (shared module or import); Coupling degree drops below threshold in coupling.md. Research current best practices and draft a spec for this work.
_Drafted 2026-06-10 17:31 UTC by radar — **status: approved**_

I'll inspect the repo's coupling metrics, config/daemon setup, and the tkt-0008 precedent so the revised spec matches reality.
## Goal

Close tkt-0016: replace the implicit config↔daemon key/default contract with an explicit hub-owned settings module so static analysis can see the dependency, and so change-coupling for `repo_scan/config.py` ↔ `repo_scan/hub/daemon.py` drops strictly below 50% (`coupling_min_degree`). **Baseline (live scan):** 7 shared commits, 56% degree, ~13 config / ~12 daemon revs — reconcile ticket prose citing 58%. Per tkt-0008 precedent, AC1 is satisfied by shared `hub.settings` with import edges `config → hub.settings` and `hub.daemon → hub.settings`, not a direct `config → daemon` import. **AC1 does not clear the hidden-seam warning:** `hidden_seams` checks direct import edges only; neither file imports the other (unlike tkt-0008’s retained `scanner → writers` edge). Seam clearance depends entirely on AC2 (pair absent from coupling output). **Human reviewer:** confirm ticket AC1 wording accepts shared-module reinterpretation before implementation.

## Approach

Extract `repo_scan/hub/settings.py` owning hub key names (`HUB_CONFIG_KEYS`) and defaults (`HUB_DEFAULTS`) currently duplicated between `RADAR_CONFIG_KEYS` and daemon inline `cfg.get(..., magic)` fallbacks. Add `cfg_hub(cfg, key)` so daemon never hardcodes hub defaults. In `load_config`, merge `HUB_DEFAULTS` and validate unknown keys against `set(DEFAULT_CONFIG) | HUB_CONFIG_KEYS | RADAR_CONFIG_KEYS`; remove hub keys from `RADAR_CONFIG_KEYS` via set subtraction. Land refactor with contract tests. **AC2 requires degree strictly below 50%** — exactly 50% remains listed; `analyze_history` only emits pairs with `degree >= coupling_min_degree`, so post-rescan success is **pair absent** from `coupling.md` / hidden-seam warning, not “listed below 50%”. A merge-time fixture proves the math; live `coupling.md` compliance is **not merge-gated** — ticket may stay open until post-merge divergent history + rescan. **Divergent commits must touch only `config.py` or only `daemon.py`** — `hub/settings.py`-only commits do not move this pair’s degree. Baseline 7 shared @ 56%: one co-touch refactor commit raises shared to 8 (~59%); plan **≥6** subsequent solo-side commits on `config.py` and/or `daemon.py` (e.g. 6 config-only → ~48%). Do not cite tkt-0008’s “≥2” rule without its tuned solo volumes (5 shared + 3 writers + 6 scanner + 2 decouple).

## Changes

- **`repo_scan/hub/settings.py`** (new) — `HUB_CONFIG_KEYS` (`serve_host`, `serve_port`, `daemon_poll_seconds`, `daemon_scan_hours`, `ntfy_topic`, `ntfy_server`, `dashboard_url`, `vault_autocommit`, `max_parallel_acts`, `max_parallel_loops`); `HUB_DEFAULTS` matching today’s daemon fallbacks; `cfg_hub(cfg, key)`. Document `serve_host` asymmetry: `server.py` binds `0.0.0.0`; daemon treats missing host as no dashboard URL — do not unify via a single default without documenting both behaviors.
- **`repo_scan/hub/daemon.py`** — `from .settings import cfg_hub, HUB_DEFAULTS`; replace inline magic defaults for hub-owned keys; no new `config` import.
- **`repo_scan/config.py`** — `from .hub.settings import HUB_CONFIG_KEYS, HUB_DEFAULTS`; seed `DEFAULT_CONFIG` with `HUB_DEFAULTS`; subtract hub keys from `RADAR_CONFIG_KEYS`; widen unknown-key check.
- **`repo_scan/hub/server.py`**, **`repo_scan/hub/notify.py`** (optional, same PR if trivial) — use `cfg_hub` only if `serve_host` semantics preserved.
- **`tests/test_hub_settings.py`** (new) — contract, load, and coupling-degree fixtures.
- **`docs/tickets/tkt-0016.md`** — baseline 56%/7 shared; AC1 reinterpretation; AC2 post-merge rescan note.
- **Regenerated scan docs** — after sufficient divergent history: `docs/reports/coupling.md`, `docs/scan.json`, `docs/index.md`, `docs/digest.md`, `docs/reports/health.md`, `docs/architecture/dependency-graph.md`, `docs/reports/dependencies.md`.

Do **not** decompose remaining `RADAR_CONFIG_KEYS` (act, budget, gates, LLM) or change coupling thresholds.

## Tests

| Acceptance criterion | Automated test |
|---|---|
| Explicit dependency (shared module) | `tests/test_hub_settings.py::test_config_imports_hub_settings` — `config.py` imports `repo_scan.hub.settings`. |
| Explicit dependency (shared module) | `tests/test_hub_settings.py::test_daemon_imports_hub_settings` — `daemon.py` imports `hub.settings`; no inline magic defaults for hub keys (AST/literal scan). |
| Hub defaults single-sourced | `tests/test_hub_settings.py::test_load_config_applies_hub_defaults` — empty repo `load_config` includes every `HUB_DEFAULTS` key; `.repo-scan.json` override wins. |
| Coupling degree below threshold | `tests/test_hub_settings.py::test_config_daemon_degree_below_threshold` — temp git fixture: **7** pair commits, **6** config-only, **5** daemon-only (~56% baseline), then **≥4** config-only or **≥3** config + **≥3** daemon-only (no `settings.py`-only commits); `analyze_history` → pair absent. No live-repo root in pytest. |
| Coupling degree below threshold | Post-rescan (manual, after ≥6 live solo-side commits if refactor co-touches both): `config.py`↔`daemon.py` **absent** from coupling table and hidden-seam warning. |
| No daemon regression | `tests/test_daemon.py` — full suite passes unchanged behavior. |

## Documentation

- **`repo_scan/hub/settings.py`** — module docstring: owns hub/daemon scheduler keys and defaults; consumed by `load_config` and hub runtime; `serve_host` bind vs URL semantics.
- **`repo_scan/config.py`** — docstring note: hub defaults imported from `hub.settings`, not duplicated in `RADAR_CONFIG_KEYS`.
- **`README.md`** — Hub config keys paragraph: defaults live in `hub/settings.py`; list unchanged key names.
- **`docs/tickets/tkt-0016.md`** — remediation summary; reconcile 58% ticket prose to live 56%; AC1/AC2 split.
- Regenerated coupling and dependency-graph artifacts after rescan.

## Risks

- `config → hub.settings` adds core→hub import; acceptable per ConfigurationObject pattern but differs from strict layering.
- Refactor commit co-touching `config.py` and `daemon.py` adds shared 7→8, worsening AC2 math until ≥6 solo-side commits land.
- Partial extraction leaves daemon reading radar/act/budget keys via `RADAR_CONFIG_KEYS` only — pair may still co-change on radar tickets.
- Default drift if any `cfg.get(key, literal)` fallbacks remain for hub keys.
- Optional `server.py`/`notify.py` migration can drift `serve_host` unless asymmetry is explicit in `cfg_hub`.
- `config.py` is in `protected_paths` — requires governance/test gate approval.
- AC2 closure not merge-gated; synthetic fixture can pass while live seam persists until divergent history accumulates.

## Out of scope

Full `RADAR_CONFIG_KEYS` split into radar/act/governance modules; import-linter contracts (follow-on); other hidden seams (`daemon`↔tests, `server`↔`ui`, radar pairs); changing `coupling_min_degree` / `hidden_seams` semantics; typed config objects beyond dict + `cfg_hub`; amending ticket AC1 wording without reviewer sign-off.

## Audit

> [!warning] Audit verdict: revise
> The shared-module direction, 56%/7-shared baseline, degree formula, and tkt-0008 AC1 reinterpretation match the repo, but the coupling fixture math and closure criteria need tightening before human review.
> - Tests table contradicts Approach on divergent-commit math: after baseline (7 shared, 13 config revs, 12 daemon revs) plus a co-touch refactor (shared→8, rev sum→27), only ≥4 config-only yields degree round(200×8/31)=52% (still listed); Approach’s ≥6 solo-side commits is correct, but the Tests row’s “≥4 config-only” alternative is insufficient.
> - Coupling fixture spec omits the landing co-touch commit (8th shared) between historical baseline and post-refactor divergent commits, so the described history does not model the PR the Approach section assumes (~59% immediately after merge).
> - Goal says “Close tkt-0016” while Risks/AC2 state the ticket may remain open until post-merge divergent history and rescan—internal closure criteria conflict.
> - Ticket problem statement and hidden_seams warning are about the config↔daemon pair having no import edge; AC1 via hub.settings leaves that direct edge absent until AC2, so AC1 alone cannot clear the four-entry hidden_seam banner—spec flags reviewer sign-off but ticket AC1 is still unamended and can be read as fully done at merge.
> - Missing risk: merging HUB_DEFAULTS into DEFAULT_CONFIG changes load_config() and write_default_config() surface (hub keys always present in cfg / new .repo-scan.json templates), not just deduplicating daemon fallbacks.
> - Missing risk: notify.py retains ntfy_server default (https://ntfy.sh) outside hub.settings if optional server/notify migration is deferred—another default drift path beside serve_host asymmetry.
> - HUB_CONFIG_KEYS lists max_parallel_acts/max_parallel_loops as hub-owned while daemon still reads radar_enabled, act_enabled, budget_daily_tokens via RADAR_CONFIG_KEYS-only keys—partial extraction risk is noted but the pair may keep co-changing on non-hub radar tickets without a mitigation plan.

## Provenance

- analysis: [[2026-06-10-hidden-seam-repo-scan-config-py-repo-sca-analysis]]
