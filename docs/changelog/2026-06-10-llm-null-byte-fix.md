# 2026-06-10 — Strip NUL bytes before LLM subprocess

Background daemon loops crashed with `ValueError: embedded null byte` when
fetched source text contained `\x00` (common in PDF extraction). POSIX forbids
NUL in `execve` argv, so `subprocess.Popen(cmd + [prompt])` failed before the
agent CLI ran.

- `complete()` sanitizes prompts via `_sanitize_subprocess_text()`
- `fetch_url` / `fetch_file` strip NUL from returned text at ingest
