# Plan template

Use this structure for every item saved to `./docs/<category>/NN-slug.md`. Write the content in the user's language. Keep the frontmatter exactly as shown, because `scripts/docs_tool.py` builds the index from it. `summary` and `tags` are what is read first (see progressive reading in `SKILL.md`), so make them specific.

- **Slim Plan-Read (`compress_context`):** An unfiltered `compress_context(file_path="docs/<category>/NN-slug.md")` call automatically returns a **slim plan-read** (frontmatter + `## Why` + 2-column `## Decisions` (`Question | Decision`) + `## Scope (Out)` + `## Risks and open points` + `## Relations`, omitting the heavy sections `## Starting point`, `Decisions (Reason)`, `Scope (In)`, `## Approach`, `## Acceptance criteria`, and `## Verification`). Load heavy sections on demand via `section="Decisions,Scope,Approach,Acceptance criteria"` or `section="--all"`.
- **Slim Phase-4 Chat Presentation:** In Phase 4 (before user approval), show only the concise plain-language summary in chat (`id`/`title`/`summary`, `## Why`, compact overview of decisions/approach, and `## Risks and open points`) without dumping the full heavy sections (`## Starting point`, `## Decisions`, `## Scope`, `## Approach`, `## Acceptance criteria`) into the chat message; write the complete template below to disk in Phase 5 after approval.

```markdown
---
id: feature/01
title: Short, specific title
category: feature
status: planned
summary: One line (max ~120 chars) saying what this is and why, for the index.
tags: [area, component, keyword]
created: 2026-01-31
updated: 2026-01-31
related: [bugs/02]
---

# Short, specific title

## Why
The problem or goal in 2-4 sentences, and how it supports the product vision
(quote the relevant line from index.md).

## Starting point (audit findings)
- Verified: facts about the current code/docs that were checked, with where (file, command, source), plus **Control Point 1 (2 pros and 2 cons from subject to solution)** per topic/sub-topic.
- Corrected: earlier beliefs or docs that turned out wrong or outdated.
- Unverified: what could not be confirmed, and why.

## Decisions (from the grill — Control Point 2: include 2 pros and 2 cons from subject to solution)
| Question | Decision | Reason (incl. 2 pros & 2 cons from subject to solution) |
| --- | --- | --- |

## Scope
- In:
- Out (explicitly not doing):

## Scaffold (only when the plan creates or reshapes modules)
Technical choices, tree, dependency direction, boundaries and key interfaces, as in `scaffold-template.md`. Omit this section for changes inside one existing module.

## Approach
Numbered steps, each small enough to be done and checked on its own. When a scaffold exists, make it one step per module, so each module can be generated in one pass from its contract. File or deliverable implementation steps are delegated to a clean execution subagent with a lossless `compress_context` Subagent Context Pack (`mcp/context-compressor`).
1. ...

## Acceptance criteria
Checkable statements. How we will know it works, including the edge cases agreed on.
- [ ] ...
  Check: `<command>` -> `<expected result>`

## Risks and open points
- ...

## Relations
- Depends on / overlaps / supersedes: `bugs/02`, ...
```

**Check lines.** Under a criterion, an optional line `Check: <command> -> <expected result>` makes it re-checkable by the regression check of `SKILL.md`. Without a `Check:` line the criterion is manual: it stays open until a person confirms it and never counts as passed on its own. Use only safe, local, read-only commands appropriate to the project and domain (for example `docs_tool.py check`, `grep` / `Select-String`, `git status`, or side-effect-free validators and tests); never put secrets, production addresses or commands that write, delete or deploy in a `Check:` line.

For bugs, replace "Why" with **Symptom, expected behaviour, how to reproduce** and add a **Root cause** line that states whether the cause is verified or still a hypothesis. Add an **Observed error** section with the failure text verbatim and masked, then the seven steps as lines: Discover (domain, subject, formal standard/authority and open primary source with 🔎/🔍/⚠️), Quote, Signal, Guard (is it a deliberate control that must stay?), Hypotheses (with the test per cause), Fix, Confirm (how the original failure is shown to be gone).

## Index format

`./docs/index.md` has four parts: the product vision, `## Standing constraints` (active project-wide invariants/exclusions with source item IDs, validated by `docs_tool.py check`), `## Search keywords` (maintained by the planner), and the regenerated tables.

```markdown
# Docs index

## Product vision
3-5 lines: what the product is for, who it is for, what it is not.

## Standing constraints
| ID | Constraint (DO NOT / MUST) | Source |
| --- | --- | --- |
| INV-01 | Hard project-wide exclusion or mandatory invariant. | bugs/01 |

## Search keywords
[vision-term-1, scale-term-2, domain-term-3, ...]

## Items
<!-- INDEX:START -->
| ID | Status | Title | Summary | Tags |
| --- | --- | --- | --- | --- |
| [feature/01](feature/01-onderwerp1.md) | planned | ... | ... | ... |
<!-- INDEX:END -->
```

One row per line, so `grep` on a keyword finds the item directly.
