---
name: forensic-audit
description: Critically audit, fact-check and verify AI-generated output in any domain (code, recipes, designs, plans, calculations, advice, texts, contracts, data) for factual errors, outdated standards, unsafe or illegal advice and fake success. Use whenever the user wants something checked, reviewed, fact-checked, audited, validated or double-checked ("is this correct?", "check this", "can I trust this?", "is this safe?", "audit this", "fact-check this"), even if the word audit is not used, and always before anyone acts on AI advice with consequences for health, safety, money, law or anything irreversible. Also use it when something has gone wrong and the user shares the evidence (an error message, log, stack trace, failed test, a failed bake, a part that does not fit, a pet that does not respond) and wants to know what is wrong and how to fix it ("it doesn't work", "why did this fail?", "what does this error mean?", "het werkt niet", "wat gaat hier fout?").
---

# Forensic Audit (universal)

Take any AI-generated output, in any domain, and test it before someone acts on it. The goal is not a reassuring stamp but an honest picture of what is proven, what is merely plausible and what is wrong. AI output often sounds more certain than it is, so an audit that also sounds certain without evidence adds nothing.

Write the report in the language the user is writing in.

---

## Output modes

The audit work (Phases 1 and 2) is ALWAYS done in full, internally. Only the amount of text shown to the user differs.

**COMPACT (default).** The user sees only the result: the answer to their question, the verdict and the honest caveats. Use this unless the user asks for more. Format: see "Compact report" at the end of this file.

**FULL.** Only when the user asks for a "full report", "audit trail", "volledig rapport", "alle details", "laat de tabellen zien" or similar. Then show Phase 1 table, Phase 2 table and the six Phase 3 sections as described below.

Never skip the audit steps in COMPACT mode to save time. Shorter output, not shallower work.

---

## Principles

**1. Run in one go, but ask when a missing input changes the verdict.**
Do not pause mid-audit for permission to continue. Exception: if a missing fact changes the verdict (jurisdiction, product version, dosage, age, load, tax year), ask ONE concise question before starting. For minor gaps, state a 1-line assumption and log it in open points.

**2. Treat every earlier claim as an unproven hypothesis.**
Earlier claims in the output or conversation are not evidence; factual, physical and legal correctness outweighs a pleasant answer.

**3. Reject fake success.**
Code that compiles but fails at runtime, or a recipe, text or plan that sounds plausible but fails in practice, is not a pass. A pass requires proof (calculation, executed test, primary source).

**4. Always search for external sources, and report honestly what was found.**
Searching is mandatory for all 10 points; own knowledge is only a hypothesis. Before Phase 1, check available tools (`web-search` / `search_website`, built-in search/fetch, code execution, file access) and prefer `search_website` (`web-search` MCP). Track **source status** and **method** per point:

| Label | Meaning |
| --- | --- |
| 🔎 SOURCED | Primary source opened and read in this session (page, document or standard, not just a snippet) |
| 🔍 SNIPPET | Search result points to a primary source, but only the snippet was seen; page not opened |
| ⚠️ NO SOURCE FOUND | Search ran, but no primary source confirmed or refuted the claim |
| 🚫 NOT SEARCHED | No search ran (missing tool, failed, or skipped) — **process failure**, must be flagged |
| ⚙️ EXECUTED | Actually run or calculated with a tool |
| 🧮 HAND-CALCULATED | Calculated by hand; calculation shown |
| 🧠 REASONED | Based on own knowledge/reasoning, not independently tested |

Rules:
- Never claim something was searched, opened, executed or measured when it was not, or present a snippet as a read primary source.
- Reach 🔎 in 1 turn via `search_website(query_or_url="<query>", auto_open_top=1)` (or batch `search_website(queries_or_urls=[...], auto_open_top=1)` / `"open: <query>"` up to 10 items/call with SQLite WAL + `ETag` caching and session-delta block re-slicing in a `<= 9.500 B` batch budget) for DuckDuckGo snippets (🔍) + auto-opened top primary URL (🔎), keeping queries concise (**4–6 core terms** + 1–2 index keywords; one language and one standard/concept per query); or pass an `http(s)` URL (HTML/PDF) with `filter_query="<keywords>"` (or `"https://... <keywords>"` on long catalogs/PDFs for `<= 10.240 B` inline) to read Markdown (🔎). Use 🔍 only when opening fails. For `>= 8` searches/scrapes (or combined 7 D1–D7 + 10 P1–P10 searches), prefer delegating the batch (**Batch Prompting**, `arXiv:2511.04108`, no hard token caps) to a `research`/`self` subagent under a **Difficulty-Adaptive Budget (DAST)**: concise *Chain-of-Draft (CoD)* density for D1–D7 and deep reasoning for P1–P10 and Step 2B disconfirmation, followed by a **Zero-Trust Context-Purge** returning `#schema:` tables (`#schema:dimension|criterion|threshold|source`, `#schema:point|status|source|evidence`).
- **Project search keywords (`./docs/index.md`) — mandatory check**: check `./docs/index.md` via `compress_context(file_path="docs/index.md", section="Search keywords")` before Phase 1.
  - **Present (in project/domain)**: include 1–3 matching terms from `## Search keywords` per query (`{selected keywords} {point query}`): 1–2 leading vision/scale terms (first ~5–8 terms) for architecture/design/UI/workflow/scale queries, or 1–2 **technical/methodological domain terms** (`primary-source-verification`, `ISO-NEN-IEC`, `IETF-RFC`, `NIST-SP-800`, `OWASP-ASVS`, `Python-stdlib`, stripping `+`) for external protocol/standard/RFC/library/scientific queries—never prepend abstract vision terms (`zero-trust`, `no-fake-green`) to external standard queries, never dump the full list, and **never send 0 keywords when present** (`0 keywords = 🚫 NOT SEARCHED`).
  - **Absent or out-of-domain standalone question**: search normally (`{point query}`) without project keywords.
- **Fail-closed on `ERROR:`**: an `ERROR:` response (HTTP 403, timeout, JS wall) **never** counts as 🔎 SOURCED; try another primary URL or fall back to 🔍 / ⚠️ and log the failed URL in open points. Try >= 2 distinct queries before concluding ⚠️ NO SOURCE FOUND and log queries tried. ⚠️ or 🚫 points can never be ✅ CONFIRMED; list each in open points and **Source gaps**.
- **No search tool**: mark all points 🚫 NOT SEARCHED, put `⚠️ NO EXTERNAL SOURCES CONSULTED — this audit rests on reasoning only` at the top, and name the primary source per point. **No code execution**: calculate by hand (🧮) and name the confirming real-world test.

**5. Keep the report compact, never at the expense of honesty.**
Warnings, source gaps, open points and `DO NOT USE` verdicts always appear in full, even in COMPACT mode.

**6. When something goes wrong, diagnose before you fix.**
For any failure (error, log, failed test, or physical/chemical/biological/procedural failure), find the cause from live primary sources and give a verified fix in 7 steps:
1. **Discover.** Derive domain, subject (product, material, species, language, protocol, version) and jurisdiction; check `./docs/index.md` for `## Search keywords` (1–3 keywords when in-domain). Ask ONE concise question if a missing fact changes the cause/standard (Principle 1); else state a 1-line assumption. Search live (`search_website` -> open primary URL for 🔎) for the failure signal and standard using: (a) law/formal standards (EU/national law, ISO, NEN, IEC, EN, UNECE, IETF RFC), (b) regulators/authorities (NIST, NCSC, NVWA, RDW, NHG, EMA, OSHA), (c) primary manufacturer/spec/framework docs (manuals, datasheets, error tables, release notes), (d) accredited guild guidelines and peer-reviewed science. **Two-step rule for paid standards (ISO/NEN/IEC):** name the formal standard (ID + title) AND open its free **open primary counterpart** (referencing law, regulator guidance, NIST/UNECE/OWASP, or datasheet) for 🔎 SOURCED.
2. **Quote.** Copy the failure signal verbatim (mask secrets); the signal is evidence, your explanation is a hypothesis.
3. **Signal.** Pinpoint the first observable deviation where it originates, not downstream wrapper symptoms.
4. **Guard.** Check the primary source for whether the failure is a deliberate guard (validation, safety interlock, type approval, normative limit). Satisfy the guard—never remove, loosen or bypass it.
5. **Hypotheses.** List <= 3 candidate causes with a cheap test each (inspection, measurement, lookup, command, trial); run it or name the exact user test.
6. **Fix.** Give the concrete fix aligned with the primary source and state what it changes (never ask for secrets).
7. **Confirm.** Verify against the standard/baseline that the failure is gone and guards still reject invalid inputs.
If a wrong diagnosis/fix could cause injury, illness, animal harm, fire, structural/environmental damage, legal breach, major financial loss or irreversible harm, stop and have a qualified professional (named from the standard/authority) perform or sign off the work, with hypotheses only as background.

**7. Execution-Subagent Isolation & Lossless Context Pack.**
Use `compress_context` (`mcp/context-compressor`) in all phases: (1) **Phase 1 & Skill Progressive Reading** (`filter_query="<keywords>"` on `docs/index.md` for tiered `#schema:` projection; default **slim plan-read** on `docs/<cat>/NN-slug.md` keeping 2-col `Decisions` + `Scope (Out)` and omitting heavy sections unless `section="Scope,Approach,Acceptance criteria"` or `--all`; section-scoping on `SKILL.md`/references like `section="Principles,Pre-build use (principles research)"`), (2) **Phase 2 Subject/File Audit** (`section="--signatures"` or `section="func1,func2"` on `.py`/`.ts`/`.js`, `section="key"` on `.json`/`.yaml`/`.toml`, delegating a read-only `research` subagent returning `#schema:point|status|file_line|evidence` on `>= 3` files), and (3) **Phase 4/5 Execution-Subagent Isolation**: delegate any file/deliverable edit to a fresh execution subagent (`invoke_subagent` / `Agent`) with a lossless `compress_context` **Subagent Context Pack** (`--signatures` + target sections/symbols + `MODULE.md`, Pipe-DSV `#schema:` for `N >= 2` flat rows/tables, or `JSON_COMPACT`; no lossy word-pruning or parallel same-file edits).

---

## Phase 1: Select exactly 10 audit points

Analyse `<USER_REQUEST>` (what is wanted) and `<AI_GENERATED_OUTPUT>` (what was proposed). Select exactly 10 points, split in two groups:

1. **5 High-Impact points (P1-P5)**: the components that make the whole thing crash, fail or become unsafe if they are not correct.
2. **5 High-Uncertainty points (P6-P10)**: the components with the most blind assumptions, missing evidence, complex boundary conditions, outdated methods or risk of fake success.

**No filler points.** Always select 10. If the output contains fewer than 10 obvious risk areas, do not pick trivial points (taste, style, wording). Instead split a serious component into separate, independently checkable sub-claims (the number, the unit, the condition, the time limit, the target group, the exception).

In FULL mode, show one table: `# | Type (Impact/Uncertainty) | Audit point | Reason (max. 10 words)`. In COMPACT mode, do not show it.

---

## Phase 2: Audit each point, one by one

Work through the 10 points in order. Do the five steps internally for each point.

**Step 1: Baseline "BEFORE".** Separate proven facts from assumptions; note the exact starting state, the hard limits (laws, tolerances, capacity), the expected change, and the main failure mechanisms (pre-mortem).

**Step 2: Simulation "AFTER".** Pick the archetype that fits: *Physical/Chemical*, *Digital runtime* (actually run code, queries, payloads), *Process/Workflow*, *Quantitative/Normative* (exact calculation against a limit) or *Adversarial/Stress test*. Perform it and note the result with the method label.

**Step 3: Primary source check (mandatory for every point).** Pick the authority type that fits: *Legal/Normative* (ISO/NEN, building codes, EU law, HACCP), *Technical* (datasheets, API docs, RFCs, release notes), *Scientific* (peer-reviewed work), *Trade/Guild* or *Safety/Audit* (NIST, OWASP, food-safety and public-health bodies). Search for the latest version of the standard or guideline, preferring the authority of the relevant jurisdiction (if `./docs/index.md` with `## Search keywords` is present, include 1-3 matching keywords in the query; if absent, search normally), and then open the primary URL to verify the actual text. Use primary sources only; marketing blogs, forums, shops and SEO content do not count as a source (they may at most point you to one). Note source + identifier or URL + source status label.

**Step 4: Red-team & Step 2B Adversarial Disconfirmation.** Try to disprove the point, using the archetype that fits: *Edge-case stress test*, *Ageing and deprecation* (**Step 2B Adversarial Disconfirmation**: actively search whether the standard, rule, API or method has been withdrawn, deprecated, superseded or refuted, and verify: (a) *Existence at time horizon $t$*, (b) *Typology* — strict binding outcome obligation vs. flexible guideline, and (c) *Higher authority* — whether overruled by a higher jurisdiction or spec), *Silent failures and side effects*, *Adversarial abuse* (operator error, environment, safety) or *Efficiency falsification* (applying the **Simplicity Ladder**: YAGNI -> DRY -> Stdlib/Built-in -> Native -> Existing Dependencies -> Minimal Code + LBYL). Compare BEFORE and AFTER with the sources from Step 3.

**Step 5: Decide.**
- *No deviation*: assign a status (below) and continue.
- *Deviation*: repair it (redesign, tighter limits, substituting a component or method, recalibrating a parameter, or a fail-closed fallback) and go back to Step 1 for this point. After two failed repair rounds, set the point to ⛔ FAIL-CLOSED rather than looping further.

**Status per point.** Status reflects the evidence, not just the absence of problems:

| Status | Use when |
| --- | --- |
| ✅ CONFIRMED | No deviation, and backed by 🔎 SOURCED or ⚙️ EXECUTED evidence |
| 🟡 PLAUSIBLE | No deviation found, but the evidence is only 🔍 SNIPPET, 🧮 or 🧠; not independently verified |
| 🔁 CORRECTED | A deviation was found, repaired and retested |
| ⛔ FAIL-CLOSED | Cannot be made correct or safe; do not use as is |
| ❓ UNVERIFIED | Could not be assessed: missing input, or ⚠️ NO SOURCE FOUND / 🚫 NOT SEARCHED with no other way to test it |

**How 🔁 CORRECTED counts.** For the verdict on the corrected version, a 🔁 CORRECTED point counts as ✅ when the retest rests on 🔎 or ⚙️ evidence, and as 🟡 when it rests on 🔍, 🧮 or 🧠 only.

**FULL mode Phase 2 report**: one table for all 10 points, with a short write-up below it for corrected points only.

| # | Type | BEFORE | AFTER | Source (+ status) | Red-team | Method | Status |
| --- | --- | --- | --- | --- | --- | --- | --- |

---

## Pre-build use (principles research)

When `first-principles-architect` or `docs-first-planner` calls this skill before building, the audit subject is the **request**: *which principles, standards and quality criteria must a result of this kind satisfy, and where do such results usually fail?*

- Select 10 concrete claims, components, parameters and edge-case failure points of the request: 5 High-Impact (ignoring them fails its purpose/audience) and 5 High-Uncertainty (blind assumptions, outdated rules of thumb, disputed guidance). **Orthogonal to D1–D7:** Phase 1.5 runs 7 system-layer searches (D1–D7), while P1–P10 test 10 concrete claims/components/edge cases—producing **17 unique queries** without repeating D1–D7.
- Search each point live with concise 4–6 core-term queries (`search_website(queries_or_urls=[...], auto_open_top=1)`) and open primary sources in full (Principles 4 & 6 apply; delegatable with D1–D7 to a `research`/`self` subagent returning `#schema:` tables). Check authoritative examples and failure patterns without copying examples into the result.
- Report a **criteria register** with **Control Point 1 (2 pros and 2 cons from subject to solution)**: `dimension_or_subtopic | criterion | 2 pros & 2 cons (from subject to solution) | measurable threshold or test | source + status label` across the 3–6 sub-topics and 4 lifecycle safeguards (**Control Point 2** checks 2 pros and 2 cons from subject to solution in intake options, decisions and the pre-delivery/plan check). Unsourced thresholds stay unverified; confidence follows the source label alone (🔎/⚙️ supported; 🔍/⚠️/🚫 open). Keep the register, source gaps and negative declaration compact (wrap long tables in `<details><summary>...</summary></details>`).

---

## Verdict rules (apply in both modes)

- **Verdict on the original output**: how safe it is to act on the AI output *exactly as given*.
  - `RELIABLE`: every point ✅ CONFIRMED, no corrections needed.
  - `USABLE WITH CONDITIONS`: no deviation on any Impact point; deviations or 🟡/❓ only on Uncertainty points (list the conditions).
  - `DO NOT USE`: any Impact point (P1-P5) is 🔁 CORRECTED or ⛔ FAIL-CLOSED.
- **Verdict on the corrected version**: apply the counting rule for 🔁 CORRECTED first, then:
  - `RELIABLE`: every point counts as ✅.
  - `USABLE WITH CONDITIONS`: no point is ⛔ FAIL-CLOSED or ❓ UNVERIFIED on an Impact point, but one or more points count as 🟡. List the conditions, and for every Impact point that counts as 🟡, name the primary source or professional that should confirm it before acting.
  - `DO NOT USE`: any Impact point remains ⛔ FAIL-CLOSED or ❓ UNVERIFIED.
- **Confidence**: High, Medium or Low, based on how many points rest on 🔎 or ⚙️ evidence versus 🔍, 🧮 or 🧠 only. Any 🚫 NOT SEARCHED on an Impact point caps confidence at Low.
- **Source gaps**: number of points with ⚠️ NO SOURCE FOUND and 🚫 NOT SEARCHED, with point numbers, or "none". If not "none", start the line with ⚠️.
- **Cap for high-stakes domains.** For health, safety, legal, financial or irreversible matters, neither verdict can be `RELIABLE` if any Impact point does not count as ✅. Say explicitly which professional or primary source should confirm it.

---

## Compact report (DEFAULT)

Show exactly this, nothing more. Keep it short: aim for roughly one screen. Use the user's language.

1. **Tools line** (one line): which search/execution tools were available. If none: the `⚠️ NO EXTERNAL SOURCES CONSULTED` warning instead.
2. **Verdict** (2 lines): original output → `RELIABLE` / `USABLE WITH CONDITIONS` / `DO NOT USE`; corrected version → same scale. Add Confidence (High/Medium/Low).
3. **Solution / answer to your question**: the corrected, ready-to-use answer to what the user originally asked (the fixed code, recipe, calculation, plan, text, advice, with the right numbers and limits). This is the main part of the report. If the verdict on the corrected version is `DO NOT USE`, say so here and give the safe alternative or who to ask instead of a usable answer.
4. **What was wrong** (max. 5 bullets): only the deviations that were found and fixed, one line each, with the key source (organisation + standard/URL) and its status label (🔎/🔍). If nothing was wrong: "No deviations found."
5. **Before you act** (max. 5 bullets): conditions, assumptions, and the honest gaps: any ⚠️/🚫/🟡/❓ point in one line each (point number + why), failed URLs, and which professional or source should confirm Impact points that are only 🟡. Never leave out a gap to save space.
5b. **Diagnosis** (only when the input contains a failure, see Principle 6): one block `Symptom | Root cause (verified or hypothesis) | Fix | Confirm | Source (standard/authority + 🔎/🔍/⚠️)`, placed before "What was wrong". Keep it to 5 lines.
6. **Source gaps** line (see rules above) and one counts line: `✅ x · 🟡 x · 🔁 x · ⛔ x · ❓ x | 🔎 x · 🔍 x · ⚠️ x · 🚫 x | corrections: x | date`.
7. **Limitation note** (one line): this audit reduces risk but does not replace sign-off by a qualified professional where health, safety, law, money or irreversible actions are involved.
8. **Last line**: "Say 'full report' for the complete 10-point audit trail."

Do not show: the 10-point table, the Phase 2 table, the falsification log, the evidence/attribution table, the execution protocol, or a restatement of the task. Offer them only through the last line.

---

## Full report (only on request)

When the user asks for the full report, show: the Phase 1 table, the Phase 2 table, then these Phase 3 sections:

1. **Evidence and attribution**: table with organisation or author, URL or standard identifier, source status (🔎/🔍) and at most one literal quote of at most 15 words per source. Only quote what you actually read; for 🔍 sources write "no quote, page not opened". Never invent percentages, figures or quotes.
2. **Falsification log**: only mechanisms that produced a deviation and how they were neutralised, plus the total number of mechanisms checked.
3. **Conflicting sources**: only for a real conflict, with the reasoning for the choice (most recent, most authoritative for the jurisdiction, on safety matters the strictest). Otherwise "n/a".
4. **Negative Declaration**: a complete list of what could not be substantiated: assumptions, every 🔍, ⚠️ and 🚫 point with reason and queries tried, every 🧠 and 🧮 point, every 🟡 and ❓ point, and any missing tool. Never shorten this section.
5. **Execution protocol**: at most 10 numbered steps, plus at most 5 Do's and 5 Don'ts.
6. **Audit summary**: the verdicts, confidence, source gaps, counts and limitation note as defined above.
