# Forensic Audit Guidelines (Gemini)

@./CLAUDE.md

## Skills

This extension ships two agent skills in `skills/`. Gemini loads them on demand when the request matches their description:

- `forensic-audit`: audit and fact-check any AI-generated output.
- `forensic-site-audit`: crawl a web app, test every feature against the live backend, capture and judge screenshots.

## Companion MCP Server (`mcp/web-search`)

When the `web-search` MCP server is enabled, use its `search_website(query_or_url)` tool for mandatory primary-source checks: pass a search query to get DuckDuckGo results (`🔍 SNIPPET`), then pass the primary source URL (`http://` or `https://`, HTML or PDF) to read the full document in Markdown (`🔎 SOURCED`).
