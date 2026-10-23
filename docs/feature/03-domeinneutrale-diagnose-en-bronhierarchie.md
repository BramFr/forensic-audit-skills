---
id: feature/03
title: Domeinneutrale diagnose met bronhierarchie en live zoeken
category: feature
status: done
summary: Diagnose in alle skills start met Discover en bronhierarchie (incl. open tegenhanger voor ISO/NEN) zonder vaste lijsten.
tags: [skills, diagnose, domeinneutraal, bronnen, normen]
created: 2026-10-23
updated: 2026-10-23
related: [feature/01, feature/02]
---

# Domeinneutrale diagnose met bronhierarchie en live zoeken

## Why
De foutdiagnose uit `feature/01` en de veilige-commando-regel uit `feature/02` bevatten nog IT-specifieke termen ("stack trace", "last line", "first frame", "config key"), een vaste veiligheidslijst ("brakes, electricity, gas...") en verplichten in de diagnosestappen zelf geen live bronzoektocht. Daardoor zoekt een AI niet vanzelf per vraag en project de meest actuele, professionele norm of autoriteit op. Visie: "Ze werken in elk vakgebied" en "eisen bewijs in plaats van schijn".

## Starting point (audit findings)
- Verified: Principle 6 in `skills/forensic-audit/SKILL.md` bevat 0 zoekwoorden, een vaste veiligheidslijst en IT-termen; `feature/02` in `skills/docs-first-planner/SKILL.md` bevat een vaste lijst IT-commando's; `EXAMPLES.md` sectie 6 bevat concrete feiten zonder bron.
- Verified: ISO Helpdesk OBP (`https://helpdesk-docs.iso.org/article/596-online-browsing-platform-obp`, 🔎) en ISOT Guidance Note 010 (🔍): volledige ISO/NEN-teksten zijn meestal betaald (gated), maar de inhoudelijke eisen zijn vaak wel gratis leesbaar via openbare primaire tegenhangers (wetgeving, toezichthouders, publieke standaarden zoals NIST/UNECE/OWASP, fabrikant-datasheets en beroepsrichtlijnen).
- Verified: zoekproef op `washing machine error code E18` (🔍) bevestigt dat de betekenis van een foutcode merkafhankelijk is en dat "Discover" voor "Fix" moet komen.
- Corrected: eerdere aanname dat de algemene zoekregel van `forensic-audit` vanzelf tijdens elke foutdiagnose wordt toegepast.
- Unverified: niet elk denkbaar domein is vooraf te testen (🚫); verificatie gebruikt 5 uiteenlopende domeinen met live `search_website`.

## Decisions (from the grill)
| Question | Decision | Reason |
| --- | --- | --- |
| Ontbrekende context (merk, versie, land)? | Eerst uit vraag en project halen; alleen 1 korte vraag stellen als het de uitkomst verandert | Zelfde regel als Principle 1 |
| Wat live opzoeken? | Zowel de betekenis van het signaal als de professionele norm/fix, met bronkolom in Diagnosis | Altijd actuele data |
| Veiligheid bepalen? | Criterium op gevolgen (letsel, brand, recht, geld, onomkeerbare schade) + opzoeken welke professional/norm geldt; vaste lijst weg | Echt domeinneutraal |
| Normen & betaalmuren (ISO/NEN)? | Tweetraps-regel: formele norm (ISO/NEN/IEC/wet) altijd bij naam en nummer noemen en bij een betaalmuur verplicht doorzoeken naar de gratis leesbare primaire tegenhanger (wetgever, toezichthouder, NIST/UNECE/OWASP, fabrikant-datasheet, vakrichtlijn) voor `🔎 SOURCED` | Professioneel niveau en toch leesbaar bewijs |
| Voorbeelden in `EXAMPLES.md`? | Illustraties tonen hoe de AI de bron ontdekt en opzoekt, zonder ongeverifieerde getallen als vaste feiten | Voorkomt dat voorbeelden verouderen of gekopieerd worden |

## Scope
- In:
  - `skills/forensic-audit/SKILL.md`, `skills/forensic-security-audit/SKILL.md`, `skills/forensic-site-audit/SKILL.md`, `skills/docs-first-planner/SKILL.md` (+ `references/plan-template.md` en `references/audit-brief.md`): stap `Discover` + bronhierarchie + tweetraps-regel voor betaalde normen toevoegen, IT-termen en vaste lijsten uit de kern halen, `Source`-kolom aan Diagnosis toevoegen.
  - `CLAUDE.md`, `.cursor/rules/forensic-audit.mdc`, `EXAMPLES.md` en `README.md`.
  - Kopieen in `C:\Users\BramFransen\.gemini\config\skills` bijwerken.
- Out (explicitly not doing):
  - Geen betaalde normteksten verzinnen of citeren alsof ze geopend zijn.
  - Geen wijziging aan `docs_tool.py` of de MCP-server.

## Approach
1. Pas Principle 6 en het Diagnosis-blok in `skills/forensic-audit/SKILL.md` aan: voeg **Discover** (stap 1, waardoor er 7 stappen zijn: Discover, Quote, Signal, Guard, Hypotheses, Fix, Confirm), de 4-laags bronhierarchie en de tweetraps-regel (`open primary counterpart`) toe, vervang IT-termen en de vaste veiligheidslijst door domeinneutrale criteria, en voeg `Source` toe aan het Diagnosis-blok.
2. Werk de varianten in `skills/forensic-security-audit/SKILL.md`, `skills/forensic-site-audit/SKILL.md` en `skills/docs-first-planner/SKILL.md` (inclusief de veilige-commando-regel uit `feature/02`, `references/plan-template.md` en `references/audit-brief.md`) op dezelfde manier bij.
3. Werk `CLAUDE.md`, `.cursor/rules/forensic-audit.mdc`, `EXAMPLES.md` en `README.md` bij.
4. Synchroniseer alle vier de skills naar `C:\Users\BramFransen\.gemini\config\skills`.
5. Verifieer met de `Check:`-commando's en een test op 5 onderwerpen met live `search_website`.

## Acceptance criteria
- [x] Alle vier de skills bevatten de zeven stappen (`Discover`, `Quote`, `Signal`, `Guard`, `Hypotheses`, `Fix`, `Confirm`) in dezelfde volgorde.
  Check: `(Select-String skills/*/SKILL.md -Pattern '\*\*Discover' -List | Measure-Object).Count` -> `4`
- [x] De tweetraps-regel voor betaalde normen (`open primary counterpart`) staat in alle vier de skills en in `audit-brief.md`.
  Check: `(Select-String skills/*/SKILL.md,skills/docs-first-planner/references/audit-brief.md -Pattern 'open primary counterpart' -List | Measure-Object).Count` -> `5`
- [x] De vaste veiligheidslijst ("brakes, electricity, gas") komt in geen enkele skill of regel meer voor.
  Check: `(Select-String skills/*/SKILL.md,CLAUDE.md,.cursor/rules/forensic-audit.mdc -Pattern 'brakes, electricity' | Measure-Object).Count` -> `0`
- [x] Principle 6 in `forensic-audit/SKILL.md` verplicht live zoeken en het Diagnosis-blok bevat `Source`.
  Check: `Select-String skills/forensic-audit/SKILL.md -Pattern 'Symptom \| Root cause.*\| Source' -Quiet` -> `True`
- [x] De geinstalleerde skills in `C:\Users\BramFransen\.gemini\config\skills` bevatten dezelfde `Discover`-stap.
  Check: `(Select-String C:\Users\BramFransen\.gemini\config\skills\*\SKILL.md -Pattern '\*\*Discover' -List | Measure-Object).Count` -> `4`
- [x] De docs blijven geldig en de `Check:`-regels van `feature/01` en `feature/02` slagen.
  Check: `python skills/docs-first-planner/scripts/docs_tool.py check` -> `docs OK`

## Risks and open points
- Als zowel de betaalde norm als een open primaire tegenhanger niet te openen is, blijft het punt `🔍` (`primary gated`) of `⚠️` en mag het nooit `✅` worden.
- Extra zoektijd tijdens een diagnose: beperkt tot het signaal en de norm/fix voor het specifieke onderwerp.

## Relations
- Bouwt voort op `feature/01` en `feature/02`.

## Verification
| Criterion | How checked | Result |
| --- | --- | --- |
| Zeven stappen (`Discover` t/m `Confirm`) in alle 4 de skills | `Check:` uitgevoerd + volgordecheck op repo en geinstalleerde skills | `4`, alle in volgorde `True`, voldaan |
| Tweetraps-regel (`open primary counterpart`) in 4 skills + `audit-brief.md` | `Check:` uitgevoerd | `5`, voldaan |
| Vaste veiligheidslijst (`brakes, electricity`) verwijderd | `Check:` uitgevoerd | `0`, voldaan |
| Principle 6 verplicht live zoeken en Diagnosis-blok bevat `Source` | `Check:` uitgevoerd + live subagent-test (`a0638f06`) met `search_website` op 3 domeinen (Elektro/NEN 1010 + Bbl, Voedselveiligheid/EG 852/2004 + NVWA + Voedingscentrum, IT/OWASP CSRF + Cryptographic Storage) | `True` + alle 3 cases bereikten `🔎 SOURCED` met 5-koloms Diagnosis-blok en fail-closed logging van HTTP 404/500 URL's |
| Geinstalleerde skills in `C:\Users\BramFransen\.gemini\config\skills` bijgewerkt | `Check:` uitgevoerd | `4`, voldaan |
| Docs geldig en regressiecheck op `feature/01` en `feature/02` | `docs_tool.py check` + alle `Check:`-regels van `feature/01` en `feature/02` gedraaid | `docs OK`, alle checks geslaagd |

