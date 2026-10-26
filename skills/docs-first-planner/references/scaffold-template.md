# Scaffold template

Use this when a plan creates or reshapes modules (folders, packages, crates, components). It turns the plan into a blueprint an agent can build from in one pass, because agents are weak at stepwise refactoring of a messy codebase but strong at generating a complete module from a clear contract. Skip it for small changes inside one existing module.

The scaffold has two parts: a **Scaffold section** inside the plan (reviewed and approved with the plan) and, after approval, one **`MODULE.md`** per module folder (the standing contract that later agents read).

## Questions to the user

The scaffold is architect work, and the user is usually not an architect. Do not hand them the blank form. Work the options out yourself, recommend one, and ask in plain language as described in the grill phase of `SKILL.md` (situation, options with practical consequences, recommendation, "or you decide"). Fill the technical choices table below from their answers about needs, not from architect vocabulary.

## 1. Scaffold section in the plan

```markdown
## Scaffold
Technical choices (fixed here so the agent does not pick them at random; reuse what the project already uses):
| Choice | Decision | Why (in the user's situation) |
| --- | --- | --- |
| Database | e.g. SQLite | one user, simple backups |
| Framework / language | ... | ... |
| Hosting / deployment | ... | ... |

Tree (new or changed folders only):
    src/
      lexer/    MODULE.md  token.<ext>
      parser/   MODULE.md

Dependency direction (arrow = may import): parser -> lexer. No cycles.

| Module | Does | Does NOT do | May depend on |
| --- | --- | --- | --- |
| src/lexer | text -> tokens | parsing, I/O | (nothing) |
| src/parser | tokens -> tree | reading files | src/lexer |

Key interfaces (signatures and data shapes only, no bodies):
    Token { kind, text, span }
    lex(source: str) -> list[Token]

Existing code searched for overlap: <pattern/symbol searched, hits, decision: reuse / extend / new>
```

Scaffold check (part of the plan check): every technical choice has a reason; no module does too much (a God object has several unrelated items in "Does": split it); no module appears twice or overlaps another's "Does"; the dependency arrows have no cycle; every interface used by a module is defined once; for each "Does NOT do" or forbidden dependency there is a `Check:` line (see below); the search for overlap with existing code was actually run.

## 2. `MODULE.md` per module folder (written after approval)

Keep it short. The header is what an agent reads first, so summary and keywords must be enough to decide whether to open the rest. `docs_tool.py modules` lists every `MODULE.md` in `index.md`, so write `summary` as one line (max about 120 characters) and `keywords` as a bracketed list.

```markdown
---
summary: One line: what this module is for and what it must not do.
keywords: [lexer, token, span]
depends_on: [src/other]
status: planned
---
# <module name>

## Purpose
2-3 lines.

## Boundaries
- Does: ...
- Does NOT do: ... (and where that lives instead)
- May depend on: ... Must not depend on: ...

## Interfaces
Signatures and data shapes, no bodies. Include a short example of the code as it should look when that clarifies the contract.

## Notes and diagram (optional)
A small text or Mermaid diagram of the flow, only if it removes a question.

## Checks
- `Check: <read-only command> -> <expected result>` (for example a search that must return 0 hits for a forbidden import)
```

Rules:
- Optional but useful: a one-line comment at the top of each key source file pointing to its `MODULE.md` ("Boundaries: see MODULE.md"), so an agent that opens only the file still sees the rules.
- A `MODULE.md` is a contract written ahead of the code. It is a hypothesis until the code confirms it (the audit rule still holds); set `status: planned` first and `done` only after the checks pass.
- Longer detail goes into the plan item or a linked file, never into the header. Do not copy the plan into the module files.
- Contracts contain no secrets and no implementation bodies. Signature stubs as real source files are a first implementation step, created only when the user asks.
- Boundary checks must follow the regression-check rules of `SKILL.md`: local, read-only commands only.
