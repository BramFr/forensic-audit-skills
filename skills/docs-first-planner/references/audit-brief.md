# Audit brief for phase 2

How to apply `forensic-audit` to the current state of a project instead of a piece of AI text. Follow the forensic-audit rules (10 points, source search per point, honest labels); this file only adapts the inputs and the output.

## Choosing the 10 points

- **P1-P5 (high impact)**: claims about the code, config, data or dependencies that the change relies on. If one is wrong the change fails or breaks something (for example "the login already supports X", "this table has column Y", "this library version offers Z"). When there is no existing code (greenfield or non-software system), P1-P5 are the governing domain constants, safety/legal thresholds, and primary component properties without which the design fails or becomes unsafe. For a **composite** wish (decomposed in Phase 1.5 into 3 to 6 sub-topics plus 4 lifecycle safeguards), distribute P1-P10 across the sub-topics and lifecycle safeguards so every stage and handoff is audited, and verify **Control Point 1 (2 pros and 2 cons from subject to solution)** for each sub-topic/approach.
- **P6-P10 (high uncertainty)**: assumptions from the user's wish, from `./docs` items marked `planned`/`done`, from comments and names, and anything outdated or unverified (deprecated APIs, old library versions, behaviour that only works in the happy path, or missing lifecycle safeguards such as first-run readiness, scale continuity, environment coexistence or selective sub-topic retry).
- No filler. If the area is small, split a claim into independent sub-claims (the number, the unit, the signature, the config key, the edge case).

## Evidence per point

Every point needs at least one of:
- `file:line` of the code that proves or disproves it (inspected via `compress_context` `--signatures` or symbol extraction),
- the output of a command or test that was actually run,
- a primary source (official docs, spec, release notes) that was opened, not only a search snippet.

A docs item, a comment or a function name is a hypothesis, not evidence. Whereas Phase 1.5's 7 dimension searches (D1–D7) ask layer-specific questions about what each dimension requires, Phase 2's 10 audit-point searches (P1–P10) test 10 concrete claims, components, parameters and edge cases of the wish—always producing distinct queries and never repeating a Phase 1.5 query.

Before running any external search (`search_website(query_or_url="<query>")` or batch `search_website(queries_or_urls=[...])` up to 10 items / `" || "`), check `./docs/index.md` for `## Search keywords` (`compress_context(file_path="docs/index.md", section="Search keywords")`): when present and in the project's domain, include 1 to 3 fitting keywords per query (`{selected keywords} {query}`: 1–2 leading vision/scale priority terms for architecture, UI, workflow or scale queries, or 1–2 **technical/methodological domain terms** such as `primary-source-verification`, `ISO-NEN-IEC`, `IETF-RFC`, `NIST-SP-800`, `OWASP-ASVS`, `Python-stdlib` for external protocol, standard, RFC, library or scientific queries without abstract vision words like `zero-trust` or `no-fake-green`; 0 keywords when present = `🚫 NOT SEARCHED`; for standalone out-of-domain questions, search normally). Keep each DuckDuckGo query concise (**4 to 6 core terms**, one language and one standard/concept per query) and pass `filter_query` when opening long URLs, catalogs or PDFs (`search_website(query_or_url="https://...", filter_query="<keywords>")` or inline `"https://... <keywords>"`) to stay `<= 10.240 B` inline without truncating primary source context.

**Batch Prompting (`arXiv:2511.04108`), DAST/CoD & Step 2B Disconfirmation:** Bundle the 7 (D1–D7) + 10 (P1–P10) queries and delegate the web-research batch to a `research`/`self` subagent using concise *Chain-of-Draft (CoD)* density for structural D1–D7 dimensions and full deep reasoning for P1–P10 claims (without hard `"use at most X tokens"` caps), followed by a **Zero-Trust Context-Purge** returning `#schema:` tables (including **Control Point 1: 2 pros and 2 cons from subject to solution**). On uncertain or legacy rules, run an active **Step 2B Adversarial Disconfirmation** query (*is this norm/method withdrawn, deprecated or superseded?*) and verify: (a) *Existence at time horizon $t$*, (b) *Typology* (strict binding obligation vs. flexible guideline), and (c) *Higher authority*. Record the status (🔎 / 🔍 / ⚠️ / 🚫) as forensic-audit defines it.

## Mapping the compact report onto the plan

| Audit result | Goes into the plan under |
| --- | --- |
| Confirmed or corrected facts (with where) + Control Point 1 | Starting point: Verified / Corrected |
| 🟡, ❓, ⚠️, 🚫 points | Starting point: Unverified, and Risks and open points |
| A question the audit needs answered | A grill question (phase 3) |
| A wrong or outdated docs item | Phase 5: fix the status or supersede it |

## Re-audit after the grill

When the grill changes scope, approach or dependencies, audit only the new or changed claims and merge the result into Starting point. This runs inside the phase 3.5 verification loop (`references/first-principles.md`), which re-searches (including Step 2B disconfirmation) every answer that sets a parameter, limit, target or method.

## Evidence rules (what counts)

- **🔎 holds per claim, not per page.** A page only counts as opened when you saw the text that proves or refutes that claim. Navigation-only, 404 or unmentioned claims are 🔍 at best.
- **Project `## Search keywords` (`./docs/index.md`).** Follow the scoping rule in "Evidence per point" above (`0` project keywords when `## Search keywords` is present and in-domain = `🚫 NOT SEARCHED`).
- **Secondary sources are 🔍.** Commercial pages, blogs or second-hand quotes never give 🔎 for the original claim.
- **Gated or blocked primary sources** (paid standards such as ISO, NEN or IEC, or HTTP 401/403 after retry): always name the formal standard (identifier + title) AND search for its free **open primary counterpart** (the law or regulation referencing it on `wetten.overheid.nl` or `eur-lex.europa.eu`, public standards/regulators such as NIST, UNECE, NCSC, OWASP, NVWA, RDW, NHG or LICG, or the official manufacturer datasheet/manual). If the open primary counterpart proves the claim, record both and mark 🔎 SOURCED; if neither can be opened, record 🔍 plus "primary gated" in the source gaps (at most 🟡, never ✅).
- **No primary source exists** (for example typical brake-pad lifetime in km): ⚠️ NO SOURCE FOUND, status 🟡 or ❓, listed under Unverified in the plan.
- **Purely internal points** (does the feature already exist, what does a docs item claim, does the import work): evidence is `file:line` or command output (⚙️), and an external search is not forced. Not all 10 points may be internal.
- **Domain constants in code** (doses, tax rates, retention periods, cable sizes): the primary source is the domain authority (Farmacotherapeutisch Kompas / NHG, Belastingdienst, NEN / IEC), not library documentation.
- **The core of the wish counts as Impact**, even if uncertain.
- **Verdict on a plan.** `DO NOT USE` describes the current project state ("do not build on this as is"); corrections go into the plan.
- **State assumptions** (jurisdiction, year, target group) in one line, and ask when the answer changes the verdict.
- **Small wishes.** Prefer sub-claims of the wish itself over filler about the rest of the project.

## High-stakes wishes (health, safety, law, money)

- Put the verdict cap and the professional or primary source that must confirm each Impact point that is only 🟡 in the plan (under Starting point Unverified and Risks), and make that confirmation an acceptance criterion or explicitly Out.
- Propose any Impact error with a safety consequence in existing code as a separate bug item in the grill.

## Wishes that contain a failure

- A pasted error, log or symptom is evidence that it happened; the explanation is a hypothesis. Discover the domain and governing standard/authority via live search (`search_website` + Step 2B disconfirmation), quote the failure, find the decisive signal at its origin (not the wrapper), and make the root cause a P1-P5 point with its own primary-source and runtime check.
- Check whether the failure is a deliberate guard. If it is, the fix satisfies the guard and the plan must not weaken it.
- Hand the result over under Starting point and as the Observed error and Root cause sections of a bug plan.

## Changes that add or reshape modules

- Treat "this module/function/type does not exist yet" as an Impact claim: prove it with a project-wide search for the symbol, concept and likely synonyms, and walk the **Simplicity Ladder** (YAGNI -> DRY -> Stdlib -> Native -> Existing Dependencies -> Minimal Code + LBYL) before adding any new module.
- Treat claimed boundaries as claims too: check real imports with a search, not names, comments or an existing `MODULE.md`.
- If `MODULE.md` files already exist in the touched area, read their headers first; a contract that disagrees with the code goes under Corrected in Starting point.
