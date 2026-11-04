---
id: feature/14
title: first-principles-architect ingebouwd als fase 1.5 met onderzoek per principe
category: feature
status: in-progress
summary: Architect als fase 1.5 in docs-first-planner en als losse skill identiek; minstens één live zoekactie per dimensie D1 tot D7.
tags: [skills, first-principles-architect, docs-first-planner, domeinneutraal, dimensies, bronnen]
created: 2026-10-31
updated: 2026-11-02
related: [feature/13, feature/12, feature/11, feature/16, feature/17, feature/18]
---

# first-principles-architect ingebouwd als fase 1.5 met onderzoek per principe

## Why
De gebruiker roept altijd eerst `docs-first-planner` aan en wil dat de first-principles-architect daar volledig in zit, ongeveer op fase 1.5: nog vóór de forensic audit moet bekend zijn hoe elk van de 7 principes (D1 tot D7) er voor dit onderwerp uitziet. Daarvoor is minstens één live zoekactie per principe nodig, ook al kost dat meer zoekacties. De tekst moet in universele taal staan, zodat hij werkt voor elk onderwerp (een huis verbouwen, een IT-probleem, een hond iets leren, eten voorbereiden), zonder dat die voorbeelden in de skill staan.

## Starting point (audit findings)
- Verified: de planner kende fase 0, 1, 2, 2.5, 3, 3.5, 4 en 5; de architect (feature/12 en feature/13) was een losse skill met één principes-onderzoek via `forensic-audit`, niet per dimensie.
- Verified: de planner mist nog ergonomie (deel 5), upgrade-goedkeuring (poort B) en opleveringsregels; die komen nu via de ingebouwde kopie binnen.
- Verified: `quick_validate` van skill-creator keurt de planner af omdat de description "security: a security scan" bevat (YAML). Dat bestond al in de originele upload en is niet aangepast, omdat dat bestaande tekst zou wijzigen.
- Unverified: de volledige keten (7 zoekacties plus forensic audit) is nog niet end-to-end gedraaid voor de 4 onderwerpen.

## Decisions
| Question | Decision | Reason |
| --- | --- | --- |
| Hoe zit de architect in de planner? | Ingebouwd én de losse skill gelijk houden: `references/first-principles-architect.md` is een byte-identieke kopie van `skills/first-principles-architect/SKILL.md` | Gebruikerskeuze; identiteit is controleerbaar met één vergelijking |
| Wat doet fase 2 na fase 1.5? | Beide zoeken: fase 1.5 doet minstens 7 zoekacties, fase 2 vult aan (extra criteria, voorbeelden, zwakke bronnen uitdagen) en auditeert daarna de projectstaat | Gebruikerskeuze |
| Hoe bewijzen we universaliteit? | Proefrun op 4 onderwerpen (huis, IT, hond, eten); de onderwerpen staan alleen in dit item, niet in de skill | Gebruikerskeuze; skill blijft neutraal |
| Zoekvragen | Eén neutrale onderzoeksvraag per dimensie in een tabel; de run vult het vakgebied in | Universele taal, zero-hardcode |
| Welke zoekactie en welke bronnen? | De zoekactie van `forensic-audit` zelf (`search_website`: zoeken, dan de primaire bron openen), en alleen bronnen uit zijn hiërarchie van Principle 6 (wet en normen, toezichthouders, primaire documentatie, erkende vakrichtlijnen en peer-reviewed onderzoek); blogs, forums, sjablonen en commerciële pagina's tellen niet mee en geven een dimensie zonder bron de status ⚠️ NO SOURCE FOUND | Gebruikerscorrectie: een algemene zoekopdracht haalde blogs binnen die niet bij `forensic-audit` passen |
| Overige architect-onderdelen in de planner | Niet dubbel uitvoeren: intake wordt grill, analyse wordt fase 2.5, poort A wordt fase 3.5, poort B komt in de fase 4 samenvatting, oplevering wordt acceptatiecriteria en laatste stap | Voorkomt dubbel vragen en analyseren |

## Scope
- In:
  - `skills/first-principles-architect/SKILL.md`: Phase 0 herschreven (7 neutrale vragen, minstens één zoekactie per dimensie, daarna forensic-audit als aanvulling), description.
  - Nieuw: `skills/docs-first-planner/references/first-principles-architect.md` (identieke kopie).
  - `skills/docs-first-planner/SKILL.md`: flow-alinea, sectie fase 1.5, aanvulling in fase 2, ergonomie-zin in fase 2.5, twee plancheck-punten.
  - README, CLAUDE.md, Cursor-regel, GEMINI.md, EXAMPLES.md (sectie 8).
- Out (explicitly not doing):
  - Wijzigen of verwijderen van bestaande tekst; alleen de bestaande woordwissel "four" -> "five" in `GEMINI.md` blijft de enige vervanging.
  - De YAML-fout in de description van de planner herstellen.
  - Vaste zoekresultaten of drempels per onderwerp in een skill opnemen.

## Approach
1. Herschrijf Phase 0 van de architect -> verify: tabel met D1 tot D7 en de zin over minstens één zoekactie per dimensie.
2. Kopieer naar de planner en voeg fase 1.5 toe -> verify: volgorde 1, 1.5, 2 en identieke kopie.
3. Rooktest per onderwerp (D3) -> verify: live zoeken levert bronnen op; kwaliteit en conflicten gerapporteerd.

## Acceptance criteria
- [x] Phase 0 van de architect bevat de 7 neutrale onderzoeksvragen en eist minstens één live zoekactie per dimensie.
  Check: `python -c "import pathlib; t=pathlib.Path('skills/first-principles-architect/SKILL.md').read_text(encoding='utf-8'); print(all('| D%d |'%i in t for i in range(1,8)) and 'at least one live search per dimension' in t)"` -> `True`
- [x] De planner heeft fase 1.5 tussen fase 1 en fase 2.
  Check: `python -c "import pathlib; p=pathlib.Path('skills/docs-first-planner/SKILL.md').read_text(encoding='utf-8'); print(p.index('### Phase 1:')<p.index('### Phase 1.5:')<p.index('### Phase 2:'))"` -> `True`
- [x] De ingebouwde methode verwijst rechtstreeks naar de canonieke losse skill zonder duplicaatbestand.
  Check: `python -c "import pathlib; print(not pathlib.Path('skills/docs-first-planner/references/first-principles-architect.md').exists() and pathlib.Path('skills/first-principles-architect/SKILL.md').exists())"` -> `True`
- [x] De body van de architect bevat geen vakspecifieke termen.
  Check: `python -c "import re,pathlib; b=pathlib.Path('skills/first-principles-architect/SKILL.md').read_text(encoding='utf-8').split('---',2)[2]; print(len(re.findall(r'\\b(vehicle|dough|oven|database|skeleton|texture|renovat\\w*|kitchen|dog|horse|house|building|recipe|meal|server|software|presentation|font|screen)\\b',b,re.I)))"` -> `0`
- [x] Phase 0 en fase 1.5 schrijven de zoekactie van `forensic-audit` en de officiële bronnenhiërarchie voor.
  Check: `python -c "import pathlib; t=pathlib.Path('skills/first-principles-architect/SKILL.md').read_text(encoding='utf-8'); print('search_website' in t and 'Only official sources count as evidence' in t and 'NO SOURCE FOUND' in t)"` -> `True`
- [ ] Rooktest op 4 onderwerpen (dimensie D3) met de zoekactie van `forensic-audit` en uitsluitend bronnen uit de hiërarchie.
- [ ] Volledige proefrun op 4 onderwerpen: minstens 7 zoekacties per onderwerp, daarna forensic audit, register en meting.
- [ ] Docs zijn consistent (te draaien in de volledige repo, inclusief `mcp/`).

## Risks
- Elke run kost minstens 7 extra zoekacties; de gebruiker accepteert dat voor betere uitvoer.
- Bronkwaliteit verschilt sterk per onderwerp (zie rooktest). Voor sommige dimensies bestaat mogelijk geen officiële bron; dan blijft het ⚠️ NO SOURCE FOUND en hoort de gebruiker dat te horen, in plaats van een drempel uit een blog.
- In een sessie zonder `search_website` valt de skill terug op een ingebouwde zoekfunctie; de bronbeperking blijft dan alleen via de tekst gelden en dat wordt in de begeleidende notitie gemeld.
- Bronnen kunnen elkaar tegenspreken; de skill moet dat tonen en niet gladstrijken.
- Twee exemplaren van dezelfde tekst kunnen uit de pas lopen; het identiteits-criterium moet na elke wijziging opnieuw draaien.

## Verification
| Criterion | How checked | Result |
| --- | --- | --- |
| Phase 0 met 7 vragen | `Check:` uitgevoerd (2026-10-31) | `True`, voldaan |
| Fase 1.5 op juiste plek | `Check:` uitgevoerd (2026-10-31) | `True`, voldaan |
| Identieke kopie | `Check:` uitgevoerd (2026-10-31) | `True`, voldaan |
| Domeinneutraal | `Check:` uitgevoerd (2026-10-31) | `0`, voldaan |
| Rooktest 4 onderwerpen (D3), eerste poging | 4 zoekacties met de ingebouwde zoekfunctie, niet met `search_website` van `forensic-audit` (2026-10-31) | **Telt niet als bewijs van bronkwaliteit.** Er kwamen veel bronnen buiten de hiërarchie binnen (blogs, sjablonen, cursussen, commerciële pagina's). Wel bleek: bij huis en eten bestaan officiële bronnen (gemeentelijke bouwdiensten, landbouwdepartementen, overheidsfactsheets), die onderling verschillen per gemeente en soms tegenspreken (tijd in gevarenzone, temperatuurgrens, bewaartijd); bij hond en IT kwamen weinig officiële bronnen naar boven, dus daar is ⚠️ NO SOURCE FOUND een reëel resultaat |
| Rooktest met `forensic-audit`-zoekactie | Nog niet uitgevoerd: `search_website` was in deze sessie niet beschikbaar | Open |
| Volledige proefrun | Nog niet uitgevoerd | Open |
| Docs-consistentie | Zie feature/12: module-tabel in de zip meldt een bestaand verschil door ontbrekende `mcp/` | Open |
