# Audit brief for phase 2

How to apply `forensic-audit` to the current state of a project instead of a piece of AI text. Follow the forensic-audit rules (10 points, source search per point, honest labels); this file only adapts the inputs and the output.

## Choosing the 10 points

- **P1-P5 (high impact)**: claims about the code, config, data or dependencies that the change relies on. If one is wrong the change fails or breaks something (for example "the login already supports X", "this table has column Y", "this library version offers Z"). When there is no existing code (greenfield or non-software system), P1-P5 are the governing domain constants, safety/legal thresholds, and primary component properties without which the design fails or becomes unsafe.
- **P6-P10 (high uncertainty)**: assumptions from the user's wish, from `./docs` items marked `planned`/`done`, from comments and names, and anything outdated or unverified (deprecated APIs, old library versions, behaviour that only works in the happy path).
- No filler. If the area is small, split a claim into independent sub-claims (the version, the signature, the config key, the edge case).

## Evidence per point

Every point needs at least one of:

- `file:line` of the code that proves or disproves it,
- the output of a command or test that was actually run,
- a primary source (official docs, spec, release notes) that was opened, not only a search snippet.

A docs item, a comment or a function name is a hypothesis, not evidence. Before running any external search (`search_website(query_or_url="<query>")`), check whether `./docs/index.md` exists with a `## Search keywords` section (using `compress_context(file_path="docs/index.md", section="Search keywords")` when available): when present and the request is in the project's domain, include 1 to 3 fitting keywords per query (`{selected keywords} {query}`: 1–2 leading vision/scale priority terms for architecture/UI/scale/performance queries, or 1–2 technical domain terms for protocol/RFC/spec queries; sending 0 keywords when present counts as `🚫 NOT SEARCHED`; for standalone questions outside the project's domain, search normally without project keywords). When opening `http(s)` URLs via `search_website(query_or_url="https://...", filter_query="<keywords>")` (or inline `"https://... <keywords>"`), pass `filter_query` on long pages, catalogs or PDFs to keep outputs under 10 KB. Run the search for every point and record the status (🔎 / 🔍 / ⚠️ / 🚫) as forensic-audit defines it.

## Mapping the compact report onto the plan

| Audit result | Goes into the plan under |
| --- | --- |
| Confirmed or corrected facts (with where) | Starting point: Verified / Corrected |
| 🟡, ❓, ⚠️, 🚫 points | Starting point: Unverified, and Risks and open points |
| A question the audit needs answered | A grill question (phase 3) |
| A wrong or outdated docs item | Phase 5 step 4: fix the status or supersede it |

## Re-audit after the grill

When the grill changes scope, approach or dependencies, audit only the new or changed claims (a smaller set of points is fine, the rules per point stay the same) and merge the result into the same Starting point section. This runs inside the phase 3.5 verification loop (`references/first-principles.md`), which also re-searches every answer that sets a parameter, limit, target or method.

## Evidence rules (what counts)

- **🔎 holds per claim, not per page.** A page only counts as opened when you saw the text that proves or refutes that claim (grep the fetched output for it). A page that returned only navigation, a 404 text, an empty list or no mention of the claim is 🔍 at best.
- **Project `## Search keywords` (`./docs/index.md`).** If `./docs/index.md` has `## Search keywords`, every external query must include 1–3 matching keywords from that list (1–2 leading vision/scale priority terms from the start of the list for architecture/UI/scale/performance queries, or 1–2 technical domain terms for protocol/RFC/spec queries, stripping `+` punctuation); a query sent with 0 project keywords when `## Search keywords` is present counts as `🚫 NOT SEARCHED`.
- **Secondary sources are 🔍.** A commercial or knowledge-base page, or a primary source seen only through someone else's quote (for example a drug compendium quoting a guideline), never gives 🔎 for the original claim.
- **Gated or blocked primary sources** (paid standards such as ISO, NEN or IEC, or HTTP 401/403 after one retry): always name the formal standard (identifier + title) AND search for its free **open primary counterpart** (the law or regulation referencing it on `wetten.overheid.nl` or `eur-lex.europa.eu`, public standards/regulators such as NIST, UNECE, NCSC, OWASP, NVWA, RDW, NHG or LICG, or the official manufacturer datasheet/manual). If the open primary counterpart proves the claim, record both and mark 🔎 SOURCED; if neither can be opened, record 🔍 plus "primary gated" in the source gaps (at most 🟡, never ✅).
- **No primary source exists** (for example typical brake-pad lifetime in km): ⚠️ NO SOURCE FOUND, status 🟡 or ❓, listed under Unverified in the plan. Do not upgrade it with marketing pages.
- **Purely internal points** (does the feature already exist, what does a docs item claim, does the import work): evidence is `file:line` or the output of a command (⚙️), and an external search is not forced. Not all 10 points may be internal; pick points that can be checked externally for the rest.
- **Domain constants in code** (doses, tax rates, retention periods, cable sizes): the primary source is the domain authority (for example Farmacotherapeutisch Kompas / NHG, Belastingdienst, NEN / IEC), not the library documentation.
- **The core of the wish counts as Impact**, even if it is very uncertain. If the wish is "pick the right rate per category", the category mapping is a P1-P5 point.
- **Verdict on a plan.** The "verdict on the original output" here describes the current state of the project. `DO NOT USE` means "do not build on this as is", it does not stop the planning; the corrections go into the plan.
- **State assumptions** the audit needed (jurisdiction, year, target group) in one line, and ask when the answer would change the verdict.
- **Small wishes.** Prefer sub-claims of the wish itself (the number, the unit, the condition, the exception) over filler about the rest of the project; mention what you left out of scope.

## High-stakes wishes (health, safety, law, money)

- Put the verdict cap and the professional or primary source that must confirm each Impact point that is only 🟡 in the plan: under Starting point (Unverified) and under Risks and open points.
- Make that confirmation an acceptance criterion or explicitly Out, never silently skipped.
- An Impact error with a safety consequence in code that is already in use (a wrong dose, a too thin cable) is a separate bug item proposed in the grill, so it is not buried inside the new feature.

## Wishes that contain a failure

- A pasted error, log or symptom is evidence that it happened; the explanation of it is a hypothesis. Discover the domain and governing standard/authority via live search (`search_website`), quote the failure, find the decisive signal at its origin (not the wrapper), and make the root cause a P1-P5 point with its own primary-source and runtime check.
- Check whether the failure is a deliberate guard. If it is, the fix satisfies the guard and the plan must not weaken it.
- Hand the result over under Starting point (Verified, Corrected, Unverified) and as the Observed error and Root cause sections of a bug plan.

## Changes that add or reshape modules

- Treat "this module/function/type does not exist yet" as an Impact claim: prove it with a project-wide search for the symbol, the concept and likely synonyms, and report the hits. Duplicated or double-implemented features are the typical vibe-coding failure, so a missing search is a process failure here.
- Treat claimed boundaries as claims too: "nothing else imports this", "A does not depend on B". Check them with a search of the real imports, not with names, comments or an existing `MODULE.md`.
- If `MODULE.md` files already exist in the touched area, read their headers first. A contract that disagrees with the code goes under Corrected in Starting point, and the plan fixes one of the two.
