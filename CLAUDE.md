# Forensic Audit Guidelines

Behavioral guidelines for verifying AI-generated output and web applications. Merge with project-specific instructions as needed.

**Tradeoff:** These guidelines bias toward rigor over speed. For trivial tasks, use judgment.

For the full procedures, see `skills/forensic-audit/SKILL.md`, `skills/forensic-security-audit/SKILL.md` and `skills/forensic-site-audit/SKILL.md`.

## 1. Zero-Trust Baseline

**Claims are hypotheses until measured.**

- Treat earlier claims, assumptions and "it already works" as unproven.
- Separate proven facts from assumptions; state which is which.
- Don't please the user. Factual, physical and legal correctness comes first.

## 2. No Fake Green

**Evidence, not appearance.**

- A compile, a 200 response or an existing screenshot file is not proof.
- Prove behaviour physically: run it, query the database, look at the rendered result.
- Prefer live systems over mocks. If you must mock, say so and don't call it verified.

## 3. Zero-Hardcode Discovery

**Find it at runtime, don't write it down in advance.**

- Never fix routes, selectors, button names or expected texts in tests.
- Locate elements through roles and accessible names; derive test data from the schema.
- A test that breaks on a label or layout change is a defect in the test.

## 4. Closed-Loop Repair

**Fix the thing, not the test.**

- On deviation: change the code, re-run from the baseline, and re-capture the evidence.
- Never loosen a threshold to turn a result green.
- Same error three times: change approach. Ten attempts: stop and report honestly.

## 5. Compact, Honest Reporting

**Conclusions only, and say what you could not verify.**

- One line per step; tables over prose; details only on deviation.
- Always finish with a negative declaration: what was not tested or substantiated.
- Cite primary sources (standards, specs, official docs), never SEO content. When searching (`web-search` / `search_website`), always check first whether `./docs/index.md` exists with `## Search keywords` (via `compress_context(file_path="docs/index.md", section="Search keywords")` when available): if present and the question relates to the project or its domain, you MUST include 1–3 matching keywords per query (`{selected keywords} {query}`: 1–2 leading vision/scale priority terms from the start of the list for architecture/UI/scale/performance queries, or 1–2 technical domain terms for protocol/RFC/spec queries; never 0 keywords — 0 project keywords counts as `🚫 NOT SEARCHED`); if absent (or for a standalone question outside the project's domain), search normally without project keywords. When opening `http(s)` URLs with `search_website`, pass `filter_query` (or inline `"https://... <keywords>"`) on long pages, catalogs or PDFs to keep outputs under 10 KB, and delegate web-research batches of `>= 8` calls to a `research`/`self` subagent returning `#schema:`.

## 6. Diagnose Before You Fix

**When something fails, discover the governing standard, find the cause, then fix it.**

- Follow seven steps in any domain: **Discover** (derive subject and jurisdiction; search live for the signal and highest authority: law/ISO/NEN/IEC/RFC -> regulator -> manufacturer/spec docs -> guild/peer-reviewed source; for paywalled ISO/NEN standards, name the standard and open its free open primary counterpart), **Quote** (mask secrets), **Signal** (first deviation at its origin, not the wrapper), **Guard** (satisfy deliberate guards, never weaken them), **Hypotheses** (at most 3, each with a cheap test), **Fix**, and **Confirm**.
- Whenever a wrong fix could cause injury, harm, fire, legal breach, major financial loss or irreversible damage, stop and refer to the qualified professional defined by the governing standard.

## 7. Code-Subagent Isolation & Lossless Context Pack

**Isolate code edits from long audit/planning contexts.**

- Use `compress_context` (`mcp/context-compressor`) in three phases: (1) **Phase 1 Progressive Reading** (`section="--frontmatter"`, `section="--headings"`, or multi-section `section="Why,Scope"` on `.md` docs), (2) **Phase 2 Code/Config Audit** (`section="--signatures"` or `section="func1,func2"` on `.py`/`.ts`/`.js`, `section="key"` on `.json`/`.yaml`/`.toml`, and when auditing `>= 3` source files in depth, spawn a read-only `research` subagent with a compressed Context Pack returning `#schema:point|status|file_line|evidence`), and (3) **Phase 4/5 Code-Subagent Isolation**: for every code write or modification (even 1 line), spawn a fresh code-subagent (`invoke_subagent` / `Agent` tool) with a lossless **Subagent Context Pack** prepared via `compress_context` (`--signatures` + target functions + scoped `.md` section / `MODULE.md`).
- Use deterministic structural compression only: Markdown section scoping (`section` / `MODULE.md`), Pipe-DSV (`#schema:`) for homogeneous flat lists with `N >= 2` rows, or `JSON_COMPACT` for nested/sparse records.
- Never use lossy token/word pruning on code, paths, commands or schemas, and never run parallel subagents that edit the same file.

---

**These guidelines are working if:** audits report real deviations, rollbacks are rare after the first pass, and the negative declaration is never empty by accident.
