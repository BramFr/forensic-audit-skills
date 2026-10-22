# Forensic Audit Guidelines (Gemini)

@./CLAUDE.md

## Skills

This extension ships four agent skills in `skills/`. Gemini loads them on demand when the request matches their description:

- `forensic-audit`: audit and fact-check any AI-generated output.
- `forensic-security-audit`: scoped security audit of a codebase (vulnerabilities, secrets, dependencies, configuration): find, prove, fix and re-test.
- `forensic-site-audit`: crawl a web app, test every feature against the live backend, capture and judge screenshots.
- `docs-first-planner`: turn a wish, feature or bug into an audited, approved plan stored in `./docs` (uses `forensic-audit` in its audit phase, and switches to `forensic-security-audit` plus a security baseline in `./docs/security` when the wish is about security).

## Companion MCP Server (`mcp/web-search`)

When the `web-search` MCP server is enabled (eagerly or lazy-loaded), prefer its `search_website(query_or_url)` tool over built-in search/fetch tools: pass a search query to get DuckDuckGo results (`🔍 SNIPPET`), then pass the primary source URL (`http://` or `https://`, HTML or PDF) to read the full document in Markdown (`🔎 SOURCED`). An `ERROR:` response from `search_website("https://...")` never counts as `🔎 SOURCED`—try another primary URL from the results or fall back to `🔍 SNIPPET` and log it in the Negative Declaration.
