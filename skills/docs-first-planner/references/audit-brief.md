# Audit brief for phase 2

How to apply `forensic-audit` to the current state of a project instead of a piece of AI text. Follow the forensic-audit rules (10 points, source search per point, honest labels); this file only adapts the inputs and the output.

## Choosing the 10 points

- **P1-P5 (high impact)**: claims about the code, config, data or dependencies that the change relies on. If one is wrong the change fails or breaks something (for example "the login already supports X", "this table has column Y", "this library version offers Z").
- **P6-P10 (high uncertainty)**: assumptions from the user's wish, from `./docs` items marked `planned`/`done`, from comments and names, and anything outdated or unverified (deprecated APIs, old library versions, behaviour that only works in the happy path).
- No filler. If the area is small, split a claim into independent sub-claims (the version, the signature, the config key, the edge case).

## Evidence per point

Every point needs at least one of:

- `file:line` of the code that proves or disproves it,
- the output of a command or test that was actually run,
- a primary source (official docs, spec, release notes) that was opened, not only a search snippet.

A docs item, a comment or a function name is a hypothesis, not evidence. Run the search for every point and record the status (🔎 / 🔍 / ⚠️ / 🚫) as forensic-audit defines it.

## Mapping the compact report onto the plan

| Audit result | Goes into the plan under |
| --- | --- |
| Confirmed or corrected facts (with where) | Starting point: Verified / Corrected |
| 🟡, ❓, ⚠️, 🚫 points | Starting point: Unverified, and Risks and open points |
| A question the audit needs answered | A grill question (phase 3) |
| A wrong or outdated docs item | Phase 5 step 4: fix the status or supersede it |

## Re-audit after the grill

When the grill changes scope, approach or dependencies, audit only the new or changed claims (a smaller set of points is fine, the rules per point stay the same) and merge the result into the same Starting point section.
