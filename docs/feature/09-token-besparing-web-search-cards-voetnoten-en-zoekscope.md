---
id: feature/09
title: Token-Besparing op Web-Search Tool Calls (DOM-Card Script-Strip, Voetnoten, Artikel-Body & Zoekscope)
category: feature
status: done
summary: Bespaar 68% tot 94% op search_website tool-tokens via DOM-card <script>-strip, voetnoot-filter, artikel-behoud, max_items=20 en domein-check op Search keywords.
tags: [mcp, web-search, token-efficiency, scraper, dom-cards, filter-query, search-keywords, subagent]
created: 2026-10-28
updated: 2026-10-30
related: [feature/05, feature/07, feature/08, bugs/01, bugs/04, feature/10, bugs/05]
---

# Token-Besparing op Web-Search Tool Calls (DOM-Card Script-Strip, Voetnoten, Artikel-Body & Zoekscope)

## Why
Uit de forensische token-analyse (`⚙️ EXECUTED` op sessie `d6c1d3af-1c0b-4d18-ac5d-ad8c247ba067`, 35 tool calls = `159.679` tekens / `53.900` UI-tokens) bleek dat een enkele `/forensic-audit` zoekopdracht nog steeds `53,9k` tokens aan tool calls verbruikte door zes oorzaken: (1) het weglaten van `filter_query` bij 19 van de 20 URL-scrapes + een hoog `max_items=60` plafond waardoor pagina's boven de 10 KB CLI-drempel spilden en via `read_file` dubbel werden ingelezen, (2) geneste `<script type="application/ld+json">`-blokken binnenin productkaarten op Kleinanzeigen die door `card.text_content()` in `_extract_dom_cards` als ruwe JSON-tekst in `details` belandden en de prijs afkapten, (3) `18,6 KB` aan juridische financieringsvoetnoten (`*`, `**`, `¹`, `³`, `⁷`, `¹²`, `⁴⁸`) op `mediamarkt.de`, (4) het ten onrechte onderdrukken van de artikeltekst (`skip_duplicate_body = True`) op blogpagina's met $\ge 5$ gerelateerde `<article>`-kaarten in de footer (`blog.playstation.com`), (5) het afdwingen van software-specifieke `## Search keywords` (`zero-trust`) op losstaande consumentenvragen buiten het projectdomein (wat 6 extra zoekrondes en 70% irrelevante resultaten opleverde), en (6) het volledig inlezen van `docs/index.md` met `read_file` i.p.v. `compress_context(..., section="Search keywords")`. Door deze 6 punten op te lossen daalt het tokenverbruik op exact dezelfde 35 tool calls van `53.900` naar `16.994` tokens (**-68,5%**), en met subagent-isolatie bij $\ge 8$ web-calls naar `~2.900` tokens in de hoofdcontext (**-94,6%**).

Visie uit `docs/index.md`: *"Deze skills laten een AI-agent controleren in plaats van instemmen. Ze gaan uit van nul vertrouwen en eisen bewijs in plaats van schijn... De rapportage is compact en eerlijk over wat niet is geverifieerd."*

## Starting point (audit findings)
- Verified: In `mcp/web-search/server.py:797-805` (`⚙️ EXECUTED` codebase-inspectie + sessie-analyse `steps/21, 32, 36, 41, 42`) roept `_extract_dom_cards` `card.text_content()` aan zonder eerst `<script>`, `<style>`, `<svg>` en `<noscript>` binnen de kaart te verwijderen. Op Kleinanzeigen vult een inline `<script type="application/ld+json">` (`{"creditText":"Kleinanzeigen",...}`) de eerste 220 tekens van `details`, waardoor de prijs (`950 € VB`) wegvalt (`||`) en `3.239` BPE-tokens aan JSON-ruis plus 3 extra detail-fetches (`2.432` BPE-tokens) ontstaan.
- Verified: In `mcp/web-search/server.py:940-1003` (`⚙️ EXECUTED` op `steps/23/output.txt`, `18.627` tekens) extraheert `_extract_main_markdown` op `mediamarkt.de` 33 paragrafen met BNP Paribas / Targobank financieringsvoetnoten (`*`, `**`, `****`, `ᵂ`, `⁰`, `¹`, `³`, `⁵`, `⁷`, `¹⁰`, `¹²`, `²¹`, `⁴⁸`, `Ratenfinanzierung`, `Sollzinssatz`, `Widerrufsrecht`) en op `billiger.de` (`step 17`) 8 opeenvolgende identieke UI-regels (*"Diese Variante ist in dieser Kombination nicht verfügbar."*). Volgens de officiële Trafilatura 2.3.1 documentatie (`https://trafilatura.readthedocs.io/en/latest/usage-python.html`, `🔎 SOURCED`) verwijdert `prune_xpath` en post-extractie filtering dergelijke boilerplate zonder verlies van artikeltekst (**-86,9% tokens** op MediaMarkt).
- Verified: In `mcp/web-search/server.py:760-763` en `1046-1064` (`⚙️ EXECUTED` op `steps/40/output.txt`, `blog.playstation.com`) valt `_extract_dom_cards` terug op `//article` wanneer er geen product-classes zijn. Op een blogartikel met 8 gerelateerde posts in de footer levert dit 9 prijsloze items op, waardoor `len(structured_items) >= 5` `skip_duplicate_body = True` activeert en de volledige artikeltekst van de blogpost weggooit.
- Verified: In `mcp/web-search/server.py:532, 645, 747` (`⚙️ EXECUTED`) staat `max_items: int = 60` en bevat Marktplaats (`step 18`, `11.307` tekens) 30 items waaronder 8 `"GEZOCHT / Wij kopen jouw PS5"` (`EUR 0.00`) advertenties. Omdat de output $>10\text{ KB}$ was, spilde de CLI deze naar een bestand en las de agent in `step 20` alle `11.565` tekens opnieuw in met `read_file`. Volgens Anthropic (*Code execution with MCP*, `https://www.anthropic.com/research/code-execution-with-mcp`, `🔎 SOURCED`) voorkomt vroeg filteren (`filter_query`) en begrenzen (`max_items=20`) dat ruwe tussenresultaten dubbel door het contextwindow stromen (**-74,9% tokens** over de 7 grote scrapes).
- Verified: Volgens ISO 25964-1:2011 / ISO 25964-2:2013 (geverifieerd via open primaire tegenhanger NISO ISO 25964 Secretariat, `https://www.niso.org/schemas/iso25964`, `🔎 SOURCED`) vereist gecontroleerde query-expansie dat de gekozen thesaurustermen binnen hetzelfde onderwerpsdomein (*scope*) vallen als de zoekvraag. In `step 45` van `d6c1d3af` zorgde het meesturen van `zero-trust primary-source-verification` op een consumentenvraag (*MediaMarkt Kleve PS5 Pro*) ervoor dat 7 van de 10 DuckDuckGo-resultaten over NIST SP 800-207 cybersecurity gingen i.p.v. MediaMarkt (**-49,3% zoek-tokens** wanneer standalone vragen buiten het projectdomein geen project-keywords meesturen).
- Verified: Volgens Liu et al. (*Lost in the Middle: How Language Models Use Long Contexts*, `https://arxiv.org/abs/2307.03172`, `🔎 SOURCED`) en de LangChain Subagents documentatie (`https://docs.langchain.com/oss/python/deepagents/subagents`, `🔎 SOURCED`) degradeert opzoek-accuratesse midden in lange tool-contexten en houdt subagent-isolatie bij multi-step web-search (`>= 8` calls) de hoofdcontext 90%+ kleiner.
- Corrected: De aanname dat `len(structured_items) >= 5` altijd betekent dat een pagina een productcatalogus is waarvan de `cleaned_body` weggelaten mag worden, klopt niet bij artikelpagina's met `<article>`-kaarten zonder prijs (`blog.playstation.com`). Daarnaast draaide de achtergrond-daemon voor `context-compressor` (`PID 5224`) nog op een oude proces-instantie van vóór de update van `feature/08`.
- Unverified: none (alle 10 auditpunten zijn met `🔎 SOURCED` + `⚙️ EXECUTED` geverifieerd).

## Decisions (from the grill)
| Question | Decision | Reason |
| --- | --- | --- |
| Welke onderdelen nemen we mee in `feature/09` om het tokenverbruik van tool calls structureel te verlagen? | Alle 6 besparingen samen uitvoeren: 4 scraper-fixes in `mcp/web-search/server.py` + 2 workflow-fixes in de skills/regels (domein-check op `## Search keywords`, `compress_context` op `index.md` & web-subagent isolatie bij $\ge 8$ web-calls) + herstarten van de MCP-daemons | Bespaart direct 68,5% op de ruwe tool-outputs (en tot 94,6% in de hoofdcontext via subagent-isolatie) en herstelt tegelijk het wegvallen van prijzen op Kleinanzeigen en artikeltekst op blogs |

## Scope
- In:
  1. **DOM-Card `<script>`/`<style>`-strip, prijs-extractie & `mailto:`-filter in `_extract_dom_cards()` (`mcp/web-search/server.py`)**:
     - Verwijder op een kopie van elke `card` (of vóór extractie op `tree`) alle `<script>`, `<style>`, `<svg>` en `<noscript>` nodes vóórdat `card.text_content()` wordt aangeroepen, en strip eventuele achtergebleven `{"creditText":...}` JSON-LD fragmenten.
     - Zoek voor `price_str` eerst in `.//*[contains(@class, 'price') or contains(@id, 'price')]` voordat met regex in `details` wordt gezocht, en ondersteun bedragen vóór én na het valuta-teken (`950 €`, `1.299,99 €`, `EUR 950`, `€ 950,-`).
     - Negeer `mailto:` en `tel:` links bij het zoeken naar de item-`href` in een kaart (zoals de deel-knop op Kleinanzeigen in `step 32`).
  2. **E-commerce voetnoot-filter & opeenvolgende regel-dedup in `_clean_plain_text_body()` (`mcp/web-search/server.py`)**:
     - Strip lange juridische krediet-/voetnootregels die beginnen met voetnootmarkers (`*`, `**`, `***`, `****`, `ᵂ`, `⁰`, `¹`, `²`, `³`, `⁴`, `⁵`, `⁶`, `⁷`, `⁸`, `⁹`) wanneer ze financierings-/actie-disclaimers bevatten (`Ratenfinanzierung`, `Sollzinssatz`, `Jahreszins`, `Einkaufscoupon`, `Widerrufsrecht`, `Finanzierungspartner`, `Apple Music`).
     - Dedupliceer direct opeenvolgende identieke niet-lege tekstregels (zoals 8× *"Diese Variante ist in dieser Kombination nicht verfügbar."* op `billiger.de`).
  3. **Slimme `skip_duplicate_body` voor artikelpagina's + catalogus-plafond `max_items=20` (`mcp/web-search/server.py`)**:
     - Verlaag `max_items` in `_extract_json_ld_items`, `_extract_hydration_items` en `_extract_dom_cards` van `60` naar `20` (zodat catalogus-scrapes standaard rond de 4–6 KB blijven en nooit boven de 10 KB CLI-drempel sporen).
     - Filter in `_extract_hydration_items` en `_extract_dom_cards` "Gezocht / Wij kopen / Inkoop"-spam met `EUR 0.00` eruit wanneer er voldoende echte aanbod-items op de pagina staan.
     - Zet `skip_duplicate_body = True` in `_html_to_markdown()` bij `len(structured_items) >= 5` **uitsluitend** aan wanneer minstens 2 van de `structured_items` een niet-lege prijs kolom (`|price|`) hebben (echte catalogus/marktplaats). Als `structured_items` geen prijzen bevatten (zoals gerelateerde `<article>`-kaarten op een blog), behoud dan altijd `cleaned_body` én laat prijsloze `<article>`-kaarten weg als `len(cleaned_body) >= 400`.
  4. **Domein-relevantie check op `## Search keywords`, `compress_context` op `index.md`, `filter_query`-richtlijn & Web-Subagent Isolatie (`mcp/web-search/server.py`, `search_website.json`, `skills/*/SKILL.md`, `references/audit-brief.md`, `GEMINI.md`, `CLAUDE.md`, `.cursor/rules/forensic-audit.mdc`)**:
     - Leg vast dat de agent `./docs/index.md` leest met `compress_context(file_path="docs/index.md", section="Search keywords")` (i.p.v. een volledige `read_file`).
     - Leg vast dat `## Search keywords` verplicht zijn voor **alle vragen die het project of het projectdomein raken**, maar dat bij een **losstaande vraag buiten het projectdomein** (zoals een consumentenaankoop of niet-gerelateerde privévraag terwijl de projectmap openstaat) géén project-keywords worden meegestuurd zodat zoekresultaten niet vervuild raken.
     - Leg vast dat bij elke `search_website("https://...")` aanroep op grote pagina's of PDF's standaard `filter_query` (of inline `"https://... <trefwoorden>"`) wordt meegegeven, en dat bij zware web-audits ($\ge 8$ `search_website` aanroepen) een `research`/`self` subagent wordt ingezet die alleen een `#schema:` bewijstabel teruggeeft aan de hoofdcontext.
  5. **Uitbreiding van `mcp/web-search/tests/test_server.py`, synchronisatie & herstart van de MCP-daemons**:
     - Voeg unit- en opposite-tests toe voor Kleinanzeigen `<script>`-stripping + prijs-extractie, MediaMarkt voetnoot-stripping + regel-dedup, en behoud van de artikel-body op blogpagina's met `<article>`-footerkaarten.
     - Synchroniseer alle gewijzigde bestanden naar `.gemini` en `C:\Users\BramFransen\forensic-audit-skills` en herstart de lopende MCP-server processen zodat de nieuwe code direct in het geheugen draait.
- Out (explicitly not doing):
  - Geen koppeling of import tussen `mcp/web-search` en `mcp/context-compressor`.
  - Geen lossy tekst-inkorting op echte artikelparagrafen of primaire wets-/normteksten.

## Approach
1. **Bouw een lossless Subagent Context Pack met `compress_context` en delegeer de code- en testwijzigingen in `mcp/web-search/server.py` en `mcp/web-search/tests/test_server.py` aan een schone code-subagent (`invoke_subagent`)** -> verify: `uv run --python 3.12 --directory mcp/web-search pytest tests/test_server.py -q`
2. **Werk het tool-schema (`search_website.json`), de 4 skills (`skills/*/SKILL.md`), `skills/docs-first-planner/references/audit-brief.md`, `GEMINI.md`, `CLAUDE.md` en `.cursor/rules/forensic-audit.mdc` bij** met de domein-check op `## Search keywords`, `compress_context(file_path="docs/index.md", section="Search keywords")`, de `filter_query`-richtlijn bij URL-scrapes en subagent-isolatie bij $\ge 8$ web-calls, en synchroniseer alle kopieën -> verify: `python skills/docs-first-planner/scripts/docs_tool.py check`
3. **Herstart de lopende MCP-daemons (`context-compressor` en `web-search`) en draai een live verificatie + BPE-tokenbenchmark** op de echte pagina-outputs uit sessie `d6c1d3af` -> verify: `uv run --python 3.12 --directory mcp/web-search pytest tests/test_server.py -q`

## Acceptance criteria
- [x] `_extract_dom_cards` verwijdert `<script>`/`<style>` binnen kaarten, negeert `mailto:`-links, extraheert prijzen zoals `950 € VB` / `1.299,99 €`, en hanteert `max_items=20` als standaard in Laag A/B/C.
  Check: `uv run --python 3.12 --directory mcp/web-search pytest tests/test_server.py -k "dom_cards or kleinanzeigen" -q` -> `passed`
- [x] `_clean_plain_text_body` verwijdert e-commerce financieringsvoetnoten (`*`, `**`, `¹`, `³`, `⁷`, `¹²`, `⁴⁸` met `Ratenfinanzierung`/`Sollzinssatz`) en dedupliceert opeenvolgende identieke UI-regels, terwijl `_html_to_markdown` op artikelpagina's met prijsloze `<article>`-kaarten de hoofdtekst (`cleaned_body`) volledig behoudt.
  Check: `uv run --python 3.12 --directory mcp/web-search pytest tests/test_server.py -k "footnotes or article_body" -q` -> `passed`
- [x] Alle unit- en regressietests in `mcp/web-search/tests/test_server.py` en `mcp/context-compressor/tests/test_server.py` slagen.
  Check: `uv run --python 3.12 --directory mcp/web-search pytest tests/test_server.py -q` -> `22 passed`
- [x] `mcp/web-search/server.py`, beide `search_website.json` schema's, alle 4 de skills (`skills/*/SKILL.md`), `references/audit-brief.md`, `GEMINI.md`, `CLAUDE.md` en `.cursor/rules/forensic-audit.mdc` bevatten de aangescherpte `## Search keywords` (inclusief standalone domein-uitzondering en `compress_context` op `index.md`) en `filter_query` richtlijn, en `.gemini\config\skills` + `.gemini\antigravity-cli\mcp\web-search\server.py` zijn byte-voor-byte gesynchroniseerd.
  Check: `py -c "import pathlib; loc=pathlib.Path(r'C:\Users\BramFransen\.gemini\config\skills'); rep=pathlib.Path(r'D:\Github Projects\forensic-audit-skills\skills'); cli_srv=pathlib.Path(r'C:\Users\BramFransen\.gemini\antigravity-cli\mcp\web-search\server.py'); rep_srv=pathlib.Path(r'D:\Github Projects\forensic-audit-skills\mcp\web-search\server.py'); print(sum((loc/p.relative_to(rep)).read_bytes()!=p.read_bytes() for p in rep.rglob('*') if p.is_file() and '__pycache__' not in p.parts) + (cli_srv.read_bytes()!=rep_srv.read_bytes()))"` -> `0`
- [x] `docs_tool.py check` geeft `docs OK`.
  Check: `python skills/docs-first-planner/scripts/docs_tool.py check` -> `docs OK`

## Risks and open points
- Op sommige webpagina's begint een legitieme opsommingsregel met `* `; door alleen regels met voetnootmarkers te strippen wanneer ze e-commerce disclaimer-termen (`Ratenfinanzierung`, `Sollzinssatz`, `Jahreszins`, `Einkaufscoupon`, `Widerrufsrecht`, `Finanzierungspartner`) bevatten, worden normale Markdown-bullets nooit geraakt.

## Relations
- Bouwt voort op: `feature/05`, `feature/07`, `feature/08`, `bugs/01`, `bugs/04`.

## Verification

| Check | Result |
| --- | --- |
| `uv run --python 3.12 --directory mcp/web-search pytest tests/test_server.py -k "dom_cards or kleinanzeigen" -q` | `1 passed` |
| `uv run --python 3.12 --directory mcp/web-search pytest tests/test_server.py -k "footnotes or article_body" -q` | `2 passed` |
| `uv run --python 3.12 --directory mcp/web-search pytest tests/test_server.py -q` | `22 passed` |
| Mirror sync check (`C:\Users\BramFransen\forensic-audit-skills` vs `D:\Github Projects\forensic-audit-skills` vs `.gemini`) | `0` diffs |
| `python skills/docs-first-planner/scripts/docs_tool.py check` | `docs OK` |
| Regressiecheck (2026-10-30): pad-consolidatie naar `D:\Github Projects\forensic-audit-skills` (`bugs/05`) | `Check:` bijgewerkt naar `.gemini\config\skills` + `.gemini\antigravity-cli\mcp\web-search\server.py` (`0` diffs) |

