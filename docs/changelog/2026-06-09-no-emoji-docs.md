# 2026-06-09 — Emoji-free generated docs

Emoji/pictographs were rendering as tofu boxes in the Obsidian viewer
(common with WSL/Linux font setups), so generated markdown no longer uses
them anywhere.

## Changes

- `health.md` status column: `🔴 critical` / `🟡 large` / `✅` replaced with
  plain text `**critical**` / `*large*` / `ok`.
- New `strip_emoji()` helper in `repo_scan/utils.py` — strips pictographs,
  emoticons, dingbats, flags, variation selectors, and ZWJ, then collapses
  doubled spaces.
- External text is sanitized before it enters the docs:
  - `write_source()` strips emoji from source titles (GitHub repo
    descriptions are the main offender, e.g. repomix's leading package
    emoji).
  - `parse_source_file()` strips on read, so research index/tags rebuilds
    clean up any pre-existing files too.
- Existing `gh-yamadashy-repomix` source note cleaned and research index
  rebuilt.

Terminal output (`✓` / `⚠` / `✗` status glyphs) is unchanged — that is
CLI-only and never lands in the vault.

## Verification

- 2 new tests: `strip_emoji` unit coverage and an end-to-end assertion that
  generated `health.md` contains no codepoints above the BMP punctuation
  range.
- Full suite: 82 passed. Repo-wide grep over `docs/**/*.md` for emoji
  ranges returns nothing after rescan.
