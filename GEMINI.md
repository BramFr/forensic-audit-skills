# Forensic Audit Guidelines (Gemini)

@./CLAUDE.md

## Skills

This extension ships four agent skills in `skills/`. Gemini loads them on demand when the request matches their description:

- `forensic-audit`: audit and fact-check any AI-generated output.
- `forensic-security-audit`: scoped security audit of a codebase (vulnerabilities, secrets, dependencies, configuration): find, prove, fix and re-test.
- `forensic-site-audit`: crawl a web app, test every feature against the live backend, capture and judge screenshots.
- `docs-first-planner`: turn a wish, feature or bug into an audited, approved plan stored in `./docs` (uses `forensic-audit` in its audit phase, and switches to `forensic-security-audit` plus a security baseline in `./docs/security` when the wish is about security).

## Companion MCP Servers (`mcp/web-search` & `mcp/context-compressor`)

When the `web-search` MCP server is enabled (eagerly or lazy-loaded), prefer its `search_website(query_or_url)` tool over built-in search/fetch tools: pass a search query to get DuckDuckGo results (`🔍 SNIPPET`), then pass the primary source URL (`http://` or `https://`, HTML or PDF) to read the full document in Markdown (`🔎 SOURCED`). **Whenever `forensic-audit` (or any audit skill) and `web-search` are used, always check first whether `./docs/index.md` exists with a `## Search keywords` section:** if present, you MUST pick 1 to 3 matching keywords from `## Search keywords` per query (`{selected keywords} {query}`: 1–2 leading vision/scale priority terms from the start of the list for architecture/UI/scale/performance queries, or 1–2 technical domain terms for protocol/RFC/spec queries, stripping search-operator punctuation like `+`, and never 0 keywords — sending 0 project keywords counts as `🚫 NOT SEARCHED`); if not present (e.g. a standalone question outside a project), proceed with the normal search flow. An `ERROR:` response from `search_website("https://...")` never counts as `🔎 SOURCED`—try another primary URL from the results or fall back to `🔍 SNIPPET` and log it in the Negative Declaration.

Use `compress_context` from `mcp/context-compressor` across all phases: (1) **Phase 1 Progressive Reading** (`section="--frontmatter"`, `section="--headings"`, or multi-section `section="Why,Scope"` on `.md` docs), (2) **Phase 2 Code/Config Audit** (`section="--signatures"` or `section="func1,func2"` on `.py`/`.ts`/`.js`, `section="key"` on `.json`/`.yaml`/`.toml`, and when auditing `>= 3` source files in depth, delegate a read-only `research` subagent with a compressed Context Pack returning `#schema:point|status|file_line|evidence`), and (3) **Phase 4/5 Code-Subagent Isolation**: when writing or modifying any code (even 1 line), always delegate the code edit to a fresh code-subagent (`invoke_subagent` / `Agent` tool) and build its lossless **Subagent Context Pack** with `compress_context` (`--signatures` + target functions + scoped `.md` section / `MODULE.md`, Pipe-DSV `#schema:` for `N >= 2` flat rows/tables, or `JSON_COMPACT` for nested/sparse data; never use lossy word-pruning or parallel edits on the same file).
