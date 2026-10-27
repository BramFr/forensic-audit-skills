# `web-search` MCP Server (`search_website`)

> Single-tool MCP server for zero-trust primary-source verification (`🔎 SOURCED` and `🔍 SNIPPET`). No Google API key required.

## Why It Exists

`forensic-audit` requires two things on every audit point (Principle 4):

1. Search for primary sources (`🔍 SNIPPET`).
2. Open and read the actual standard, specification, datasheet or regulation (`🔎 SOURCED`) rather than relying on a search snippet.

Built-in agent web tools often truncate pages, fail on PDFs, or require paid search API keys. This MCP server exposes **one tool** (`search_website`) that handles both steps deterministically:

| Input (`query_or_url`) | Action | Output |
|---|---|---|
| Search query (anything not starting with `http://` or `https://`) | **2-tier search cascade**: (1) Direct DuckDuckGo HTML (`https://html.duckduckgo.com/html/`), checking strictly for `HTTP 200` without `anomaly-modal` / `cc=botnet` challenges; (2) automatic metasearch fallback via `ddgs` (`backend="auto"`, routed through a `curl_cffi` `primp.Client` shim for native OS DNS resolution), stripping ad redirects (`bing.com/aclick`, `duckduckgo.com/y.js`) and tracking parameters (`utm_*`, `fbclid`, `gclid`, `msockid`) | Top 10 organic results in lossless Positional Pipe-DSV (`#schema:idx\|title\|url\|snippet`, **-24.2% tokens**) |
| Web URL (`http://...` or `https://...`) | **3-tier fetch cascade**: (1) `curl_cffi` (`impersonate="chrome"`) for authentic BoringSSL JA3/JA4 TLS + HTTP/2 fingerprints (bypasses Akamai/Cloudflare WAFs), (2) automatic CMP/cookie-gate redirect unwrapping (`myprivacy.dpgmedia.nl`, JS `callbackUrl`, meta-refresh), (3) automatic headless Chrome fallback via Playwright for JS-only SPAs; extracts structured catalog items (JSON-LD, `__NEXT_DATA__`, DOM cards) in Pipe-DSV (`#schema:title\|price\|url\|details`) and full readable article text, tables, and visible `<pre>`/`<code>` examples as clean plain text while stripping `<script>`/`<style>`/`<svg>`, inline link URL bloat, `[#]` permalinks, and UI boilerplate | Full page content in compact plain text + Pipe-DSV (**-22.4% to -79.3% tokens**, 0% information loss) |
| PDF URL (`Content-Type: application/pdf`, `.pdf`, or `%PDF-` header) | Opens the byte stream via `pymupdf`, converts pages via `pymupdf4llm`, and strips formatting/UI noise | Full document in clean plain text + tables (untruncated) |

If all three tiers fail (for example a hard login wall or unreachable host), it returns an explicit `ERROR:` string rather than an empty pass so the agent never mistakes a failed fetch for `🔎 SOURCED`.

## Built-in Lossless Token Optimizations (`feature/07` & `bugs/04`)

1. **Filtered Page Scoping (`filter_query`)**: When `filter_query` matches blocks on a page, returns only `## Page Headings Index` + `## Filtered Matches` without re-appending the full unfiltered page underneath (**-72.5% tokens**).
2. **Positional Pipe-DSV (`#schema:`)**: Formats DuckDuckGo results (`#schema:idx|title|url|snippet`, **-24.2% tokens**) and extracted catalog/listing items (`#schema:title|price|url|details`).
3. **Pure Readable Text with Visible `<pre>` Code Preserved**: Strips `<script>`, `<style>`, `<svg>`, `<noscript>`, inline `[text](https://...)` URL targets, Sphinx `[#]`/`[¶]` permalinks, and Markdown formatting wrappers (`**`, ```` ``` ````) while preserving 100% of prose, tables, inline `<code>` values, and visible `<pre>` code blocks as plain text (**-22.4% to -64.7% tokens**; pass `include_code=True` if fenced ```` ``` ```` wrappers are desired).
4. **URL Tracking Parameter Stripping & Catalog Deduplication**: Strips `utm_*`, `fbclid`, `gclid`, `_trk*`, `hash`, `itmmeta`, `itmprp`, and `amdata` from extracted URLs and omits duplicate `trafilatura` footer text when `>= 5` structured catalog items are extracted (**-79.3% tokens** on catalog pages).

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
