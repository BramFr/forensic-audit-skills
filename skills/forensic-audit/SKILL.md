---
name: forensic-audit
description: Critically audit, fact-check and verify AI-generated output in any domain (code, recipes, designs, plans, calculations, advice, texts, contracts, data) for factual errors, outdated standards, unsafe or illegal advice and fake success. Use whenever the user wants something checked, reviewed, fact-checked, audited, validated or double-checked ("is this correct?", "check this", "can I trust this?", "is this safe?", "audit this", "fact-check this"), even if the word audit is not used, and always before anyone acts on AI advice with consequences for health, safety, money, law or anything irreversible.
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
Do not pause mid-audit to ask permission to continue ("shall I proceed to step 2?"). There is one exception: if a missing fact would change the outcome of the audit (jurisdiction, product version, dosage, age, load, tax year), ask ONE concise question before starting instead of guessing. If the gap is minor, state your assumption in one line, continue, and list it under the open points.

**2. Treat every earlier claim as an unproven hypothesis.**
Claims in the output, and in the earlier conversation, are not evidence. Do not try to please the user: factual, physical and legal correctness matters more than a pleasant answer.

**3. Reject fake success.**
Code that compiles but fails at runtime, or a recipe, text or plan that sounds plausible but fails in practice, is not a pass. A pass needs proof (a calculation, an executed test, a primary source), not just coherence.

**4. Always search for external sources, and report honestly what was found.**
Searching is mandatory for every one of the 10 audit points, including points you are confident about. Your own knowledge is a starting hypothesis, never the final evidence. Check once, before Phase 1, which tools you actually have in this session (including lazy-loaded MCP servers such as `web-search` / `search_website`, built-in web search, page fetch, code execution, file access). When the `search_website` MCP tool is available (eagerly or via `call_mcp_tool` on server `web-search`), always prefer it over built-in search or fetch tools.

For every point, track two things: the **source status** and the **method**.

*Source status* (mandatory per point):

| Label | Meaning |
| --- | --- |
| 🔎 SOURCED | A primary source was opened and read in this session (the actual page, document or standard, not only a search-result summary) |
| 🔍 SNIPPET | A search was run and the result points to a primary source, but only the search-result summary was seen; the page itself was not opened |
| ⚠️ NO SOURCE FOUND | A search was run, but no primary source confirming or refuting the claim was found |
| 🚫 NOT SEARCHED | No search was run for this point (no search tool available, search failed, or skipped). This is a **process failure** and must be flagged as such |

*Method*:

| Label | Meaning |
| --- | --- |
| ⚙️ EXECUTED | Actually run or calculated with a tool |
| 🧮 HAND-CALCULATED | Calculated by hand; the calculation is shown |
| 🧠 REASONED | Based on own knowledge or reasoning, not independently tested |

Rules:
- Never write that something was searched, opened, executed or measured when it was not. Never present a search-result summary as if you read the primary source.
- Try to reach 🔎 using a two-step flow: first run `search_website("<query>")` to get DuckDuckGo results (🔍 SNIPPET), then pass the most authoritative primary `http(s)` URL (HTML or PDF) to `search_website("https://...")` to read the full primary source in Markdown (🔎 SOURCED). Use 🔍 only when opening is not possible.
- **Fail-closed on `ERROR:`**: if `search_website("https://...")` (or any fetch tool) returns an `ERROR:` response (HTTP 403, timeout, unextractable JS-only page), it **never** counts as 🔎 SOURCED. Either open a second primary URL from the results, or fall back to 🔍 SNIPPET (or ⚠️ NO SOURCE FOUND) and record the failed URL and reason in the open points.
- Search in at least two ways before concluding ⚠️ NO SOURCE FOUND (different wording, the language of the relevant jurisdiction, the name of the standard or authority). Record the queries tried.
- A point with ⚠️ NO SOURCE FOUND or 🚫 NOT SEARCHED can never be ✅ CONFIRMED. Every such point is listed, with the reason, in the open points and in the **Source gaps** line.
- **No search tool at all**: every point becomes 🚫 NOT SEARCHED. Put this warning at the very top of the report: `⚠️ NO EXTERNAL SOURCES CONSULTED — this audit rests on reasoning only`. For each point, name the primary source the user should check.
- **No code execution**: do the calculation by hand (🧮). For physical or chemical claims you can only predict, not measure, so say which real-world test would confirm it.

**5. Keep the report compact, but never at the expense of honesty.**
Compactness never applies to warnings, source gaps, open points or a DO NOT USE verdict. These always appear, even in COMPACT mode.

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

**Step 3: Primary source check (mandatory for every point).** Pick the authority type that fits: *Legal/Normative* (ISO/NEN, building codes, EU law, HACCP), *Technical* (datasheets, API docs, RFCs, release notes), *Scientific* (peer-reviewed work), *Trade/Guild* or *Safety/Audit* (NIST, OWASP, food-safety and public-health bodies). Search for the latest version of the standard or guideline, preferring the authority of the relevant jurisdiction, and then open the primary URL to verify the actual text. Use primary sources only; marketing blogs, forums, shops and SEO content do not count as a source (they may at most point you to one). Note source + identifier or URL + source status label.

**Step 4: Red-team.** Try to disprove the point, using the archetype that fits: *Edge-case stress test*, *Ageing and deprecation* (withdrawn standards, deprecated APIs), *Silent failures and side effects*, *Adversarial abuse* (operator error, environment, safety) or *Efficiency falsification*. Compare BEFORE and AFTER with the sources from Step 3.

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
