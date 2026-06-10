# 2026-06-09 — Portability fixes from first external-repo run

First run against a real external repo (`hhl_site`, a Vite/React/TSX site
with ~700 commits) — exactly the drop-into-any-repo scenario from
RADAR_CONTEXT. Three real bugs surfaced immediately; all fixed.

## Bugs found and fixed

### 1. TS/TSX dependency graph was silently empty
`madge --json src` returns `{}` for `.tsx`/`.jsx` projects unless
`--extensions ts,tsx,js,jsx` is passed. Our own repo is pure Python, so the
code path had never actually produced a TS graph. Now passes the extensions
flag — 43 edges detected on hhl_site.

### 2. PageRank dead on TS repos (paths not re-anchored)
madge emits paths relative to the scanned `src/` dir (`App.tsx`), but
ranking/line-count keys are repo-relative (`src/App.tsx`). The adjacency
never matched, so PageRank and "imported by" were silently 0 for every
file. Edges are now re-anchored to the repo root. On hhl_site the ranking
flipped from churn-only noise to genuinely useful (PageSection.tsx — 5
dependents x 42 commits — correctly #1), and dep-graph PageRank tinting
lit up.

### 3. Lockfiles polluted counts, health, and ranking
`package-lock.json` (12k lines) ranked as the #5 most important file and
inflated total line counts. New `LOCKFILES` skip set in `get_line_counts`
(npm/yarn/pnpm/bun/poetry/uv/pipenv/cargo/composer/bundler/go).

### 4. (cosmetic) Final scan message hardcoded `docs/`
Now respects the configured `docs_dir`.

## Also validated

- `docs_dir` config override works: hhl_site already had a real `docs/`
  folder (resumes, screenshots), so its `.repo-scan.json` points output at
  `repo-docs/` instead — no collision.
- Scan does not touch the target repo's git hooks unless `--install-hook`
  is passed explicitly.

## Verification

- `tests/test_portability.py`: lockfile exclusion + end-to-end madge test
  (tsx imports, repo-relative edges; skipped if madge missing).
- Full suite: 84 passed.
