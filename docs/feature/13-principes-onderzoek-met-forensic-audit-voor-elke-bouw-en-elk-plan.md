---
id: feature/13
title: Verplicht principes-onderzoek met forensic-audit vóór elke bouw en elk plan
category: feature
status: in-progress
summary: first-principles-architect en docs-first-planner onderzoeken altijd eerst via forensic-audit welke criteria het resultaat moet halen.
tags: [skills, forensic-audit, first-principles-architect, docs-first-planner, domeinneutraal, bronnen, criteria]
created: 2026-10-31
updated: 2026-10-31
related: [feature/12, feature/11, feature/03]
---

# Verplicht principes-onderzoek met forensic-audit vóór elke bouw en elk plan

## Why
Een gevraagde presentatie (HTML-slideshow) werd technisch compleet opgeleverd, maar was slecht: te kleine letters en te veel informatie per slide. Niemand had eerst onderzocht waaraan zo'n resultaat moet voldoen. De gebruiker wil dat de skills bij elk verzoek, ongeacht hoe simpel, eerst met `forensic-audit` en live bronnen de principes en kwaliteitscriteria van het gevraagde resultaat ophalen, domeinneutraal, en dat elke zekerheidsuitspraak alleen op een bron rust.

## Starting point (audit findings)
- Verified: `docs-first-planner` fase 2 auditte alleen de huidige projectstaat en de aannames in de wens, niet de criteria waaraan het resultaat moet voldoen; `forensic-audit` ging uit van een bestaand resultaat.
- Verified: `first-principles-architect` (feature/12) had geen onderzoeksstap voorafgaand aan de intake en geen controle van het resultaat tegen bronnen.
- Corrected: eerdere uitspraak dat de skills "domeinneutraal" waren, rustte op een scan van termen. Dat bewijst niet dat de criteria per vakgebied juist en actueel worden opgehaald; dat moet per run via live bronnen.
- Unverified: gedrag in echte runs (zie Risks).

## Decisions
| Question | Decision | Reason |
| --- | --- | --- |
| Wanneer onderzoeken? | Altijd, bij elk verzoek, ook korte of vertrouwde | Gebruiker zonder expertise kan criteria niet benoemen; eigen kennis is een hypothese |
| Hoe? | Met `forensic-audit` in een nieuwe pre-build modus: onderwerp is het verzoek, de 10 punten zijn criteria en faalpunten | Hergebruikt bronnenhiërarchie en bewijslabels; geen tweede mechanisme |
| Uitkomst | Intern criteria-register: criterium, meetbare drempel of test, bron plus label | Voedt intake, acceptatiecriteria en controle voor oplevering |
| Voorbeelden | Een paar gezaghebbende voorbeelden van goed en fout, alleen als referentie voor de bouwer | Maakt criteria concreet; nooit in het resultaat kopiëren |
| Zekerheid | Alleen op basis van bronstatus; geen bron betekent "onverifieerd" | Gebruikersbesluit: confidence alleen uit een bron |
| Controle voor oplevering | Resultaat meten tegen het register; een misser gaat terug voor herstel | Gesloten lus; voorkomt onleesbaar of overladen resultaat |
| Planner op alle routes | Ook op de security-route | "Altijd, ongeacht de vraag" |

## Scope
- In:
  - `skills/first-principles-architect/SKILL.md`: Fase 0, bronregel voor zekerheid, controle voor oplevering, extra gotcha.
  - `skills/docs-first-planner/SKILL.md`: alinea "Principles of the wish" in fase 2, extra plancheck, description.
  - `skills/forensic-audit/SKILL.md`: sectie "Pre-build use (principles research)".
  - README, CLAUDE.md, Cursor-regel, GEMINI.md en EXAMPLES.md (sectie 8).
- Out (explicitly not doing):
  - Vaste lijsten met criteria of drempels per vakgebied in een skill (zou niet actueel zijn en breekt zero-hardcode).
  - Het wijzigen van bestaande tekst van `forensic-audit`; alleen een nieuwe sectie.

## Approach
1. Voeg de pre-build modus toe aan `forensic-audit` en de verplichte stap aan beide skills -> verify: de zinnen staan erin, geen tekst verwijderd.
2. Werk de documentatie bij en regenereer de index -> verify: index bevat feature/13.
3. Draai een proefrun met een echt verzoek (bijvoorbeeld de presentatie) -> verify: register met bronnen vóór de bouw en meting vóór oplevering.

## Acceptance criteria
- [x] De drie skills bevatten de nieuwe stap.
  Check: `python -c "import pathlib; r=lambda f: pathlib.Path(f).read_text(encoding='utf-8'); print(all(x in r(f) for f,x in [('skills/first-principles-architect/SKILL.md','## Phase 0'),('skills/docs-first-planner/SKILL.md','Principles of the wish'),('skills/forensic-audit/SKILL.md','Pre-build use (principles research)')]))"` -> `True`
- [x] Zekerheid rust alleen op een bron.
  Check: `python -c "import pathlib; t=pathlib.Path('skills/first-principles-architect/SKILL.md').read_text(encoding='utf-8'); print('no source, no confidence' in t)"` -> `True`
- [ ] Proefrun met een echt verzoek (bijvoorbeeld een presentatie) laat register met bronnen vóór de bouw en meting vóór oplevering zien.
- [ ] Docs zijn consistent (te draaien in de volledige repo, inclusief `mcp/`).

## Risks
- Elke run kost extra zoekacties en tijd; begrensd door de bestaande compacte rapportage van `forensic-audit`.
- Of het register in de praktijk tot betere resultaten leidt, is nog niet aangetoond; daarom is de proefrun een open criterium.
- `docs-first-planner` en `first-principles-architect` kunnen nog steeds samen triggeren bij dezelfde vraag; het register wordt dan één keer opgehaald omdat de planner de architect niet aanroept.

## Verification
| Criterion | How checked | Result |
| --- | --- | --- |
| Nieuwe stap in drie skills | `Check:` uitgevoerd (2026-10-31) | `True`, voldaan |
| Zekerheid alleen via bron | `Check:` uitgevoerd (2026-10-31) | `True`, voldaan |
| Proefrun | Nog niet uitgevoerd | Open |
| Docs-consistentie | Zie feature/12: module-tabel meldt in de zip een bestaand verschil door ontbrekende `mcp/` | Open |
