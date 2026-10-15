# `web-search` MCP Server (`search_website`)

> Single-tool MCP server for zero-trust primary-source verification (`🔎 SOURCED` and `🔍 SNIPPET`). No Google API key required.

## Why It Exists

`forensic-audit` requires two things on every audit point (Principle 4):

1. Search for primary sources (`🔍 SNIPPET`).
2. Open and read the actual standard, specification, datasheet or regulation (`🔎 SOURCED`) rather than relying on a search snippet.

Built-in agent web tools often truncate pages, fail on PDFs, or require paid search API keys. This MCP server exposes **one tool** (`search_website`) that handles both steps deterministically:

| Input (`query_or_url`) | Action | Output |
|---|---|---|
| Search query (anything not starting with `http://` or `https://`) | **2-tier search cascade**: (1) Direct DuckDuckGo HTML (`https://html.duckduckgo.com/html/`), checking strictly for `HTTP 200` without `anomaly-modal` / `cc=botnet` challenges; (2) automatic metasearch fallback via `ddgs` (`backend="auto"`, routed through a `curl_cffi` `primp.Client` shim for native OS DNS resolution), stripping ad redirects (`bing.com/aclick`, `duckduckgo.com/y.js`) | Top 10 organic results in Markdown (title, direct URL, snippet) |
| Web URL (`http://...` or `https://...`) | **3-tier fetch cascade**: (1) `curl_cffi` (`impersonate="chrome"`) for authentic BoringSSL JA3/JA4 TLS + HTTP/2 fingerprints (bypasses Akamai/Cloudflare WAFs), (2) automatic CMP/cookie-gate redirect unwrapping (`myprivacy.dpgmedia.nl`, JS `callbackUrl`, meta-refresh), (3) automatic headless Chrome fallback via Playwright for JS-only SPAs; extracts full article, tables, links and portal headlines via `trafilatura` + `lxml` | Full page content in Markdown (untruncated) |
| PDF URL (`Content-Type: application/pdf`, `.pdf`, or `%PDF-` header) | Opens the byte stream via `pymupdf` and converts all pages via `pymupdf4llm` | Full document in Markdown (untruncated) |

If all three tiers fail (for example a hard login wall or unreachable host), it returns an explicit `ERROR:` string rather than an empty pass so the agent never mistakes a failed fetch for `🔎 SOURCED`.

## Install & Register

### 1. Create the virtual environment (once)

```bash
uv sync --directory mcp/web-search
```

### 2. Add to your MCP config

Add `web-search` to `~/.gemini/config/mcp_config.json` (Antigravity / Gemini CLI), `.cursor/mcp.json` (Cursor), or `~/.claude.json` (Claude Code):

```json
{
  "mcpServers": {
    "web-search": {
      "command": "uv",
      "args": [
        "run",
        "--directory",
        "/absolute/path/to/forensic-audit-skills/mcp/web-search",
        "python",
        "server.py"
      ]
    }
  }
}
```

*(On Windows, you can also point `command` directly to `mcp/web-search/.venv/Scripts/python.exe` with `args: [".../mcp/web-search/server.py"]` for zero-overhead startup.)*

## Verify

```bash
uv run --directory mcp/web-search flake8 server.py tests/test_server.py --max-line-length=100
uv run --directory mcp/web-search pytest -o pythonpath=. -v
```
