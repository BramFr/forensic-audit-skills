---
id: bugs/03
title: Regressie op Search keywords in docs_tool.py SKELETON en docs-first-planner
category: bugs
status: done
summary: Herstel ## Search keywords in docs_tool.py SKELETON en docs-first-planner referenties na commit b8b68f5.
tags: [planner, docs, search-keywords, regressie, bugfix]
created: 2026-10-27
updated: 2026-10-27
related: [feature/04, bugs/01, bugs/02, feature/06]
---

# Regressie op Search keywords in docs_tool.py SKELETON en docs-first-planner

## Symptom, expected behaviour, how to reproduce
- **Symptom:** De automatische regressiecheck op `feature/04` geeft `False` op `Select-String skills/docs-first-planner/scripts/docs_tool.py -Pattern "## Search keywords" -Quiet` en `6` i.p.v. `9` op de 9 skill-/regelbestanden.
- **Expected behaviour:** `SKELETON` in `skills/docs-first-planner/scripts/docs_tool.py` bevat `## Search keywords`, en alle 9 skill-/regelbestanden bevatten `Search keywords`.
- **How to reproduce:** Voer `Select-String skills/docs-first-planner/scripts/docs_tool.py -Pattern "## Search keywords" -Quiet` uit vanuit de project-root.
- **Root cause:** regression or outdated criterion: unconfirmed (in commit `b8b68f5` is `SKELETON` in `docs_tool.py` overschreven zonder `## Search keywords`).

## Observed error
```text
=== Check 2: Search keywords in 9 skill/rule files ===
6
=== Check 5: docs_tool.py SKELETON ===
False
```

## Decisions (from the grill)
| Question | Decision | Reason |
| --- | --- | --- |

## Scope
- In: Herstellen van `## Search keywords` in `skills/docs-first-planner/scripts/docs_tool.py` (`SKELETON`) en de `docs-first-planner` bestanden.
- Out (explicitly not doing): Nader te bepalen bij planning.

## Approach
1. Wordt uitgewerkt bij het plannen van dit item (of gecombineerd met de nieuwe feature).

## Acceptance criteria
- [x] `scripts/docs_tool.py` bevat `## Search keywords` in `SKELETON`.
  Check: `Select-String skills/docs-first-planner/scripts/docs_tool.py -Pattern "## Search keywords" -Quiet` -> `True`

## Risks and open points
- Regressie ontdekt tijdens Fase 1 regressiecheck op 2026-10-27 en direct opgelost via `feature/06`.

## Relations
- Regressie van: `feature/04`, `bugs/01`.
- Opgelost in: `feature/06`.

## Verification
| Criterion | How checked | Result |
| --- | --- | --- |
| `scripts/docs_tool.py` bevat `## Search keywords` in `SKELETON` | `Select-String skills/docs-first-planner/scripts/docs_tool.py -Pattern "## Search keywords" -Quiet` | `True`, voldaan |
