# `context-compressor` MCP Server (`compress_context`)

> Deterministic, 100% lossless context compression for orchestrator progressive reading (Phase 1), code/config audits (Phase 2), and clean code-subagent context packs (Phase 4/5).

## Features

- **Workspace-Bounded & Fail-Closed**: Resolves `file_path` strictly inside `workspace_root` (defaults to current working directory) and rejects any path traversal outside the workspace.
- **Python & TS/JS AST Source Code Extraction (`.py`, `.ts`, `.tsx`, `.js`, `.jsx`)**:
  - `section="--signatures"` (or `--outline`): extracts Python AST imports, top-level constants, classes, and function/method signatures with type annotations, 1st docstring line, and `# L<start>-L<end>` line ranges (and TS/JS `import`/`export`/`interface`/`type`/`class`/`function` signatures with line numbers).
  - `section="func1,ClassA"` (comma-separated symbols): extracts the exact verbatim source lines (including decorators) prefixed with `# L<start>-L<end>`.
  - Without `section`: collapses multiple consecutive blank lines outside multiline strings into at most 1 blank line.
- **Lossless Markdown & Text Compaction (`.md`, `.txt`)**:
  - `section="--frontmatter"`: extracts only the YAML frontmatter block (`--- ... ---`).
  - `section="--headings"`: extracts all `#`–`######` headings outside code fences with line numbers (`L<nr>: <heading>`).
  - `section="Why,Scope,Acceptance criteria"`: extracts one or multiple comma-separated sections in a single call, with **exact-match heading precedence** before substring fallback and **multi-section `(start, end)` line-range deduplication** (`feature/20`: `skills/forensic-audit/SKILL.md` `Principles,Pre-build use (principles research)` compressed from `22,133 B` to `10,223 B <= 10,240 B`, `-53.8%`, `0` duplicate sections).
  - **Automatic Slim Plan-Read (`feature/19`)**: when reading `./docs/<cat>/NN-*.md` with `section=None`, defaults to YAML frontmatter + `Why,Scope,Acceptance criteria,Relations` (`<= 4,500 B`, `-87.9%` vs. `--all`; pass `section="--all"` for full historical verification blocks).
  - **Tiered Table Projection (`filter_query="<keywords>"`, `feature/19`)**: filters `#schema:` Pipe-DSV rows in `docs/index.md` into matching full rows (`id|title|status|summary`) plus a compact tail `#schema:id|status` for non-matching `done` items (`-34.0%` bytes, `<= 10,240 B`).
  - **Reversible Link Compaction & Never-Larger Guard (`feature/10`, `feature/18`)**: compacts `docs/index.md` `[feature/NN](feature/NN-slug.md)` links (`-25.8%`), registers `@mcp.tool(output_schema=None)` for a slim MCP tool list, and guarantees compressed output never exceeds raw input byte size.
  - Converts Markdown tables with $\ge 2$ data rows into Positional Pipe-DSV (`#schema:Col1|Col2` + `val1|val2`) when `dsv_for_flat_lists=True`, while preserving 1-row tables (`|col|`), YAML frontmatter, code fences, URLs, IPs, and identifier casing verbatim.
- **Lossless JSON, CSV/TSV, YAML & TOML Compression (`.json`, `.csv`, `.tsv`, `.yaml`, `.yml`, `.toml`)**:
  - Supports `section="key1,key2"` on JSON objects, converts top-level or nested dict flat lists ($\ge 2$ scalar objects) and `.csv`/`.tsv` files into Positional Pipe-DSV (`#schema:col1|col2...`), minifies general JSON via RFC 8259, and strips full-line `#` comments and extra blank lines from `.yaml`/`.toml`.

## Verify & Reproducible 3-Profile Benchmark (`feature/20`)

See [`../../docs/benchmarks/benchmark-1request.md`](../../docs/benchmarks/benchmark-1request.md) and [`../../docs/feature/20-reproduceerbare-3-profielen-benchmark-en-regressiefix.md`](../../docs/feature/20-reproduceerbare-3-profielen-benchmark-en-regressiefix.md) (`feature/20`) for the full 3-profile 1-request benchmark (`989,768 -> 292,313 [-70.5%] -> 126,831 [-87.2%]` cumulative tokens across `24 -> 10 -> 7` turns).

```powershell
uv run --directory mcp/context-compressor pytest tests/test_server.py -q
python scripts/benchmark_1request.py --check
```
