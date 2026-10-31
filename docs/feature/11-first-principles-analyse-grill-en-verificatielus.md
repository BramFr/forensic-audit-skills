---
id: feature/11
title: First-principles analyse, grill van 3-10 vragen en web-geverifieerde antwoordlus in docs-first-planner
category: feature
status: done
summary: Fase 2.5 (7 dimensies + systeemanalyse), grill 3-10 vragen in rondes en fase 3.5 die antwoorden opnieuw nazoekt.
tags: [planner, docs-first-planner, first-principles, grill, verificatie, domeinneutraal, web-search]
created: 2026-10-30
updated: 2026-10-30
related: [feature/03, feature/04, feature/09, bugs/05]
---

# First-principles analyse, grill van 3-10 vragen en web-geverifieerde antwoordlus in docs-first-planner

## Why
De planner stelde na de audit één vraag per keer en stopte zodra het plan in vijf regels paste. Daardoor bleven kritieke randvoorwaarden (grenzen, breekpunten, omkeerbaarheid) soms onbesproken. Ook werden de antwoorden van de gebruiker niet opnieuw tegen bronnen gecontroleerd. De gebruiker wil een domeinneutrale first-principles intake (INCOSE, cybernetische terugkoppeling, FMEA). Na de audit moet die minimaal 3 en maximaal 10 vragen stellen en elk antwoord opnieuw nazoeken met `search_website`. Bij nieuwe gaten mag hij altijd doorvragen.

## Starting point (audit findings)
- Verified: `skills/docs-first-planner/SKILL.md` (158 regels) had de flow `0 -> 1 -> 2 -> 3 Grill -> 4 -> 5`, "one question at a time" en een lichte re-audit trigger. De drie kopieën (repo, `.gemini\config\skills`, `C:\Users\BramFransen\forensic-audit-skills`) waren vooraf byte-identiek.
- Corrected: de bron-skill gebruikt een zekerheidsdrempel van "80%". Dat is schijnprecisie, dus die is vervangen door bewijslabels: een stap haalt de drempel alleen met 🔎 SOURCED, een gereproduceerde test of echte code of meting.
- Out by design: fase 3 van de bron-skill (meteen code of stappenplan opleveren) botst met "this skill plans; it does not implement". Die fase is daarom omgezet naar extra plan-checks (geen dode paden, keten volledig doorlopen).

## Decisions (from the grill)
| Question | Decision | Reason |
| --- | --- | --- |
| Vragen één voor één of in rondes? | Rondes van 3-5 vragen | Minimaal 3 vragen één voor één kost te veel beurten |
| Max 10 per plan of per ronde? | 10 per plan; daarna alleen meer op expliciet verzoek ("vraag verder") | Voorkomt verhoor-moeheid; open gaten gaan als onbevestigd het plan in |
| 80%-drempel als percentage? | Nee, bewijslabels (🔎 / test / code) | Percentage is schijnprecisie |
| Plan-item en sync naar geïnstalleerde kopieën? | Ja, beide | Werkwijze van dit project (feature/04, feature/09) |
| Zichtbaarheid 7-delige systeemanalyse (na proefruns)? | Alleen tonen bij `full report`; in compacte modus alleen D1-D7 tabel (1 regel per dimensie) | Compacte modus moet compact blijven |
| Persoon & plan-definitie bij niet-software (na proefruns)? | Domeinneutrale persona ("specialist engineer/architect") en bij niet-software is de gekwantificeerde specificatie zelf het plan in `./docs`; losse eenmalige checks zonder `./docs` horen bij `forensic-audit` | Houdt `docs-first-planner` 100% domeinneutraal én trouw aan `./docs` |

## Scope
- In:
  - Nieuw: `skills/docs-first-planner/references/first-principles.md` (7 dimensies, 7-delige systeemanalyse, grill-regels, fase 3.5 met confidence gate en circuit breaker, plan-check-aanvullingen), in het Engels en domeinneutraal.
  - `SKILL.md`: description, flow, fase 2.5, hand-over, grill-regels (3-10, rondes), fase 3.5 (vervangt de re-audit trigger), plancheck.
  - `references/audit-brief.md` (re-audit valt binnen fase 3.5) en `README.md` (skill-rij).
  - Sync naar `C:\Users\BramFransen\.gemini\config\skills` en `C:\Users\BramFransen\forensic-audit-skills`.
- Out (explicitly not doing):
  - Implementatie of code opleveren door de planner (fase 3 van de bron-skill).
  - Wijzigingen aan `forensic-audit`, `forensic-security-audit`, `forensic-site-audit` of `docs_tool.py`.

## Approach
1. Schrijf `references/first-principles.md` -> verify: het bestand bevat de 7 dimensies en de secties "Phase 2.5", "Grill rules", "Phase 3.5" en "Plan check additions".
2. Pas `SKILL.md`, `audit-brief.md` en `README.md` aan -> verify: `docs_tool.py check` geeft `docs OK`.
3. Synchroniseer de skill naar beide kopieën -> verify: byte-vergelijking geeft `0`.

## Acceptance criteria
- [x] `SKILL.md` bevat fase 2.5, fase 3.5, de regel 3-10 vragen in rondes en verwijst naar `references/first-principles.md`; "one question at a time" komt niet meer voor.
  Check: `py -c "t=open(r'skills/docs-first-planner/SKILL.md',encoding='utf-8').read(); print(all(s in t for s in ['### Phase 2.5','### Phase 3.5','3 to 10 questions','references/first-principles.md']) and 'one question at a time' not in t)"` -> `True`
- [x] Docs zijn consistent.
  Check: `py skills/docs-first-planner/scripts/docs_tool.py check` -> `docs OK`
- [x] Repo en de geïnstalleerde kopie van `docs-first-planner` in `C:\Users\BramFransen\.gemini\config\skills\docs-first-planner` zijn byte-identiek.
  Check: `py -c "import pathlib; r=pathlib.Path(r'D:\Github Projects\forensic-audit-skills\skills\docs-first-planner'); b=pathlib.Path(r'C:\Users\BramFransen\.gemini\config\skills\docs-first-planner'); print(sum(not (b/p.relative_to(r)).exists() or (b/p.relative_to(r)).read_bytes()!=p.read_bytes() for p in r.rglob('*') if p.is_file() and '__pycache__' not in p.parts))"` -> `0`
- [x] Handmatig: drie proefruns (IT: self-hosted Vaultwarden voor MSP; Bouw: jaren-30 tussenmuur verwijderen; Recept: one-pan eiwitrijk & caloriearm voor 2 personen) laten het D1-D7 dimensie-overzicht zien, stellen 3-5 vragen in de eerste ronde, zoeken de antwoorden in fase 3.5 opnieuw na met `search_website` en vangen parameter-mismatches op via de circuit breaker.

## Risks
- Meer vragen en extra zoekacties kosten meer tokens en tijd per plan; begrensd door het maximum van 10 vragen en het intern houden van de 7-delige systeemanalyse in compacte modus.

## Verification
| Criterion | How checked | Result |
| --- | --- | --- |
| Inhoud `SKILL.md` | `Check:` uitgevoerd (2026-10-30) | `True`, voldaan |
| `docs_tool.py check` | `Check:` uitgevoerd (2026-10-30) | `docs OK`, voldaan |
| Sync 3 kopieën | `Check:` uitgevoerd (2026-10-30) | `0` verschillen, voldaan |
| Proefrun 3 domeinen (IT, Bouw, Recept) | Uitgevoerd met echte `search_website` calls en verwerkt in skilltekst (2026-10-30) | Alle 3 geslaagd (`PASS` op alle checkpoints; circuit breaker ving M365 OAuth2/Caddy DNS-01 in IT, brandwerendheid NEN 6069 in Bouw en kabeljauw-eiwitgat/bereidingspad in Recept) |
| Regressiecheck (2026-10-30): pad-consolidatie naar `D:\Github Projects\forensic-audit-skills` (`bugs/05`) | `Check:` bijgewerkt naar `.gemini\config\skills\docs-first-planner` en uitgevoerd | `0` verschillen, voldaan |
