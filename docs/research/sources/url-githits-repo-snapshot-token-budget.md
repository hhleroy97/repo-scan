---
id: "url-githits-repo-snapshot-token-budget"
type: "url"
url: "https://app.githits.com/solutions/c82a0e55-c083-47af-99ac-ca561293799a"
raw_url: "https://github.com/MervinPraison/PraisonAI/blob/main/src/praisonai-agents/praisonaiagents/context/manager.py"
tags: ["context-engineering", "token-budget", "snapshot", "deduplication", "agents"]
linked_files: ["repo_scan/digest.py", "repo_scan/radar/research.py", "repo_scan/config.py"]
relevance: "Implementation patterns for repo_snapshot injection: hash-based digest dedup across LLM calls, heuristic token estimation, truncate-to-budget — repo-scan already has digest_tokens and usage.jsonl; wire similar dedup so parallel loops do not re-send identical scan snapshots."
ingested_at: "2026-06-10 16:00 UTC"
---

# GitHits — Repo snapshot digest with token budget (PraisonAI pattern)

## Summary

GitHits `get_example` distilled a pattern from PraisonAI's context manager: compute a **hash digest** of the repo snapshot, deduplicate across session LLM calls (skip re-injection when digest unchanged), estimate tokens heuristically (chars/4), and truncate user content to fit `max_tokens`. Repo-scan should adopt digest dedup for `repo_snapshot()` — if `scan.json` `generated_at` and git HEAD are unchanged since last injection, omit the block.

## Key claims

- Snapshot hook at LLM call boundary captures exact messages + digest for audit.
- Session dedup cache prevents paying twice for the same snapshot in parallel threads.
- Budget utilization metric helps governance (`budget_daily_tokens` alignment).
- Heuristic estimation matches repo-scan's existing chars/4 fallback in `llm.py`.

## GitHits provenance

- `get_example` query: "repo snapshot digest inject into LLM prompt context window budget token limit"
- solution_id: `c82a0e55-c083-47af-99ac-ca561293799a`
- Reference: [PraisonAI context/manager.py](https://github.com/MervinPraison/PraisonAI/blob/main/src/praisonai-agents/praisonaiagents/context/manager.py) (MIT)

## Notes

_yours to annotate — implement `repo_snapshot_digest()` keyed on scan.generated_at + git rev-parse HEAD._
