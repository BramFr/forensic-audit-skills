---
id: bugs/02
title: Regressie op Search keywords in docs-first-planner bestanden
category: bugs
status: done
summary: Herstel Search keywords instructie in docs-first-planner SKILL.md, audit-brief.md en plan-template.md na commit b8b68f5.
tags: [planner, forensic-audit, search-keywords, regressie, bugfix]
created: 2026-10-27
updated: 2026-10-27
related: [bugs/01, feature/04, bugs/03, feature/06]
---

# Regressie op Search keywords in docs-first-planner bestanden

## Symptom, expected behaviour, how to reproduce
- **Symptom:** De automatische regressiecheck op `bugs/01` geeft `6` treffers voor `Search keywords` in plaats van de verwachte `9` treffers.
- **Expected behaviour:** Alle 9 bestanden (`skills/*/SKILL.md`, `skills/docs-first-planner/references/audit-brief.md`, `skills/docs-first-planner/references/plan-template.md`, `GEMINI.md`, `CLAUDE.md` en `.cursor/rules/forensic-audit.mdc`) bevatten de `## Search keywords`-instructie.
- **How to reproduce:** Voer `(Select-String skills/*/SKILL.md,skills/docs-first-planner/references/audit-brief.md,skills/docs-first-planner/references/plan-template.md,GEMINI.md,CLAUDE.md,.cursor/rules/forensic-audit.mdc -Pattern "Search keywords" -List | Measure-Object).Count` uit vanuit de project-root.
- **Root cause:** regression or outdated criterion: unconfirmed (in commit `b8b68f5` zijn `skills/docs-first-planner/SKILL.md`, `references/audit-brief.md` en `references/plan-template.md` overschreven zonder de `Search keywords`-regels).

## Observed error
```text
=== Check 2: Search keywords in 9 skill/rule files ===
6
```

## Decisions (from the grill)
| Question | Decision | Reason |
| --- | --- | --- |

## Scope
- In: Herstellen van `## Search keywords` in `skills/docs-first-planner/SKILL.md`, `references/audit-brief.md` en `references/plan-template.md` (of meenemen in de geplande feature).
- Out (explicitly not doing): Nader te bepalen bij planning.

## Approach
1. Wordt uitgewerkt bij het plannen van dit item (of gecombineerd met de nieuwe feature).

## Acceptance criteria
- [x] Alle 9 bestanden bevatten opnieuw `Search keywords`.
  Check: `(Select-String skills/*/SKILL.md,skills/docs-first-planner/references/audit-brief.md,skills/docs-first-planner/references/plan-template.md,GEMINI.md,CLAUDE.md,.cursor/rules/forensic-audit.mdc -Pattern "Search keywords" -List | Measure-Object).Count` -> `9`

## Risks and open points
- Regressie ontdekt tijdens Fase 1 regressiecheck op 2026-10-27 en direct opgelost via `feature/06`.

## Relations
- Regressie van: `bugs/01`, `feature/04`.
- Opgelost in: `feature/06`.

## Verification
| Criterion | How checked | Result |
| --- | --- | --- |
| Alle 9 bestanden bevatten `Search keywords` | `(Select-String skills/*/SKILL.md,skills/docs-first-planner/references/audit-brief.md,skills/docs-first-planner/references/plan-template.md,GEMINI.md,CLAUDE.md,.cursor/rules/forensic-audit.mdc -Pattern "Search keywords" -List \| Measure-Object).Count` | `9`, voldaan |
