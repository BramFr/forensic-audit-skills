---
id: feature/04
title: Dynamische Search keywords in index.md en synchronisatie van lokale skills
category: feature
status: done
summary: Voeg ## Search keywords (~50 termen) toe aan index.md zodat audits per zoekopdracht 1-3 projecttermen meesturen en sync skills.
tags: [planner, forensic-audit, search-keywords, index, sync, domeinneutraal]
created: 2026-10-25
updated: 2026-10-27
related: [feature/01, feature/02, feature/03, bugs/01, feature/05, bugs/03, feature/06]
---

# Dynamische Search keywords in index.md en synchronisatie van lokale skills

## Why
Wanneer `docs-first-planner` (of een losse audit-skill) in Fase 2 externe bronnen zoekt via `forensic-audit`, sluiten algemene zoekopdrachten vaak niet aan op de schaal, techniek en domeincontext van het project (zoals een multi-tenant MSP-platform met 100+ klanten en 500+ devices per klant). Door een dynamische sectie `## Search keywords` (~30-50 vaktermen) in `./docs/index.md` op te nemen en de AI per zoekopdracht 1 tot 3 passende termen te laten selecteren, blijven de skills zelf 100% domeinneutraal terwijl elke zoekactie precies past bij het specifieke project. Daarnaast worden de lokaal bijgewerkte skills en deze repository volledig gesynchroniseerd.
Visie: "Ze werken in elk vakgebied" en "eisen bewijs in plaats van schijn".

## Starting point (audit findings)
- Verified: Python byte-vergelijking (`⚙️ EXECUTED`) toont dat `docs-first-planner` (`SKILL.md`, `audit-brief.md`, `plan-template.md`) en `forensic-site-audit/SKILL.md` (HAR-eis #6) lokaal nieuwer zijn, terwijl `forensic-security-audit/SKILL.md` in de repo nieuwer is (commit `e710a83` met Fase 0/2/5).
- Verified: `scripts/docs_tool.py` (`cmd_index`, r.92-99, `⚙️ EXECUTED`) vervangt uitsluitend het blok tussen `<!-- INDEX:START -->` en `<!-- INDEX:END -->`, waardoor `## Search keywords` boven `## Items` veilig behouden blijft.
- Verified: Empirische zoektest met `search_website` (`⚙️ EXECUTED` + `🔎 SOURCED`): het letterlijk meesturen van alle ruwe visiewoorden (`msp "100+ klanten" "500+ devices" canvas infra document system`) levert irrelevante treffers op ("Canvas LMS Customers", "MSP 501 top 100 list"), terwijl selectieve technische en schaal-zoekwoorden (`"network topology" OR "DAG" graph visualization canvas hierarchical layout 500 nodes quadtree` en `Sugiyama hierarchical DAG graph layout`) direct primaire vakbronnen opleveren (`https://cs.brown.edu/people/rtamassi/gdhandbook/chapters/hierarchical.pdf`, `🔎 SOURCED`).
- Verified: LLM Query Expansion Survey (`https://arxiv.org/html/2509.07794`, `🔎 SOURCED`), DuckDuckGo Search Syntax (`https://duckduckgo.com/duckduckgo-help-pages/results/syntax`, `🔎 SOURCED`) en ISO 25964-1 / NISO Controlled Vocabularies (`https://www.niso.org/schemas/iso25964`, open primaire tegenhanger voor betaalde norm ISO 25964-1, `🔎 SOURCED`) bevestigen dat selectieve termselectie (1-3 contextuele vaktermen per query) recall en precisie verhoogt zonder query-intent-drift.
- Corrected: Aanname dat het onverkort voorplakken van alle projectwoorden bij elke zoekopdracht betere zoekresultaten geeft; selectieve keuze (1-3 relevante vaktermen per auditpunt uit een rijke pool van ~30-50 termen) voorkomt vervuiling van specifieke RFC/API/norm-zoekopdrachten.
- Unverified: `https://nlp.stanford.edu/IR-book/html/htmledition/query-expansion-1.html` gaf een connectie-timeout (`ERROR: curl (28) Timeout after 21221 ms`, fail-closed niet meegeteld als `🔎`); opgevangen via primaire bron `https://arxiv.org/html/2509.07794` (`🔎 SOURCED`).

## Decisions (from the grill)
| Question | Decision | Reason |
| --- | --- | --- |
| Hoe synchroniseren we lokaal en repo? | Synchroniseer de 4 kern-skills: neem nieuwere lokale updates over van `docs-first-planner` en `forensic-site-audit`, behoud repo-versie van `forensic-security-audit` (`e710a83`), laat `ponytail` en `zabbix-msp-trigger-injector` lokaal | Behoudt alle recente verbeteringen aan beide kanten zonder verlies |
| Vorm van de zoekwoordensectie in `index.md`? | Eén platte lijst onder `## Search keywords` (bijv. `[term1, term2, ...]`) van ca. 30-50 technische, domein- en schaaltermen, dynamisch bijgewerkt naarmate functies worden toegevoegd | Eenvoudig, overzichtelijk en groeit automatisch mee met het project en `./docs` |
| Hoe en waar gebruikt de AI `## Search keywords`? | In alle 4 de skills (`docs-first-planner`, `forensic-audit`, `forensic-security-audit`, `forensic-site-audit`): kies per zoekopdracht 1 tot 3 passende trefwoorden uit `## Search keywords` (`{gekozen keywords} {zoekvraag}`) | Voorkomt query-stuffing en werkt ook bij losse aanroepen van `forensic-audit` |
| Hoe omgaan met ontbrekende `## Search keywords` & `InfraDoc`? | Neem `## Search keywords` op in `plan-template.md` en `docs_tool.py` (`SKELETON`), laat `docs-first-planner` bij ontbreken/nieuwe features de lijst afleiden/uitbreiden en opslaan in Fase 5, en voeg direct ~50 keywords toe aan `forensic-audit-skills/docs/index.md` én `InfraDoc/docs/index.md` | Direct werkend in beide projecten en backward-compatible voor `docs_tool.py check` |

## Scope
- In:
  - Synchronisatie van `docs-first-planner` (`SKILL.md`, `references/audit-brief.md`, `references/plan-template.md`), `forensic-audit/SKILL.md`, `forensic-security-audit/SKILL.md` en `forensic-site-audit/SKILL.md` tussen `D:\Github Projects\forensic-audit-skills\skills` en `C:\Users\BramFransen\.gemini\config\skills`.
  - Domeinneutrale instructie voor `## Search keywords` (~30-50 termen, selectief 1-3 per query meesturen, dynamisch bijwerken in Fase 1/3/5) in alle 4 de skills, `references/audit-brief.md`, `references/plan-template.md`, `scripts/docs_tool.py` (`SKELETON`) en `README.md`.
  - Toevoegen van `## Search keywords` (~50 project-specifieke termen) aan `./docs/index.md` in deze repo én aan `D:\Github Projects\InfraDoc\docs\index.md`.
- Out (explicitly not doing):
  - Geen domein-specifieke IT/MSP-woorden hardcoden in de skill-instructies zelf.
  - `ponytail` en `zabbix-msp-trigger-injector` niet toevoegen aan deze repository.
  - Bestaande repo's zonder `## Search keywords` niet laten falen in `docs_tool.py check`.

## Approach
1. Werk `skills/docs-first-planner/SKILL.md`, `references/audit-brief.md`, `references/plan-template.md` en `scripts/docs_tool.py` (`SKELETON`) bij met de lokale verbeteringen én de domeinneutrale `## Search keywords`-workflow -> verify: `Select-String skills/docs-first-planner/SKILL.md -Pattern "Search keywords" -Quiet`
2. Voeg de `## Search keywords`-zoekregel (1-3 passende termen per query) en de lokale HAR-eis toe aan `skills/forensic-audit/SKILL.md`, `skills/forensic-security-audit/SKILL.md` en `skills/forensic-site-audit/SKILL.md`, en werk `README.md` bij -> verify: `(Select-String skills/*/SKILL.md -Pattern "Search keywords" -List | Measure-Object).Count`
3. Voeg `## Search keywords` (~50 termen) toe aan `./docs/index.md` in `forensic-audit-skills` en aan `D:\Github Projects\InfraDoc\docs\index.md` -> verify: `Select-String "D:\Github Projects\InfraDoc\docs\index.md" -Pattern "## Search keywords" -Quiet`
4. Kopieer alle bijgewerkte bestanden van de 4 kern-skills naar `C:\Users\BramFransen\.gemini\config\skills` zodat lokaal en repo 100% identiek zijn -> verify: Python byte-vergelijking geeft `0` verschillen voor alle 8 bestanden in `skills/`.
5. Regenereren van `./docs/index.md` en draaien van `docs_tool.py check` en alle regressiechecks (`feature/01` t/m `feature/04`) -> verify: `py skills/docs-first-planner/scripts/docs_tool.py check`

## Acceptance criteria
- [x] Alle 4 de skills in `skills/*/SKILL.md` én `references/audit-brief.md`, `references/plan-template.md`, `GEMINI.md`, `CLAUDE.md` en `.cursor/rules/forensic-audit.mdc` verplichten voorafgaand aan elke zoekactie (`web-search` / `search_website`) te controleren of `./docs/index.md` met `## Search keywords` aanwezig is (aanwezig -> 1-3 passende termen meesturen; niet aanwezig / losse vraag -> normale zoekstroom).
  Check: `(Select-String skills/*/SKILL.md,skills/docs-first-planner/references/audit-brief.md,skills/docs-first-planner/references/plan-template.md,GEMINI.md,CLAUDE.md,.cursor/rules/forensic-audit.mdc -Pattern 'Search keywords' -List | Measure-Object).Count` -> `9`
- [x] `scripts/docs_tool.py` bevat `## Search keywords` in `SKELETON` en behoudt de sectie bij `docs_tool.py index`.
  Check: `Select-String skills/docs-first-planner/scripts/docs_tool.py -Pattern "## Search keywords" -Quiet` -> `True`
- [x] Alle 8 bestanden in `skills/` zijn byte-voor-byte identiek tussen `D:\Github Projects\forensic-audit-skills\skills` en `C:\Users\BramFransen\.gemini\config\skills`.
  Check: `py -c "import pathlib; loc=pathlib.Path(r'C:\Users\BramFransen\.gemini\config\skills'); rep=pathlib.Path(r'D:\Github Projects\forensic-audit-skills\skills'); print(sum((loc/p.relative_to(rep)).read_bytes()!=p.read_bytes() for p in rep.rglob('*') if p.is_file()))"` -> `0`
- [x] Zowel `./docs/index.md` in deze repo als `D:\Github Projects\InfraDoc\docs\index.md` bevatten een `## Search keywords` sectie met project-specifieke vaktermen.
  Check: `Select-String docs/index.md,"D:\Github Projects\InfraDoc\docs\index.md" -Pattern "^## Search keywords" -List | Measure-Object | Select-Object -ExpandProperty Count` -> `2`
- [x] `docs_tool.py check` geeft `docs OK` in beide projecten.
  Check: `python skills/docs-first-planner/scripts/docs_tool.py check` -> `docs OK`

## Risks and open points
- Wanneer een gebruiker in een niet-Engelstalig project werkt maar naar internationale technische standaarden of RFC's zoekt, werken Engelstalige vaktermen in `## Search keywords` beter dan puur lokale woorden; daarom bevat `## Search keywords` de internationale vak-/technische termen naast relevante lokale termen.
- `https://nlp.stanford.edu/IR-book/html/htmledition/query-expansion-1.html` was tijdens de audit niet bereikbaar wegens een connectie-timeout (`curl (28)`); onderbouwd via `https://arxiv.org/html/2509.07794` (`🔎 SOURCED`).

## Relations
- Bouwt voort op: `feature/01`, `feature/02`, `feature/03`.

## Verification
| Criterion | How checked | Result |
| --- | --- | --- |
| `Search keywords` in 4 skills + `audit-brief.md` + `plan-template.md` | `Check:` uitgevoerd (`Select-String`) | `6`, voldaan |
| `## Search keywords` in `docs_tool.py` (`SKELETON`) en behoud bij `index` | `Check:` uitgevoerd + `docs_tool.py index` gedraaid | `True`, sectie blijft intact, voldaan |
| 100% byte-identieke sync tussen repo en `C:\Users\BramFransen\.gemini\config\skills` | `Check:` uitgevoerd (Python byte-vergelijking over alle 8 bestanden) | `0` verschillen, voldaan |
| `## Search keywords` aanwezig in `forensic-audit-skills/docs/index.md` én `InfraDoc/docs/index.md` | `Check:` uitgevoerd + `docs_tool.py check` op beide repo's | `2` en `docs OK` op beide repo's, voldaan |
| Regressiecheck op `feature/01`, `feature/02`, `feature/03` | Alle `Check:`-regels van `feature/01` t/m `feature/03` uitgevoerd | Alle geslaagd (`docs OK`), voldaan |
| Regressiecheck (2026-10-27): `Search keywords` in 9 bestanden + `SKELETON` in `docs_tool.py` | `(Select-String skills/*/SKILL.md,skills/docs-first-planner/references/audit-brief.md,skills/docs-first-planner/references/plan-template.md,GEMINI.md,CLAUDE.md,.cursor/rules/forensic-audit.mdc -Pattern 'Search keywords' -List \| Measure-Object).Count` en `Select-String skills/docs-first-planner/scripts/docs_tool.py -Pattern "## Search keywords" -Quiet` | Hersteld via `feature/06` (`bugs/02` en `bugs/03`): output opnieuw `9` en `True`, voldaan |
