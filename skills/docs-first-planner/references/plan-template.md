# Plan template

Use this structure for every item saved to `./docs/<category>/NN-slug.md`. Write the content in the user's language. Keep the frontmatter exactly as shown, because `scripts/docs_tool.py` builds the index from it.

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
- Verified: facts about the current code/docs that were checked, with where (file, command, source).
- Corrected: earlier beliefs or docs that turned out wrong or outdated.
- Unverified: what could not be confirmed, and why.

## Decisions (from the grill)
| Question | Decision | Reason |
| --- | --- | --- |

## Scope
- In:
- Out (explicitly not doing):

## Approach
Numbered steps, each small enough to be done and checked on its own.
1. ...

## Acceptance criteria
Checkable statements. How we will know it works, including the edge cases agreed on.
- [ ] ...

## Risks and open points
- ...

## Relations
- Depends on / overlaps / supersedes: `bugs/02`, ...
```

For bugs, replace "Why" with **Symptom, expected behaviour, how to reproduce** and add a **Root cause** line that states whether the cause is verified or still a hypothesis.

## Index format

`./docs/index.md` has two parts. The skill writes the vision once and keeps it; the table is regenerated.

```markdown
# Docs index

## Product vision
3-5 lines: what the product is for, who it is for, what it is not.

## Items
<!-- INDEX:START -->
| ID | Status | Title | Summary | Tags |
| --- | --- | --- | --- | --- |
| [feature/01](feature/01-onderwerp1.md) | planned | ... | ... | ... |
<!-- INDEX:END -->
```

One row per line, so `grep` on a keyword finds the item directly.
