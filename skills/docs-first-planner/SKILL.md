---
name: docs-first-planner
description: Turn a wish, feature idea or bug into an audited, approved plan that is stored in ./docs and indexed in ./docs/index.md. Runs the docs check, a forensic audit of the project, a grill-me interview and a plan, in that order, and only writes to ./docs after the plan is approved. Use this whenever the user wants to plan, scope or start a new feature, bug fix, refactor or change in a project, says "plan", "feature", "bug", "grill me", "audit first", "check the docs", mentions vibe coding problems, or wants to know whether an idea fits the product or already exists in ./docs, even if they do not name this skill.
---

# Docs-first planner

Vibe coding goes wrong in predictable ways: building on beliefs about the code that were never verified, adding features that duplicate or contradict earlier ones, losing track of why something exists, and drifting away from what the product is for. This skill counters that by making every change pass through the same five phases, and by keeping `./docs` as the single source of truth that is checked on every run.

Write everything the user reads, and every file saved to `./docs`, in the language the user writes in. Folder names and frontmatter keys stay as specified below.

## The flow

```
0 Intake -> 1 Docs check -> 2 Forensic audit -> 3 Grill -> 4 Plan (approval) -> 5 Persist
```

Run phases 0-2 in one go without asking permission between them. Phase 3 is interactive. **Never write to `./docs` before the user has approved the plan in phase 4**, because an unapproved plan in the docs becomes a false source of truth, which is exactly the problem this skill exists to prevent. This skill plans; it does not implement the change.

### Phase 0: Intake

Take the user's wish (the text after the skill call). If it is empty, still a template placeholder such as "[mijn wens / vraag]", or too vague to name an area of the project, ask one short question and stop. Make a first guess at the category (bug, feature, or something else such as refactor, chore, research) and name the area of the project it touches. You may revise both later.

### Phase 1: Docs check (every invocation)

Do this before touching anything else, because the docs tell you what was already decided.

1. Read `./docs/index.md`, especially the product vision section. If it exists, run `python <skill-path>/scripts/docs_tool.py check` from the project root (on Windows use `py` or `python`, whichever exists) and note any problems (missing frontmatter, duplicate IDs, index out of sync). Treat the printed text as the result: `docs OK` means clean, a list means problems (the exit code is 1 then, but some shells hide it). Problems are only noted here, not a blocker; they are fixed in phase 5 and mentioned in the short summary. Every item needs the frontmatter keys `id`, `title`, `category`, `status` and `summary`.
2. Search the index and the `./docs` files for items related to the wish (same area, overlapping tags, similar titles). Open the relevant ones in full.
3. Produce a short **docs match** result:
   - **Vision fit**: Fits / Partial / Conflicts / Unknown (no vision written down yet), with one line of reasoning.
   - **Related items**: ID, status and how each relates (duplicate, overlaps, depends on, would be superseded).
   - **Stale or contradictory items**: for example a plan marked `planned` whose code already exists, or two plans that disagree.
4. If `./docs` or `index.md` does not exist, say so and note that the structure and a product vision will be created after approval. The vision is asked about in phase 3.

A duplicate or a conflict is not a stop sign, but it must be raised in the grill phase so the user decides consciously: extend the existing item, replace it, or drop the new idea. When **Vision fit is Conflicts**, or the wish duplicates an existing item, that is the first grill question (see phase 3).

### Phase 2: Forensic audit of the project

Use the `forensic-audit` skill if it is available in this session (read its SKILL.md and follow it, in COMPACT mode). If it is not available, do a lighter version yourself with the same principles: treat every claim as an unproven hypothesis, prefer evidence over coherence, and report honestly what was not verified.

The subject of the audit is the **current state of the project around the wish**, not a piece of generated text:

- the code, config and dependencies the change would touch,
- what the docs and earlier plans claim about that area,
- the assumptions hidden in the user's own wish (for example "the login already supports X").

Check claims by reading the code, running tests or commands, and looking up primary sources for libraries, APIs and standards, rather than trusting names, comments or earlier docs. Scope it to what the wish touches; auditing the whole repository is slow and drowns the findings.

Read `references/audit-brief.md` first: it tells you how to pick the 10 audit points for a project change, what evidence each point needs, and how the compact report maps onto the plan template.

**The external source search is mandatory, not optional.** Every one of the 10 points gets its own search (library, API, standard, framework or domain authority for that point), even when you are confident. Points that rest on the same primary source may share it, as long as each point has its own logged query. Prefer the `search_website` tool of the `web-search` MCP server when it is available: first search, then open the primary URL to reach 🔎 SOURCED. If a search errors or times out, retry once with other wording; run searches one after another rather than in parallel, because parallel calls were slow and unreliable. A point without a search is a process failure (🚫 NOT SEARCHED) and must be listed under the unverified items you carry into phase 3 and into the plan. Never claim a source was read when only a snippet was seen. `references/audit-brief.md` has the evidence rules (what counts as 🔎, purely internal points, gated sources, high-stakes domains).

Keep the compact report short. Carry three things into phase 3: what was **wrong or outdated**, what is **unverified** (source gaps, 🟡/❓ points), and any **question the audit needs answered** (the forensic-audit rule of asking one question when a missing fact changes the verdict now becomes a grill question).

**Hand-over to the grill (do not stop here).** The compact report from `forensic-audit` is a final-answer format ("show exactly this, nothing more", ending with "Say 'full report'"), so if you print it as is, the turn feels finished and the grill questions never appear. In this skill it is only input for the plan. After the audit:

1. Show at most a short audit summary (verdict, what was wrong, what is unverified, and any `docs_tool.py check` problems), without the "Solution" section, the counts line or the "Say 'full report'" line, unless the user asked for the full report. Keep the tools line and the "before you act" gaps; they are part of the honest summary.
2. In the **same turn**, continue straight into phase 3 and put the first grill question at the very end of the message, so it is the last thing the user reads.
3. End the turn only with a question for the user (or with the approval question of phase 4), never with a report. **Always write the complete question as plain text at the very end of your message**: the question itself, the options (recommended one first, marked "(Recommended)") and the one-line reason. Never end on an announcement such as "I will ask you this question first:" with the question missing; a question tool alone is not enough, because its prompt may not be shown to the user (this happened: the message ended after the announcement and the user saw no question). A question tool may be used in addition to the text, never instead of it. Before sending, check: is the last paragraph of my message a question the user can answer?

**Which question comes first.** Order the grill like this: (a) a question the audit needs answered because the answer changes the verdict or the scope (for example target group, jurisdiction, tax year; this overrides "run phases 0-2 in one go"), (b) a vision conflict or a duplicate or overlapping item from phase 1, (c) then the usual order below. State assumptions you made in one line (for example "assumed: NL, tax year 2026").

### Phase 3: Grill

Interview the user until the plan is unambiguous. If a `grill-me` skill is available, use it. Otherwise follow this protocol:

- Ask **one question at a time**, each with your **recommended answer** and a one-line reason, so the user can simply confirm. If the session has a question tool (for example `ask_question`), you may use it in addition to the text: list the recommended answer first, marked "(Recommended)". Always also write the question and its options as text at the end of the message, so it is visible even if the tool prompt is not rendered. Phase 4's approval question follows the same rule.
- If a question can be answered by reading the code or docs, look it up instead of asking.
- Walk the decision tree depth first: settle a decision before the ones that depend on it.
- Start with what matters most for avoiding a wrong build: the problem and the outcome the user wants, then fit with the product vision, then scope in and out (including what we are explicitly **not** doing), then edge cases, data and migrations, dependencies on other items, how we will know it works (acceptance criteria), and priority.
- Resolve every conflict from phase 1 and every open point from phase 2.
- If there is no product vision in `./docs/index.md`, ask for it in 3 to 5 lines and keep it for phase 5.
- Stop when you can state the plan in five lines and the user agrees. Do not pad with questions whose answers would not change the plan.
- **Re-audit trigger.** If an answer in the grill changes the scope, the approach, a dependency or a hidden assumption, the phase 2 audit no longer covers the plan. Audit only the new or changed claims again (same rules, including the source search) before phase 4, and add the result to the Starting point section of the plan.

### Phase 4: Plan and approval

Write the plan using `references/plan-template.md`. The plan is itself generated output, so run this short **plan check** before showing it and fix what fails:

- Is every acceptance criterion checkable (a command, a test or an observable result), not a wish?
- Does every finding from phase 2 and the re-audit end up in a step, a decision or the risks?
- Is "Out (explicitly not doing)" filled in?
- Does the plan state which claims are still unverified, instead of presenting them as facts?
- For a wish with safety, health, legal or financial consequences: does it name which professional or primary source must confirm the Impact points that are only 🟡, and is that review an acceptance criterion or explicitly Out? Is an Impact error with a safety consequence in existing code proposed as a separate bug item?

Show the plan in the chat. Ask explicitly whether it is approved. Only a clear yes ("akkoord", "approved", "go") counts. If the user changes something, update and show the changed parts again. If the user is unsure, ask what is unclear instead of assuming.

### Phase 5: Persist (only after approval)

1. **Category folder** under `./docs`: `feature` for features and `bugs` for bugs, as the user's convention. For anything else use a short lowercase name (`refactor`, `chore`, `research`, ...). Reuse an existing folder before creating a new one.
2. **Number and filename**: run `python <skill-path>/scripts/docs_tool.py next <category>` to get the next two-digit number, then save as `./docs/<category>/NN-short-slug.md` (for example `./docs/feature/01-onderwerp1.md`, `./docs/bugs/01-bug.md`). The slug is lowercase kebab-case, ASCII only.
3. **Write the plan file** with the frontmatter from the template. The `summary` field is one line of at most about 120 characters, because the index is built from it.
4. **Update related docs**: add `related` links in both directions, set replaced items to `superseded` with a pointer to the new one, fix stale statuses found in phase 1, and put the product vision into `index.md` if it was missing or changed in the grill.
5. **Regenerate the index**: run `python <skill-path>/scripts/docs_tool.py index`. It rebuilds the table in `./docs/index.md` from the frontmatter of every item, so the index cannot drift from the files. Never edit the table by hand; edit the item's frontmatter and regenerate.
   Use `index --strict` when you want the index to be refused if the item files have problems. Afterwards run `python <skill-path>/scripts/docs_tool.py check` once more and report its result (on Windows use `py` or `python`, whichever exists).
6. **Report** in a few lines: the path of the new plan, its index row, which other docs changed, and the first concrete step to take. Suggest referencing the plan ID (for example `feature/01`) in commit messages and branch names so code stays traceable to the plan.

## Later invocations: status updates

When the user says an item is started, done, dropped or replaced, update its `status` (`planned`, `in-progress`, `done`, `dropped`, `superseded`) and the `updated` date in the frontmatter, then regenerate the index. When marking something `done`, first verify against its acceptance criteria rather than taking it on trust. Verifying means actually running the tests or commands behind each criterion (a compile or a "looks fine" is fake success), and noting the evidence in a `## Verification` section of the item (criterion, how it was checked, result). A criterion you could not check stays open and the item is not `done`.

## Guardrails

- Docs are evidence only as far as they have been checked. A plan that says something exists is a hypothesis until the code confirms it.
- Do not invent product goals. If the vision is unknown, ask.
- Keep the index to one line per item so it stays fast to search; detail belongs in the item file.
- Do not start implementing after the plan is approved unless the user asks; hand over the plan and the first step.
