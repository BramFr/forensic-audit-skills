---
id: feature/12
title: Skill first-principles-architect domeinneutraal toevoegen (intake, systeemanalyse, verificatielus, schone oplevering)
category: feature
status: in-progress
summary: Nieuwe skill first-principles-architect: 7-dimensie intake, 8-delige analyse, poorten A en B en schone oplevering, zonder iets te verwijderen.
tags: [skills, first-principles, architect, domeinneutraal, intake, oplevering, ergonomie]
created: 2026-10-31
updated: 2026-10-31
related: [feature/11, feature/03]
---

# Skill first-principles-architect domeinneutraal toevoegen

## Why
De planner (`docs-first-planner`, feature/11) heeft al een first-principles analyse, maar werkt altijd met `./docs` en levert bewust niets op. Voor een eenmalig verzoek om iets te bouwen, ontwerpen, tunen of oplossen was er geen skill die eerst de systeemeisen uitvraagt, de aannames verifieert en daarna een schoon resultaat oplevert. Ook ontbraken perceptuele en cognitieve ergonomie, een goedkeuringspoort voor kwaliteitsupgrades die de gebruiker niet kent, end-to-end pad-integriteit en opleveringszuiverheid. De gebruiker wil de bestaande skill `first-principles-architect` in deze repo opnemen, volledig domeinneutraal, zonder iets te verwijderen.

## Starting point (audit findings)
- Verified: de repo had 4 skills. `skills/docs-first-planner/references/first-principles.md` bevat al de 7 dimensies, een 7-delige systeemanalyse, de grill (3-10 vragen) en fase 3.5 (confidence gate, circuit breaker).
- Verified: de bron-skill heeft 8 analyse-onderdelen. Het achtste (perceptie, cognitie en zintuiglijke ergonomie) ontbreekt in de planner, net als Sluis B (upgrade-voorstellen met goedkeuring) en de regels voor opleveringszuiverheid.
- Corrected: de bron-skill gebruikt een zekerheidsdrempel van "80%". Dat is schijnprecisie (zelfde besluit als feature/11), dus vervangen door bewijslabels (🔎 SOURCED, ⚙️ EXECUTED, echte code of data).
- Corrected: de bron-skill noemt voorbeelden uit vakgebieden (voertuigen, dieren, schermen, recepturen enzovoort). Die zijn vervangen door abstracte formuleringen; het vakgebied wordt tijdens de run afgeleid.
- Unverified: de skill is nog niet met echte gebruikersprompts in meerdere domeinen doorgelopen (zie Risks).

## Decisions
| Question | Decision | Reason |
| --- | --- | --- |
| Aparte skill of samenvoegen in de planner? | Aparte skill `skills/first-principles-architect/SKILL.md` | De planner is gebonden aan `./docs` en levert bewust niet op; de architect werkt eenmalig en levert wel op |
| Taal van de skill | Engels (zoals de andere skills), antwoord in de taal van de gebruiker | Conventie van de repo; docs-items blijven Nederlands |
| 80%-drempel | Bewijslabels in plaats van een percentage | Schijnprecisie, besluit uit feature/11 |
| Domeinneutraliteit | Geen vakspecifieke voorbeelden in de body; vocabulaire, metrics en getallen worden per run afgeleid; de description noemt wel voorbeeldvelden voor triggering | Zero-hardcode principe van de repo |
| Eerlijkheid versus schone oplevering | Open punten en aannames in een kort begeleidend bericht, nooit in het opgeleverde werk | Combineert opleveringszuiverheid met compact, eerlijk rapporteren (CLAUDE.md, principe 5) |
| Zoekregels | Verwijzen naar `forensic-audit` Principle 4 in plaats van dupliceren | Eén bron van waarheid |
| Bestaande bestanden | Alleen invoegen; enige vervanging is "four" -> "five" in `GEMINI.md` | Opdracht: niets verwijderen, alleen updates |
| Gedrag van de planner | Alleen verwijzingen toegevoegd (description en body); verder ongewijzigd | Geen ongevraagde gedragswijziging, voorkomt dubbel triggeren |

## Scope
- In:
  - Nieuw: `skills/first-principles-architect/SKILL.md`.
  - Registratie en verwijzingen: `README.md` (tabel, uitleg, gebruik, layout), `CLAUDE.md` (verwijzing en principe 8), `.cursor/rules/forensic-audit.mdc` (principe 7), `GEMINI.md`, `.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json`, `gemini-extension.json`, `EXAMPLES.md` (sectie 7), `docs/index.md` (Search keywords).
  - `skills/docs-first-planner/SKILL.md`: twee verwijzingen naar de nieuwe skill.
- Out (explicitly not doing):
  - Het verwijderen of herschrijven van bestaande tekst, en gedragswijzigingen in `forensic-audit`, `forensic-security-audit`, `forensic-site-audit` of `docs_tool.py`.
  - Het overnemen van ergonomie, Sluis B en opleveringszuiverheid in `docs-first-planner` (mogelijk vervolgitem).
  - Een versienummer-bump in de plugin-bestanden en sync naar lokaal geïnstalleerde kopieën.

## Approach
1. Schrijf de skill domeinneutraal in het Engels -> verify: frontmatter geldig, naam gelijk aan mapnaam.
2. Registreer de skill en voeg verwijzingen toe, alleen door in te voegen -> verify: byte-diff toont 0 verwijderde bytes behalve "four" -> "five".
3. Maak dit item aan, regenereer de index en draai de check -> verify: `docs OK`.

## Acceptance criteria
- [x] De skill bevat de 7 dimensies, fase 1, 2, 2.5 (poort A en B) en 3 en is geldig.
  Check: `python -c "import re,pathlib; t=pathlib.Path('skills/first-principles-architect/SKILL.md').read_text(encoding='utf-8'); print(re.search(r'^name: first-principles-architect$',t,re.M) is not None and all(s in t for s in ['D7','## Phase 1','## Phase 2:','## Phase 2.5','Gate A','Gate B','## Phase 3']))"` -> `True`
- [x] De body van de skill bevat geen vakspecifieke termen.
  Check: `python -c "import re,pathlib; b=pathlib.Path('skills/first-principles-architect/SKILL.md').read_text(encoding='utf-8').split('---',2)[2]; print(len(re.findall(r'\\b(vehicle|dough|oven|database|skeleton|texture|renovat\\w*|kitchen|dog|horse)\\b',b,re.I)))"` -> `0`
- [x] De skill is overal geregistreerd.
  Check: `python -c "import pathlib; fs=['README.md','CLAUDE.md','GEMINI.md','EXAMPLES.md','.cursor/rules/forensic-audit.mdc','.claude-plugin/plugin.json','skills/docs-first-planner/SKILL.md']; print(sum('first-principles' in pathlib.Path(f).read_text(encoding='utf-8').lower() for f in fs))"` -> `7`
- [x] De JSON-bestanden zijn nog geldig.
  Check: `python -c "import json; [json.load(open(f,encoding='utf-8')) for f in ['.claude-plugin/plugin.json','.claude-plugin/marketplace.json','gemini-extension.json']]; print('ok')"` -> `ok`
- [ ] Docs zijn consistent (te draaien in de volledige repo, inclusief `mcp/`).
  Check: `python skills/docs-first-planner/scripts/docs_tool.py check` -> `docs OK`

## Risks
- De skill is niet met echte prompts in meerdere domeinen doorgelopen; de triggering ten opzichte van `docs-first-planner` (beide noemen bouwen en tunen) is alleen via verwijzingen in de descriptions afgebakend en moet in gebruik blijken.
- De planner mist nog ergonomie, Sluis B en opleveringszuiverheid; de twee skills kunnen daardoor tijdelijk verschillend gedrag vertonen op dezelfde dimensies.

## Verification
| Criterion | How checked | Result |
| --- | --- | --- |
| Inhoud en geldigheid skill | `Check:` uitgevoerd (2026-10-31) plus `quick_validate` van skill-creator | `True`, `Skill is valid!`, voldaan |
| Domeinneutraal | `Check:` uitgevoerd (2026-10-31) | `0`, voldaan |
| Registratie | `Check:` uitgevoerd (2026-10-31) | `7`, voldaan |
| JSON geldig | `Check:` uitgevoerd (2026-10-31) | `ok`, voldaan |
| Niets verwijderd | Byte-diff origineel tegen nieuw (2026-10-31) | 0 verwijderde bestanden, 0 verwijderde bytes, behalve 3 bytes ("four" -> "five") in `GEMINI.md` |
| Docs-consistentie | `Check:` uitgevoerd (2026-10-31) in de uitgepakte zip, die geen `mcp/`-map bevat | Index in sync. Enige melding: module-tabel niet in sync omdat `mcp/context-compressor/MODULE.md` in de zip ontbreekt; die melding bestond al vóór deze wijziging. Open tot de check in de volledige repo `docs OK` geeft |
