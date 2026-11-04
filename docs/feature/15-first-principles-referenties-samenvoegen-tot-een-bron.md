---
id: feature/15
title: first-principles referenties samenvoegen tot één bron (architect-kopie)
category: feature
status: in-progress
summary: first-principles.md houdt alleen planner-specifieke regels; dimensies en analyse staan nog alleen in de architect-kopie.
tags: [skills, docs-first-planner, first-principles, architect, dubbele-tekst, bron-van-waarheid]
created: 2026-10-31
updated: 2026-11-02
related: [feature/14, feature/11, feature/18]
---

# first-principles referenties samenvoegen tot één bron

## Why
Na feature/14 stonden de 7 dimensies, de systeemanalyse, de verificatielus, de circuit breaker en de placebo-regel in twee bestanden: `references/first-principles.md` (1326 woorden) en de ingebouwde kopie `references/first-principles-architect.md` (3139 woorden). Twee uitwerkingen van dezelfde stof kunnen uit de pas lopen en de planner zou dan twee verschillende versies volgen. De gebruiker koos optie 2: `first-principles.md` terugbrengen tot de planner-specifieke delen en voor de rest naar de architect-kopie verwijzen.

## Starting point (audit findings)
- Verified: 13 van 14 gecontroleerde begrippen kwamen in beide bestanden voor (overlap gemeten op 2026-10-31).
- Verified: `SKILL.md` verwijst naar `first-principles.md` voor fase 2.5, de grill-regels, fase 3.5 en de plancheck; die secties moeten blijven.
- Verified: de architect telt 8 analyse-delen (met deel 5, perceptie en ergonomie), `first-principles.md` telde er 7. Daardoor verschuiven nummers: "deel 7" (misvatting) wordt "deel 8"; "deel 4" (oorzakelijke keten) blijft.

## Decisions
| Question | Decision | Reason |
| --- | --- | --- |
| Welke optie? | Optie 2: `first-principles.md` houdt alleen planner-specifieke regels en verwijst naar de architect-kopie | Gebruikerskeuze; één bron voor dimensies en analyse |
| Regel "niets verwijderen"? | Voor dit item expliciet opgeheven door de gebruiker, beperkt tot de dubbele tekst in `first-principles.md` en de twee zinnen in `SKILL.md` die het aantal analyse-delen noemen | Verwijderen van dubbele tekst is het doel van dit item |
| Bij verschil tussen de twee bestanden | De architect-kopie wint | Eén bron van waarheid |
| Nummering | De 8 delen van de architect gelden; verwijzingen in `first-principles.md` zijn bijgewerkt | Voorkomt verwijzing naar een deel dat niet meer bestaat |
| Domeinvoorbeelden uit de oude tekst | Vervallen mee (lijst van vakgebieden en de D4-voorbeelden) | Universele taal |

## Scope
- In:
  - `skills/docs-first-planner/references/first-principles.md`: introductie vervangen door verwijzing; sectie "The 7 universal dimensions" en sectie "System analysis (7 fixed parts)" verwijderd; "7" -> "8" en "deel 7" -> "deel 8" in de blijvende secties; één zin over officiële bronnen in fase 3.5.
  - `skills/docs-first-planner/SKILL.md`: de zin "draft the 7-part system analysis (...)" in fase 2.5 verwijst nu naar de 8 delen van de architect-kopie, en "keep the 7-part system analysis internal" in fase 3 is "8-part" geworden.
- Out (explicitly not doing):
  - De grill-regels, fase 3.5 (herstel, circuit breaker, hard reset) en de plancheck inhoudelijk wijzigen.
  - De architect-kopie of de losse skill wijzigen.

## Approach
1. Verwijder de dubbele secties en vervang de introductie -> verify: tabel en 7-delige lijst staan niet meer in `first-principles.md`.
2. Werk de verwijzingen bij (nummering, pointer) -> verify: geen "7-part" meer in de planner-bestanden.
3. Controleer dat de secties waarnaar `SKILL.md` verwijst nog bestaan -> verify: koppen aanwezig.

## Acceptance criteria
- [x] `first-principles.md` bevat de dimensietabel en de 7-delige lijst niet meer en verwijst naar `skills/first-principles-architect/SKILL.md`.
  Check: `python -c "import pathlib; t=pathlib.Path('skills/docs-first-planner/references/first-principles.md').read_text(encoding='utf-8'); print('| D1 |' not in t and 'System analysis (7 fixed parts)' not in t and 'first-principles-architect/SKILL.md' in t)"` -> `True`
- [x] De secties waarnaar `SKILL.md` verwijst bestaan nog.
  Check: `python -c "import pathlib; t=pathlib.Path('skills/docs-first-planner/references/first-principles.md').read_text(encoding='utf-8'); print(all(h in t for h in ['## Phase 2.5:','## Grill rules','## Phase 3.5:','## Plan check additions']))"` -> `True`
- [x] Geen verwijzing meer naar een 7-delige analyse in de planner.
  Check: `python -c "import pathlib; print(sum(pathlib.Path(f).read_text(encoding='utf-8').count('7-part') for f in ['skills/docs-first-planner/SKILL.md','skills/docs-first-planner/references/first-principles.md']))"` -> `0`
- [x] De canonieke architect-skill is de enige bron en het duplicaatbestand is verwijderd.
  Check: `python -c "import pathlib; print(not pathlib.Path('skills/docs-first-planner/references/first-principles-architect.md').exists() and pathlib.Path('skills/first-principles-architect/SKILL.md').exists())"` -> `True`
- [ ] Docs zijn consistent (te draaien in de volledige repo, inclusief `mcp/`).

## Risks
- Een planner-sessie die alleen `first-principles.md` leest, mist de dimensietabel. Mitigatie: de introductie noemt de dimensies bij naam en `SKILL.md` fase 1.5 laat de architect-kopie lezen.
- De oude tekst (introductie met vakgebieden, tabel, 7-delige lijst) staat alleen nog in de originele upload van `forensic-audit-skills.zip`; bewaar die als terugvalpunt.

## Verification
| Criterion | How checked | Result |
| --- | --- | --- |
| Dubbele secties weg | `Check:` uitgevoerd (2026-10-31) | `True`, voldaan |
| Secties voor `SKILL.md` aanwezig | `Check:` uitgevoerd (2026-10-31) | `True`, voldaan |
| Geen 7-delige verwijzing | `Check:` uitgevoerd (2026-10-31) | `0`, voldaan |
| Identieke kopie | `Check:` uitgevoerd (2026-10-31) | `True`, voldaan |
| Docs-consistentie | Zie feature/12: module-tabel in de zip meldt een bestaand verschil door ontbrekende `mcp/` | Open |
