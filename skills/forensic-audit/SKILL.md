---
name: forensic-audit
description: Critically audit, fact-check and verify AI-generated output in any domain (code, recipes, designs, plans, calculations, advice, texts, contracts, data) for factual errors, outdated standards, unsafe or illegal advice and fake success. Use whenever the user wants something checked, reviewed, fact-checked, audited, validated or double-checked ("is this correct?", "check this", "can I trust this?", "is this safe?", "audit this", "fact-check this"), even if the word audit is not used, and always before anyone acts on AI advice with consequences for health, safety, money, law or anything irreversible.
---

# Forensic Audit (universal)

Take any AI-generated output, in any domain, and test it before someone acts on it. The goal is not a reassuring stamp but an honest picture of what is proven, what is merely plausible and what is wrong. AI output often sounds more certain than it is, so an audit that also sounds certain without evidence adds nothing.

Write the report in the language the user is writing in.

---

## Principles

**1. Run in one go, but ask when a missing input changes the verdict.**
Do not pause mid-audit to ask permission to continue ("shall I proceed to step 2?"); that only slows the user down. There is one exception: if a missing fact would change the outcome of the audit (jurisdiction, product version, dosage, age, load, tax year), ask ONE concise question before starting instead of guessing. If the gap is minor, state your assumption in one line, continue, and list it under the Negative Declaration in Phase 3.

**2. Treat every earlier claim as an unproven hypothesis.**
Claims in the output, and in the earlier conversation, are not evidence. Do not try to please the user: factual, physical and legal correctness matters more than a pleasant answer.

**3. Reject fake success.**
Code that compiles but fails at runtime, or a recipe, text or plan that sounds plausible but fails in practice, is not a pass. A pass needs proof (a calculation, an executed test, a primary source), not just coherence.

**4. Always search for external sources, and report honestly what was found.**
Searching is mandatory for every one of the 10 audit points, including points you are confident about. Your own knowledge is a starting hypothesis, never the final evidence. Check once, before Phase 1, which tools you actually have in this session (web search, page fetch, code execution, file access) and state them in one line at the top of the report.

For every point, report two things: the **source status** (did an external source back it up?) and the **method** (how was the claim itself tested?).

*Source status* (Step 3, mandatory per point):

| Label | Meaning |
| --- | --- |
| 🔎 SOURCED | A primary source was opened and read in this session (the actual page, document or standard, not only a search-result summary) |
| 🔍 SNIPPET | A search was run and the result points to a primary source, but only the search-result summary was seen; the page itself was not opened |
| ⚠️ NO SOURCE FOUND | A search was run, but no primary source confirming or refuting the claim was found |
| 🚫 NOT SEARCHED | No search was run for this point (no search tool available, search failed, or skipped). This is a **process failure** and must be flagged as such |

*Method* (Step 2, per point):

| Label | Meaning |
| --- | --- |
| ⚙️ EXECUTED | Actually run or calculated with a tool |
| 🧮 HAND-CALCULATED | Calculated by hand; the calculation is shown in the table cell |
| 🧠 REASONED | Based on own knowledge or reasoning, not independently tested |

Rules:
- Never write that something was searched, opened, executed or measured when it was not. Never present a search-result summary as if you read the primary source.
- Try to reach 🔎: when a search returns a relevant primary source and a fetch tool is available (such as `search_website` with a URL, or a page-fetch tool), open it. If `search_website` is available, pass a query string to search DuckDuckGo (🔍) and then pass the target `http(s)` URL (HTML or PDF) to `search_website` to read the full primary source in Markdown (🔎). Use 🔍 only when opening is not possible.
- Search in at least two ways before concluding ⚠️ NO SOURCE FOUND (for example different wording, the language of the relevant jurisdiction, or the name of the standard or authority). Report the queries tried in the Negative Declaration.
- A point with ⚠️ NO SOURCE FOUND or 🚫 NOT SEARCHED can never be ✅ CONFIRMED. Every such point is listed, with the reason, in the Negative Declaration and in the **Source Gaps** line of the Audit Summary.
- **No search tool at all**: every point becomes 🚫 NOT SEARCHED. Put a clear warning at the very top of the report: `⚠️ NO EXTERNAL SOURCES CONSULTED — this audit rests on reasoning only`. For each point, name the primary source the user should check (standard, datasheet, regulation, authority).
- **No code execution**: do the calculation by hand and show it in the table cell (🧮). For physical or chemical claims you can only predict, not measure, so say which real-world test would confirm it.

**5. Keep the report compact, but never at the expense of honesty.**
Do all steps of Phase 2 fully, but report conclusions only. No restating of the task, no introduction, no method explanation. At most one line per step per point, tables and keywords instead of full sentences. A point that passes on the first run gets one line. Only on a deviation do you show what deviated, what changed and the retest. Give the written-out five-step analysis only when the user asks for a "full report" or "audit trail". Compactness never applies to the Negative Declaration, source gaps or warnings.

---

## Phase 1: Select exactly 10 audit points

Analyse `<USER_REQUEST>` (what is wanted) and `<AI_GENERATED_OUTPUT>` (what was proposed). Select exactly 10 points, split in two groups:

1. **5 High-Impact points (P1-P5)**: the components that make the whole thing crash, fail or become unsafe if they are not correct.
2. **5 High-Uncertainty points (P6-P10)**: the components with the most blind assumptions, missing evidence, complex boundary conditions, outdated methods or risk of fake success.

**No filler points.** Always select 10, so the output is searched thoroughly. If the output contains fewer than 10 obvious risk areas, do not pick trivial points (taste, style, wording). Instead split a serious component into separate, independently checkable sub-claims, for example the number, the unit, the condition it applies under, the time limit, the target group and the exception. A smaller output gets a deeper audit, not a shallower one.

Report one table: `# | Type (Impact/Uncertainty) | Audit point | Reason (max. 10 words)`.

---

## Phase 2: Audit each point, one by one

Work through the 10 points in order. Do the five steps internally for each point.

**Step 1: Baseline "BEFORE".** Separate proven facts from assumptions; note the exact starting state, the hard limits (laws, tolerances, capacity), the expected change, and the main failure mechanisms (pre-mortem). Report in one line: key value + biggest risk.

**Step 2: Simulation "AFTER".** Pick the archetype that fits: *Physical/Chemical*, *Digital runtime* (actually run code, queries, payloads), *Process/Workflow*, *Quantitative/Normative* (exact calculation against a limit) or *Adversarial/Stress test*. Perform it and report the result as a value or outcome in one line, with the method label from Principle 4.

**Step 3: Primary source check (mandatory for every point).** Pick the authority type that fits: *Legal/Normative* (ISO/NEN, building codes, EU law, HACCP), *Technical* (datasheets, API docs, RFCs, release notes), *Scientific* (peer-reviewed work), *Trade/Guild* or *Safety/Audit* (NIST, OWASP, food-safety and public-health bodies). Search for the latest version of the standard or guideline, preferring the authority of the relevant jurisdiction. Use primary sources only; marketing blogs, forums, shops and SEO content do not count as a source (they may at most point you to one). Report source + identifier or URL + source status label in one line. If nothing was found, write `⚠️ NO SOURCE FOUND` with the queries tried; if no search was done, write `🚫 NOT SEARCHED` with the reason.

**Step 4: Red-team.** Try to disprove the point, using the archetype that fits: *Edge-case stress test*, *Ageing and deprecation* (withdrawn standards, deprecated APIs), *Silent failures and side effects*, *Adversarial abuse* (operator error, environment, safety) or *Efficiency falsification* (outdated or costly versus the current best practice). Compare BEFORE and AFTER with the sources from Step 3. Report archetype + outcome in one line.

**Step 5: Decide.**
- *No deviation*: assign a status (below) and continue to the next point.
- *Deviation*: repair it (redesign, tighter limits, substituting a component or method, recalibrating a parameter, or a fail-closed fallback) and go back to Step 1 for this point. Report only: what deviated, what was changed, retest result. After two failed repair rounds, set the point to ⛔ FAIL-CLOSED rather than looping further.

**Status per point.** Status reflects the evidence, not just the absence of problems:

| Status | Use when |
| --- | --- |
| ✅ CONFIRMED | No deviation, and backed by 🔎 SOURCED or ⚙️ EXECUTED evidence |
| 🟡 PLAUSIBLE | No deviation found, but the evidence is only 🔍 SNIPPET, 🧮 or 🧠; not independently verified |
| 🔁 CORRECTED | A deviation was found, repaired and retested |
| ⛔ FAIL-CLOSED | Cannot be made correct or safe; do not use as is |
| ❓ UNVERIFIED | Could not be assessed: missing input, or ⚠️ NO SOURCE FOUND / 🚫 NOT SEARCHED with no other way to test it |

**How 🔁 CORRECTED counts.** A correction is only as strong as the evidence behind the retest. For the verdict on the corrected version, a 🔁 CORRECTED point counts as ✅ when the retest rests on 🔎 or ⚙️ evidence, and as 🟡 when it rests on 🔍, 🧮 or 🧠 only. Always show which applies in the Source column.

**Phase 2 report**: one table for all 10 points, with a short write-up below it for corrected points only.

| # | Type | BEFORE | AFTER | Source (+ status) | Red-team | Method | Status |
| --- | --- | --- | --- | --- | --- | --- | --- |

---

## Phase 3: Handover (compact)

Close with these six sections:

1. **Evidence and attribution**: one table with organisation or author, URL or standard identifier, source status (🔎/🔍) and at most one literal quote of at most 15 words per source. Only quote what you actually read; for 🔍 sources write "no quote, page not opened". Never invent percentages, figures or quotes.
2. **Falsification log**: only mechanisms that produced a deviation and how they were neutralised, plus the total number of mechanisms checked.
3. **Conflicting sources**: only for a real conflict, with the reasoning for the choice made (as a rule: the most recent, the most authoritative for the jurisdiction, and on safety matters the strictest). Otherwise "n/a".
4. **Negative Declaration**: an honest, complete list of what could not be substantiated: assumptions made, every 🔍, ⚠️ and 🚫 point with the reason and the queries tried, every 🧠 and 🧮 point, every 🟡 and ❓ point, and any missing tool. Never shorten this section.
5. **Execution protocol**: at most 10 numbered steps, plus at most 5 Do's and 5 Don'ts.
6. **Audit summary** (replaces a pass stamp):
   - **Verdict on the original output**: how safe it is to act on the AI output *exactly as given*.
     - `RELIABLE`: every point ✅ CONFIRMED, no corrections needed.
     - `USABLE WITH CONDITIONS`: no deviation on any Impact point; deviations or 🟡/❓ only on Uncertainty points (conditions listed).
     - `DO NOT USE`: any Impact point (P1-P5) is 🔁 CORRECTED or ⛔ FAIL-CLOSED. An output that needed a correction on an Impact point was wrong where it mattered most, even if the error could be repaired.
   - **Verdict on the corrected version**: how safe it is to act on the audit's corrected version and execution protocol. Apply the counting rule for 🔁 CORRECTED above first, then:
     - `RELIABLE`: every point counts as ✅.
     - `USABLE WITH CONDITIONS`: no point is ⛔ FAIL-CLOSED or ❓ UNVERIFIED on an Impact point, but one or more points (Impact or Uncertainty) count as 🟡. List the conditions, and for every Impact point that counts as 🟡, name the primary source or professional that should confirm it before acting.
     - `DO NOT USE`: any Impact point remains ⛔ FAIL-CLOSED or ❓ UNVERIFIED.
   - **Confidence**: High, Medium or Low, based on how many points rest on 🔎 or ⚙️ evidence versus 🔍, 🧮 or 🧠 only. Any 🚫 NOT SEARCHED on an Impact point caps confidence at Low.
   - **Source gaps**: the number of points with ⚠️ NO SOURCE FOUND and 🚫 NOT SEARCHED, with point numbers, or "none". If this is not "none", start the line with ⚠️.
   - Counts: points per status, per source status and per method, number of corrections, today's date.
   - One-line limitation note: this audit reduces risk but does not replace sign-off by a qualified professional where health, safety, law, money or irreversible actions are involved.

**Cap for high-stakes domains.** For health, safety, legal, financial or irreversible matters, neither verdict can be `RELIABLE` if any Impact point (P1-P5) does not count as ✅ (per the rules above). In that case, say explicitly which professional or primary source should confirm it.
