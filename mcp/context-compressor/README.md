# `context-compressor` MCP Server (`compress_context`)

> Deterministic, 100% lossless context compression for subagent context packs: Markdown section scoping, table compaction, RFC 8259 JSON minification, and Positional Pipe-DSV (`#schema:...`) for flat lists ($N \ge 2$).

## Features

- **Workspace-Bounded & Fail-Closed**: Resolves `file_path` strictly inside `workspace_root` (defaults to current working directory) and rejects any path traversal outside the workspace.
- **Lossless JSON Compression**:
  - Converts flat, dense lists of $\ge 2$ scalar dictionaries into Positional Pipe-DSV (`#schema:col1|col2...`) with `\|` escaping and newline normalization.
  - Minifies single objects, nested structures, or sparse lists via RFC 8259 `json.dumps(..., separators=(",", ":"), ensure_ascii=False)`.
- **Lossless Markdown & Text Compaction**:
  - Extracts a single Markdown heading block when `section` is specified (case-insensitive heading substring match outside fenced code blocks).
  - Preserves YAML frontmatter (`---`), fenced code blocks (` ``` `), inline code, URLs, IP addresses, paths, and identifier casing verbatim.
  - Compacts consecutive blank lines and strips padding spaces from Markdown tables (`| col |` $\to$ `|col|`, `| --- |` $\to$ `|-|`).

## Verify

```powershell
py -3.13 -m pytest mcp/context-compressor/tests/test_server.py -v
```
