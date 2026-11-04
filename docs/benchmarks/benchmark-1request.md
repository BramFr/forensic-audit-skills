# Reproducible 3-Profile 1-Request Benchmark (`feature/18`, `feature/19`, `feature/20`)

- **Plans & Architecture Rationale:** [feature/20](../feature/20-reproduceerbare-3-profielen-benchmark-en-regressiefix.md) | [feature/19](../feature/19-vijf-lossless-token-upgrades-auto-open-batch-budget-index-filter-en-sqlite-cache.md) | [feature/18](../feature/18-1-request-benchmark-en-lossless-token-finetuning.md) | [feature/10](../feature/10-lossless-token-fixes-context-compressor-en-web-search.md)
- **Reference Commit (`feature/20`):** `feat(benchmark): live 3-profile benchmark report, section deduplication and <=3.1KB schema (feature/20)`
- **Reproduce & Verify:** `python scripts/benchmark_1request.py --save` | `python scripts/benchmark_1request.py --check`

## Executive Summary & `feature/20` Architecture Fixes

1. **Live 3-Profile Chain Model (`feature/20` fix #1):** Dynamically computes cumulative 1-request token consumption across `Baseline` (`24` turns, `989,768` tok) -> `Finetuned v1 (feature/18)` (`10` turns, `291,573` tok, `-70.5%`) -> `Finetuned v2 (feature/19 + feature/20)` (`7` turns, `128,549` tok, `-87.0%`), eliminating all `>10,240 B` temp-file offloads (`6 -> 0 -> 0`).
2. **Exact-Match Section Deduplication (`feature/20` fix #2):** `mcp/context-compressor/server.py` prioritizes exact heading matches before substring fallback and deduplicates overlapping `(start, end)` line intervals on multi-section reads (`skills/forensic-audit/SKILL.md` `Principles,Pre-build use (principles research)`: `22,144 B` -> `10,234 B <= 10,240 B`, `-53.8%`, `0` duplicate sections).
3. **Compact Tool Schema `<= 3.1 KB` (`feature/20` fix #3):** `mcp/web-search/search_website.json` compressed from `4,124 B` (`3,374 B` in `feature/18`) to `2,565 B <= 3,100 B` (`-37.8%`) while preserving all `AliasChoices` and mandatory `## Search keywords` rules.

## Methodology & Normative Standards

- **Active Token Estimator:** `deterministic UTF-8 heuristic ceil(bytes / 3.8) (tiktoken o200k_base fallback)` alongside exact UTF-8 byte lengths (`IETF RFC 8259` / `IETF RFC 7763`).
- **Normative Framework:** `ISO/IEC 25010:2023` & `ISO/IEC 25023:2016` (quantitative performance efficiency & resource utilization), `IETF RFC 9111` (STD 98 HTTP Caching `ETag`/`If-None-Match`/`304 Not Modified`, obsoleting RFC 7234), `IETF RFC 3986 §6` (URI cache-key normalization), and `NIST SP 800-53 Rev. 5.2.0 SI-7` (deterministic `--check` parity).

## 1. Artifact Inline Budget Verification (`<= 10,240 B` / `<= 4,500 B` / `<= 3,100 B`)

```text
#schema:artifact|before_bytes|after_bytes|after_tokens|reduction_pct|limit_bytes|status
compress_context(web-search --signatures)|80257|9688|2550|-87.9%|10240|OK (inline <= limit)
compress_context(context-compressor --signatures)|50700|4982|1312|-90.2%|10240|OK (inline <= limit)
compress_context(docs/index.md 4 sections)|15446|9497|2500|-38.5%|10240|OK (inline <= limit)
compress_context(docs/index.md filter_query='benchmark')|15446|6791|1788|-56.0%|10240|OK (inline <= limit)
compress_context(references/audit-brief.md)|10394|9122|2401|-12.2%|10240|OK (inline <= limit)
compress_context(references/persist-and-regression.md Phase 5)|6896|3911|1030|-43.3%|10240|OK (inline <= limit)
compress_context(docs/feature/18 slim plan read)|27389|4225|1112|-84.6%|4500|OK (inline <= limit)
compress_context(forensic-audit SKILL.md Principles,Pre-build)|22144|10234|2694|-53.8%|10240|OK (inline <= limit)
compress_context(first-principles-architect SKILL.md Phase 0)|20981|7262|1912|-65.4%|10240|OK (inline <= limit)
search_website.json tool schema|4124|2565|675|-37.8%|3100|OK (inline <= limit)
skills/docs-first-planner/SKILL.md|51767|26485|6970|-48.8%|26500|OK (inline <= limit)
skills/first-principles-architect/SKILL.md|25400|20981|5522|-17.4%|21000|OK (inline <= limit)
```

## 2. Live Component Measurements (`feature/19` + `feature/20`)

```text
#schema:component_feature|before_metric|after_metric|delta_or_speedup|limit_or_target|status
Tiered index projection (filter_query='benchmark')|9497 B (2500 tok)|6791 B (1788 tok)|-28.5%|<= 10240 B|OK
Slim plan-read (docs/feature/18 section=None vs --all)|27310 B (7187 tok)|4225 B (1112 tok)|-84.5%|<= 4500 B (>= -80%)|OK
Exact-match deduplicated multi-section (forensic-audit Principles,Pre-build)|22144 B (5828 tok)|10234 B (2694 tok)|-53.8%|<= 10240 B (0 dupes)|OK
Batch search slack budget (8 items with auto_open_top=1)|46695 B (unbudgeted)|9275 B (slack-capped)|-80.1%|<= 9500 B|OK
SQLite WAL + RFC 3986 cache hit speedup (time.perf_counter)|1 HTTP parse + WAL write|0 HTTP calls (warm WAL hit)|100% network elimination (journal_mode=wal)|PRAGMA wal + RFC 3986|OK
Session delta block re-slicing (2nd view of primary source)|7927 B (1st view + ToC)|7023 B (2nd delta view)|-11.4%|< 1st view (ToC+blocks omitted)|OK
```

## 3. Cumulative 1-Request 3-Profile Token Model

```text
#schema:chain_profile|turns|single_turn_prefix_tokens|cumulative_tokens|delta_pct|inline_offloads
Baseline (pre-feature/18)|24|41240|989768|0.0%|6 (>10.240 B temp-files)
Finetuned v1 (feature/18)|10|20618|291573|-70.5%|0 (100% inline <=10.240 B)
Finetuned v2 (feature/19 + feature/20)|7|10525|128549|-87.0%|0 (100% inline <=9.500 B + auto_open_top + slim-plan)
```
