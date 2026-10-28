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
  - `section="Why,Scope,Acceptance criteria"`: extracts one or multiple comma-separated sections in a single call.
  - Converts Markdown tables with $\ge 2$ data rows into Positional Pipe-DSV (`#schema:Col1|Col2` + `val1|val2`) when `dsv_for_flat_lists=True`, while preserving 1-row tables (`|col|`), YAML frontmatter, code fences, URLs, IPs, and identifier casing verbatim.
- **Lossless JSON, CSV/TSV, YAML & TOML Compression (`.json`, `.csv`, `.tsv`, `.yaml`, `.yml`, `.toml`)**:
  - Supports `section="key1,key2"` on JSON objects, converts top-level or nested dict flat lists ($\ge 2$ scalar objects) and `.csv`/`.tsv` files into Positional Pipe-DSV (`#schema:col1|col2...`), minifies general JSON via RFC 8259, and strips full-line `#` comments and extra blank lines from `.yaml`/`.toml`.

## Verify

```powershell
uv run --directory mcp/context-compressor pytest tests/test_server.py -q
```
