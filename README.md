# Forensic Audit Skills

> Zero-trust audit skills for AI coding agents. Verify AI output, and crawl-test whole websites with visual evidence, without a single hardcoded selector.

Two skills that make an agent audit instead of agree.

## The Problems

AI-generated output tends to look right without being right:

- **Fake green.** Code compiles, a request returns 200, a screenshot file exists, and nothing was actually proven.
- **Silent assumptions.** Claims from earlier turns are carried forward as facts.
- **Brittle tests.** Selectors, routes and expected texts are written down in advance and break on the first copy change.
- **Missing evidence.** No database check, no look at the rendered result, no primary source.

## The Solution

| Component | Use it to | Addresses |
|-------|-----------|-----------|
| [**forensic-audit**](skills/forensic-audit/SKILL.md) | Audit and fact-check any AI-generated output (code, plans, recipes, contracts, calculations, advice) | Fake green, silent assumptions, outdated or unsafe advice |
| [**forensic-site-audit**](skills/forensic-site-audit/SKILL.md) | Crawl a website or web app, test every feature against the live backend, capture and judge screenshots | Brittle tests, missing evidence, untested pages, UX defects |
| [**forensic-security-audit**](skills/forensic-security-audit/SKILL.md) | Security audit of a codebase within a scope you name: find, prove, fix and re-test vulnerabilities, secrets, dependency and configuration risks; severity per finding, no hardcoded sources | Fake security, unverified "it is safe", leaked secrets, vulnerable dependencies |
| [**docs-first-planner**](skills/docs-first-planner/SKILL.md) | Turn a wish, feature or bug into an audited, approved plan stored in `./docs` (docs check, dimension research per principle (phase 1.5), forensic audit of the project and the wish, first-principles analysis, grill of 3-10 questions with a web-verified answer loop, plan, persist) with `scripts/docs_tool.py` for numbering, index and checks | Vibe coding: unverified beliefs, duplicate or contradicting features, lost rationale |
| [**first-principles-architect**](skills/first-principles-architect/SKILL.md) | Domain-neutral intake and design engine for anything that must be built, designed, tuned, solved or trained: 7-dimension intake, 8-part systems analysis (incl. perception and ergonomics), closed verification loop with an approval gate for quality upgrades, and a clean, whitelist-only delivery | Answers built on guessed parameters, unseen side effects, placebo options and scaffolding left in the result |
| [**mcp/web-search**](mcp/web-search/README.md) | Single-tool MCP server (`search_website`): DuckDuckGo search (`🔍 SNIPPET`) + 1-turn `auto_open_top=1` primary-source opening + untruncated HTML/PDF extraction (`🔎 SOURCED`) with `<= 9,500 B` slack-redistributed batch budget, SQLite WAL + RFC 9111 `ETag` + RFC 3986 cache, session-delta block re-slicing, Pipe-DSV `#schema:`, and `filter_query` section scoping (`search_website.json = 2,565 B <= 3.1 KB`), no API keys | Unopened primary sources, unreadable PDF datasheets/standards, paid search API lock-in, web-scraping token bloat (-22% to -80.1% tokens) |
| [**mcp/context-compressor**](mcp/context-compressor/README.md) | Single-tool MCP server (`compress_context`): 100% lossless structural context compression (Markdown `--frontmatter`, `--headings`, exact-match deduplicated multi-section `A,B,C <= 10,240 B`, `filter_query` tiered index projection, automatic Slim Plan-Read on `./docs/<cat>/NN-*.md`, table->DSV, Python/TS/JS AST `--signatures` & symbol extraction, JSON/YAML/TOML/CSV Pipe-DSV `#schema:` & `JSON_COMPACT`) | Context rot during long audits, token bloat from full source files/prose/Markdown tables (-48% to -99% tokens), syntax-breaking lossy compression |

Both skills run **in a single request**, with no mid-way questions, and report **conclusions only**.

## How It Works

### forensic-audit

1. **Tool check and mandatory sourcing**: every point is searched; each gets a source status (🔎 sourced, 🔍 snippet only, ⚠️ no source found, 🚫 not searched) and a method label (⚙️ executed, 🧮 hand-calculated, 🧠 reasoned).
2. **Dual-focus selection**: exactly 10 audit points, 5 by impact and 5 by uncertainty, with no filler points.
3. **Closed loop per point**: baseline (BEFORE), simulation (AFTER), primary-source check, red-team falsification, repair with at most two rounds before fail-closed.
4. **Evidence-based status**: ✅ confirmed, 🟡 plausible, 🔁 corrected, ⛔ fail-closed, ❓ unverified.
5. **Honest hand-over**: two verdicts (original output and corrected version), confidence, source gaps, negative declaration and an execution protocol.

### forensic-security-audit

1. **Scope first**: only what you name is read and tested; secrets are masked and treated as compromised.
2. **Attack surface map**: entry points, trust boundaries, assets and the dependency and build chain, discovered from the code.
3. **Findings per category**: injection, authentication, authorization, secrets, dependencies, configuration, crypto, input/output, data protection, availability, AI/agent risks.
4. **Proof**: each finding is reproduced where possible (🔴 proven), otherwise 🟠 likely or ❓ unverified, never counted as confirmed. Current standards and advisories are searched at runtime, not hardcoded.
5. **Closed loop**: concrete fix, re-test of the original proof, at most two repair rounds before fail-closed.
6. **Verdict** (SECURE ENOUGH / CONDITIONAL / NOT SECURE) with severity, confidence, coverage and source gaps.

When you ask `docs-first-planner` for anything security related, it switches to this skill automatically, stores the plan under `./docs/security/` and keeps a security baseline there that later AI work must respect.

### forensic-site-audit

0. **Discovery**: crawl routes, read the accessibility tree and write a `site-inventory.json`. Nothing is hardcoded.
1. **Dual-focus selection** of 10 audit points derived from that inventory.
2. **Closed loop per point**: rest-state screenshot, interaction per control type, SQL persistence check, red-team probes, visual inspection against measured thresholds.
3. **Implementation** of missing pages, test-first, if the task requires it.
4. **Hand-over** with a screenshot register, coverage figures and an audit stamp.

**Zero-hardcode rule:** routes, selectors, labels, field names and texts are discovered at runtime through the accessibility tree and the backend schema. A test that breaks on a copy or layout change is rewritten.

**Default thresholds** checked from measurements, not by eye alone:

| Criterion | Threshold |
|-----------|-----------|
| Target size (Fitts' Law) | >= 44x44 CSS px |
| Text contrast | >= 4.5:1 (>= 3:1 for large text and UI components) |
| Layout | No overlap, overflow or clipped text |
| Interaction feedback | Visible focus, hover, active, disabled and loading states |
| Page health | No console errors, no failed requests |

### first-principles-architect

0. **Principles research, always**: before any question, each of the 7 dimensions is researched with at least one live search, using the search of `forensic-audit` itself and official sources only (law and standards, regulators, primary documentation, accredited guidelines, peer-reviewed science; never blogs or forums), and `forensic-audit` then supplements it on the request itself: which principles and quality criteria must a result of this kind satisfy, and where do such results usually fail? The outcome is a sourced criteria register that the intake, the pre-delivery check and the confidence statements rest on. `docs-first-planner` embeds this whole skill as its phase 1.5, between the docs check and the forensic audit, and keeps it identical to this one.
1. **Intake before answers**: the request is mapped onto 7 universal dimensions (baseline, target, hard constraints, failure modes, system dynamics, resource budget, reversibility). Wrong assumptions are corrected and only the 3 to 4 questions that change the outcome are asked.
2. **Systems analysis**: 8 fixed parts in the subject's own vocabulary, including how the result is perceived and controlled by whoever uses it.
3. **Closed verification loop**: a circuit breaker (parameter mismatch, confidence gap, constraint violation) sends the work back to research or to the intake. An approval gate lets you choose which proactive quality upgrades to include. A link in the chain passes only with a 🔎 primary source or a ⚙️ executed test, never with a percentage.
4. **Clean delivery**: every option on offer is wired through to its execution, and the deliverable contains only what you supplied or approved. Gaps are reported around the deliverable, never inside it.

It is domain-neutral by design: the subject, vocabulary and numbers are derived at runtime. Use `docs-first-planner` instead when the result must be a tracked plan in `./docs`.

## Install

### Option A: Claude Code plugin (recommended)

From Claude Code:

```
/plugin marketplace add BramFr/forensic-audit-skills
/plugin install forensic-audit-skills@forensic-audit-skills
```

This installs both skills.

### Option B: Per-project `CLAUDE.md`

New project:

```bash
curl -o CLAUDE.md https://raw.githubusercontent.com/BramFr/forensic-audit-skills/main/CLAUDE.md
```

Existing project (append):

```bash
echo "" >> CLAUDE.md
curl https://raw.githubusercontent.com/BramFr/forensic-audit-skills/main/CLAUDE.md >> CLAUDE.md
```

### Option C: Copy a skill folder

Copy `skills/forensic-audit/` and/or `skills/forensic-site-audit/` into your agent's skills directory (for example `~/.claude/skills/`).

### Option D: Cursor

See [CURSOR.md](CURSOR.md).

### Option E: Gemini CLI

```bash
gemini extensions install https://github.com/BramFr/forensic-audit-skills
```

This installs both skills plus [GEMINI.md](GEMINI.md) as context. Alternatively copy a skill folder into `~/.gemini/skills/` (user scope) or `.gemini/skills/` (workspace).

### Option F: Antigravity

Copy `skills/forensic-audit/` and/or `skills/forensic-site-audit/` into your workspace `.agents/skills/` or the global skills directory. The `SKILL.md` format is the same.

### Companion MCP Servers (`web-search` & `context-compressor`)

To give your agent keyless DuckDuckGo search (`🔍 SNIPPET`), full HTML/PDF-to-Markdown extraction (`🔎 SOURCED`) via `search_website`, and 100% lossless structural context compression (`compress_context`) for clean code-subagent context packs, sync [`mcp/web-search`](mcp/web-search/README.md) and [`mcp/context-compressor`](mcp/context-compressor/README.md) with `uv` and add them to your MCP configuration (for example `~/.gemini/config/mcp_config.json`, `.cursor/mcp.json`, or `~/.claude.json`):

```bash
uv sync --directory mcp/web-search
uv sync --directory mcp/context-compressor
```

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
    },
    "context-compressor": {
      "command": "uv",
      "args": [
        "run",
        "--directory",
        "/absolute/path/to/forensic-audit-skills/mcp/context-compressor",
        "python",
        "server.py"
      ]
    }
  }
}
```

Skills use `compress_context` across all phases: (1) **Phase 1 Progressive Reading** (`filter_query="<keywords>"` on `docs/index.md` for tiered `#schema:` projection, default **Slim Plan-Read** on `docs/<cat>/NN-slug.md`, `section="--frontmatter"`, `section="--headings"`, or exact-match deduplicated multi-section `section="Why,Scope"`), (2) **Phase 2 Code/Config Audit** (`section="--signatures"` or `section="func1,func2"` on `.py`/`.ts`/`.js`, `section="key"` on `.json`/`.yaml`/`.toml`, and read-only subagent Context Packs when auditing `>= 3` files), and (3) **Phase 4/5 Code-Subagent Isolation**: whenever any skill writes or modifies code (even 1 line), it delegates the edit to a fresh code-subagent with a lossless **Subagent Context Pack** built via `compress_context` (`--signatures` + target functions + scoped `.md` section / `MODULE.md`, Pipe-DSV `#schema:` for flat lists/tables with `N >= 2` rows, or `JSON_COMPACT` for nested/sparse data; never lossy token pruning).

#### Lossless Token Savings (Measured `o200k_base` Benchmarks)

Both MCP servers reduce context token consumption with **0% information or quote loss** (reproducible via `python scripts/benchmark_1request.py --check`; full report in [`docs/benchmarks/benchmark-1request.md`](docs/benchmarks/benchmark-1request.md) and architecture rationale in [`docs/feature/20-reproduceerbare-3-profielen-benchmark-en-regressiefix.md`](docs/feature/20-reproduceerbare-3-profielen-benchmark-en-regressiefix.md) (`feature/20`)):

| Optimization Layer | Mechanism | Measured Token / Byte Reduction |
|---|---|---|
| **3-Profile Cumulative 1-Request Chain (`feature/18`–`feature/20`)** | Role-scoped Subagent Context Packs + 1-turn `auto_open_top=1` batch search + filtered index + Slim Plan-Read across `24 -> 10 -> 7` turns (`0` `>10,240 B` temp-file offloads) | **`989,768 -> 292,313 (-70.5%) -> 126,831 (-87.2%)` cumulative tokens** |
| **Slim Plan-Read & Exact-Match Section Deduplication (`mcp/context-compressor`)** | Default Slim Plan-Read on `./docs/<cat>/NN-*.md` (`Why,Scope,Acceptance criteria`) + exact-match heading precedence & line-range deduplication (`skills/forensic-audit/SKILL.md` `Principles,Pre-build`: `22,133 B -> 10,223 B <= 10,240 B`, `0` dupes) + `filter_query` tiered `docs/index.md` projection | **-87.9% on plan reads**, **-53.8% on multi-section skill reads**, **-34.0% on `docs/index.md`** |
| **Code-Subagent Context Pack (`mcp/context-compressor`)** | `--signatures` (`-87.9%` to `-89.5%`) + scoped `.md` section extraction + table compaction + Pipe-DSV (`#schema:`) / `JSON_COMPACT` sent to an isolated code-subagent | **-48.5% to -89.5% tokens** (and **-48.4% real API `input_tokens`** in live multi-file A/B subagent benchmarks, with 100% identical test & audit output) |
| **`web-search` 1-Turn `auto_open_top=1` & `<= 9,500 B` Batch Slack Budget** | Opens top-ranked primary authority URLs inside the search turn and redistributes unused byte slack across batch items on clean paragraph boundaries | **-80.1% bytes** (`46,695 B -> 9,275 B <= 9,500 B` on 8-item batches) |
| **`web-search` SQLite WAL + RFC 9111 `ETag` + Session-Delta Re-Slicing** | Persistent SQLite `PRAGMA journal_mode=WAL` cache with RFC 3986 URI normalization, `If-None-Match` / `304 Not Modified` revalidation, and session-delta omission of already-shown blocks/ToC | **100% network elimination on warm hits** + **-11.4% bytes** on 2nd view (`7,927 B -> 7,023 B`) |
| **`web-search` Filtered Page Scoping (`filter_query`) & Catalog DSV** | Returns compact `## Page Headings Index` + `## Filtered Matches` (**-72.5% tokens**), Positional Pipe-DSV (`#schema:`), URL tracking stripping, and compact `search_website.json` tool schema (`2,565 B <= 3.1 KB`, **-37.8%**) | **-22.4% to -79.3% tokens** across docs, RFCs, and catalogs |

## Usage

Just describe the task. The skills trigger on intent.

```
Audit this migration plan before I run it.
Fact-check this recipe for food safety.
Test the whole site, take screenshots and tell me what is broken.
Implement the missing login and settings pages and verify them visually.
Design this for me, but ask what you need to know before you give me a solution.
```

For site audits you can pass an optional **project context block** (goal, backend, UX and security requirements, acceptance criteria). It is read as parameters, never as selectors. See [EXAMPLES.md](EXAMPLES.md).

When something has already gone wrong, share the evidence (an error message, a log, a failed bake, a part that does not fit). The skills discover the domain and governing standard via live search (law, ISO/NEN/IEC/RFC, regulator, manufacturer docs or guild standard — opening free primary counterparts when a formal standard is paywalled), find the decisive signal, check whether it is a deliberate guard, test the likely causes and give a verified fix. See [EXAMPLES.md](EXAMPLES.md), section 6. Each skill has its own variant of the same seven steps (Discover, Quote, Signal, Guard, Hypotheses, Fix, Confirm); keep the step names identical when editing.

With `docs-first-planner`, acceptance criteria can carry a `Check: <command> -> <expected result>` line. The planner re-runs the safe, read-only ones of related `done` items before and after a change, marks a failing item `in-progress` and opens a bug item; anything that writes, deploys or touches the network is only run after your approval. `./docs/index.md` also maintains a dynamic `## Search keywords` list (~30-50 project-specific technical, domain and scale terms, starting with the ~5-8 core vision/scale priority terms); during every audit, the skills and the `search_website` MCP tool schema require selecting 1 to 3 fitting keywords per search query (`{selected keywords} {query}`: 1–2 leading vision/scale priority terms for architecture/UI/scale/performance queries, or 1–2 technical domain terms for protocol/RFC/spec queries, never 0 keywords) so external sources match the project's scale and domain.

Ask for **"full report"** or **"show audit trail"** to get the written-out analysis. The default is compact.

## Requirements (forensic-site-audit)

- A running instance of the target web app and its backend
- Playwright with Chromium (or a Playwright sidecar endpoint)
- Read access to the database to verify persistence (SQL)
- Credentials supplied through environment variables, never inline

## Repository Layout

```
forensic-audit-skills/
├── .claude-plugin/
│   ├── marketplace.json
│   └── plugin.json
├── .cursor/rules/forensic-audit.mdc
├── docs/
│   ├── benchmarks/benchmark-1request.md
│   └── index.md
├── mcp/
│   ├── context-compressor/
│   │   ├── pyproject.toml
│   │   ├── README.md
│   │   ├── server.py
│   │   └── tests/test_server.py
│   └── web-search/
│       ├── pyproject.toml
│       ├── README.md
│       ├── search_website.json
│       ├── server.py
│       └── tests/test_server.py
├── scripts/
│   └── benchmark_1request.py
├── skills/
│   ├── docs-first-planner/SKILL.md
│   ├── first-principles-architect/SKILL.md
│   ├── forensic-audit/SKILL.md
│   ├── forensic-security-audit/SKILL.md
│   └── forensic-site-audit/SKILL.md
├── CLAUDE.md
├── CURSOR.md
├── EXAMPLES.md
├── GEMINI.md
├── gemini-extension.json
├── LICENSE
└── README.md
```

## Tradeoff

These skills bias toward rigor over speed. A full site audit crawls, tests, screenshots and re-tests. For a trivial change, a quick manual check is fine.

## License

MIT
