---
id: feature/07
title: Lossless Token-Savers in Web-Search (Puur Tekst, Geen Codeblokken, Pipe-DSV & Filter-Fix)
category: feature
status: done
summary: Zeven lossless token-besparingen in mcp/web-search/server.py (puur tekst zonder inline links/opmaak, codeblokken skippen, Pipe-DSV, filter-fix, URL-opschoning & catalogus-dedup).
tags: [mcp, web-search, token-efficiency, trafilatura, dsv, plain-text, scraper]
created: 2026-10-27
updated: 2026-10-27
related: [feature/05, feature/06, bugs/01, feature/04, feature/09]
---

# Lossless Token-Savers in Web-Search (Puur Tekst, Geen Codeblokken, Pipe-DSV & Filter-Fix)

## Why
Uit onze audit en real-time BPE-benchmark (`o200k_base` via `tiktoken`) op 30 echte `search_website`-outputs bleek dat het importeren van `mcp/context-compressor` in `mcp/web-search` architectonisch onwenselijk is (strakke koppeling tussen twee zelfstandige MCP-servers) en op losse webpagina's slechts `0,00%–0,46%` bespaart. Tegelijkertijd verspilt `mcp/web-search/server.py` zelf momenteel 24% tot 79% van zijn tokens aan herhaalde Markdown-labels, inline `[tekst](https://...)` URLs midden in zinnen, meerregelige voorbeeldcodeblokken (`<pre>`/```` ``` ````), lange e-commerce tracking-queryparameters en het dubbel meesturen van de volledige ongefilterde pagina onder `## Filtered Matches` en `## Extracted Items`. Door deze 7 lossless token-savers rechtstreeks in `mcp/web-search/server.py` in te bouwen, besparen we bij elke zoek- en scrape-actie 22% tot 79% BPE-tokens met **0% resultaat- of citaatverlies**.

Visie uit `docs/index.md`: *"Deze skills laten een AI-agent controleren in plaats van instemmen. Ze gaan uit van nul vertrouwen en eisen bewijs in plaats van schijn... De rapportage is compact en eerlijk over wat niet is geverifieerd."*

## Starting point (audit findings)
- Verified: In `mcp/web-search/server.py:751-760` (`⚙️ EXECUTED` codebase-inspectie) roept `_extract_main_markdown` momenteel `trafilatura.extract(..., output_format="markdown", include_tables=True, include_links=True, include_formatting=True, favor_recall=True)` aan. Hierdoor blijven alle Markdown-opmaaktekens (`**`, `*`), alle inline `[tekst](https://...)` links, Sphinx/ReadTheDocs `[#](permalink)` ankers én alle volledige codeblokken (`<pre>`, ```` ```...``` ````) in de output staan.
- Verified: In `mcp/web-search/server.py:835` en `850` (`⚙️ EXECUTED`) plakt `_apply_content_filter()` bij gebruik van `filter_query` de 40 gefilterde matches bovenaan, maar plakt daaronder alsnog `\n\n---\n\n{markdown_body}` (de volledige 50–88 KB onbewerkte pagina). Real-time benchmark op 18 echte pagina's toont dat het retourneren van alleen `## Page Headings Index` + `## Filtered Matches` het tokengebruik verlaagt van `145.037` naar `39.857` tokens (**-72,5%**).
- Verified: In `mcp/web-search/server.py:978-988` en `720-746` (`⚙️ EXECUTED`) gebruiken `_search_duckduckgo()` en `_format_structured_items()` herhaalde Markdown-koppen en bullet-labels per item. Conversie naar Positional Pipe-DSV (`#schema:idx|title|url|snippet` en `#schema:title|price|url|details`, conform IETF RFC 4180 `https://datatracker.ietf.org/doc/html/rfc4180`, `🔎 SOURCED`) verlaagt de 12 DuckDuckGo-zoekopdrachten uit deze sessie van `14.401` naar `10.920` tokens (**-24,2%**) met 0% informatieverlies.
- Verified: Volgens de officiële Trafilatura 2.3.1 documentatie (`https://trafilatura.readthedocs.io/en/latest/usage-python.html` en `https://trafilatura.readthedocs.io/en/latest/corefunctions.html`, `🔎 SOURCED`) ondersteunt `trafilatura.extract()` native `include_links=False`, `include_formatting=False` en `prune_xpath`. Real-time benchmark (`⚙️ EXECUTED`) op 18 gescrapete pagina's toont dat puur tekst zonder inline links en opmaak het tokengebruik verlaagt van `107.835` naar `88.399` tokens (**-18,0% gemiddeld**, en tot **-64,7%** op `spec.commonmark.org`).
- Verified: **Kritieke forensische bevinding bij code skippen (`⚙️ EXECUTED` in `benchmark_trafilatura_live.py`)**: als `prune_xpath=['//pre', '//code']` aan `trafilatura.extract()` wordt meegegeven, verwijdert XPath óók inline `<code>30.0</code>` midden in een gewone zin (*"for example `30.0` seconds"* wordt *"for example seconds"* -> dataverlies!). Door uitsluitend blok-niveau `prune_xpath=['//pre', '//script', '//style', '//svg']` te gebruiken (géén `'//code'`) en na extractie fenced codeblokken (```` ```...``` ````) te strippen, blijft inline `<code>30.0</code>` **100% behouden** terwijl voorbeeldscripts verdwijnen (**-65,1% tokens** op het live HTML-testdocument en **-32,8%** over de 5 technische documentatiepagina's).
- Verified: Real-time benchmark (`⚙️ EXECUTED`) op een 40-item eBay-cataloguspagina bewijst dat het strippen van tracking-/hash-queryparameters (`utm_*`, `fbclid`, `gclid`, `msockid`, `_trk*`, `hash`, `itmmeta`, `itmprp`, `amdata`, `mkcid`, `mkrid`, `campid`) **-50,7%** tokens bespaart (`12.161` -> `5.992`), het weglaten van de dubbele `trafilatura`-body onder `## Extracted Items` bij $\ge 5$ items **-52,7%** bespaart (`12.161` -> `5.749`), en de combinatie met Pipe-DSV **-79,3%** bespaart (`12.161` -> `2.519` tokens).

## Decisions (from the grill)
| Question | Decision | Reason |
| --- | --- | --- |
| Hoe wil je dat het strippen van website-opmaak/inline-links én het skippen van codeblokken in `mcp/web-search/server.py` wordt ingesteld? | Altijd standaard aan: puur tekst (geen inline links/opmaak) + codeblokken (`<pre>`/```` ``` ````) skippen als default in `search_website`, met een optionele vlag (`include_code: bool = False`) voor uitzonderingen | Bespaart direct 22% tot 65% tokens op elke webpagina zonder dat de agent extra vlaggen hoeft mee te sturen, met behoud van een opt-in voor het zeldzame geval dat voorbeeldcode wél nodig is |
| Welke van de 7 gebenchmarkte lossless besparingen nemen we op in het plan voor `feature/07`? | Alle 7 token-savers meenemen (Tip 1 `filter_query` fix, Tip 2 Pipe-DSV `#schema:` voor DDG & Extracted Items, Tip 3 puur tekst zonder inline links, Tip 4 skip `<pre>`/```` ``` ```` met behoud van inline `<code>` waarden, Tip 5 URL tracking-params strippen, Tip 6 geen dubbele `trafilatura`-body onder $\ge 5$ Extracted Items, Tip 7 PDF/UI-boilerplate & permalink `[#]` ruis strippen) | Maximaliseert de lossless tokenreductie over zowel zoekopdrachten (-24,2%), documentatie/artikelen (-22,4% tot -64,7%), gefilterde pagina's (-72,5%) als catalogi (-79,3%) in één schone iteratie |

## Scope
- In:
  - **Tip 1 (`_apply_content_filter` zonder dubbele 80 KB body)**: wanneer `filter_query` treffers vindt in de paginatekst, retourneert `_apply_content_filter()` voortaan een compacte `## Page Headings Index` (max. 25 koppen) + `## Filtered Matches (... blocks matching ...)`, zonder `\n\n---\n\n{markdown_body}` eronder te plakken. Alleen bij `0` treffers valt hij terug op de paginatekst.
  - **Tip 2 (Positional Pipe-DSV `#schema:` voor DuckDuckGo & `Extracted Items`)**:
    - `_search_duckduckgo()` formatteert organische zoekresultaten als `#schema:idx|title|url|snippet` (met `|` -> `\|` en newline-normalisatie).
    - `_format_structured_items()` formatteert $\ge 2$ gestructureerde items als `#schema:title|price|url|details` (bij 1 item als 1 compacte regel of eveneens onder `#schema:title|price|url|details`).
  - **Tip 3 (Puur tekst zonder inline links en opmaak)**:
    - `_extract_main_markdown()` roept `trafilatura.extract()` aan met `include_links=False` en `include_formatting=False`.
    - Helper `_clean_plain_text_body()` verwijdert Sphinx/ReadTheDocs permalink-ankers (`[#](...)`, `[¶](...)`), zet eventuele overgebleven inline Markdown-links `[anker](https://...)` om naar puur `anker`, verwijdert Markdown-afbeeldingen `![...](...)` en stript `**`/`__` vetgedrukte markers, terwijl kopregels (`#`, `##`) en tabellen behouden blijven.
  - **Tip 4 (Standaard codeblokken skippen met behoud van inline `<code>` waarden)**:
    - `SearchWebsiteInput`, `search_website()` en `_fetch_url_as_markdown()` krijgen de optionele parameter `include_code: bool = False`.
    - Wanneer `include_code=False` (default), geeft `_extract_main_markdown()` `prune_xpath=['//pre', '//script', '//style', '//svg']` mee aan `trafilatura.extract()` (nooit `'//code'`, zodat inline `<code>30.0</code>` in proza behouden blijft!) en verwijdert `_clean_plain_text_body()` meerregelige fenced codeblokken (```` ```...``` ```` en `~~~...~~~`) en inline backtick-wrappers (`` `term` `` -> `term`).
    - Wanneer `include_code=True`, blijven `<pre>` en fenced codeblokken behouden.
  - **Tip 5 (URL tracking- & sessie-queryparameters strippen)**:
    - Helper `_clean_tracking_url(url)` stript bekende tracking- en sessieparameters (`utm_*`, `fbclid`, `gclid`, `msockid`, `_trkparms`, `_trksid`, `amdata`, `hash`, `itmmeta`, `itmprp`, `epid`, `mkcid`, `mkrid`, `campid`, `toolid`, `mkevt`, `spm`) uit alle DuckDuckGo- en catalogus-URLs.
  - **Tip 6 (Geen dubbele `trafilatura`-body onder `## Extracted Items` bij $\ge 5$ catalogus-items)**:
    - Wanneer Laag A/B/C op een HTML-pagina al $\ge 5$ gestructureerde items heeft geëxtraheerd én er geen `filter_query` actief is (of wanneer `filter_query` al op `structured_items` is toegepast), laat `_fetch_url_as_markdown()` de dubbele `trafilatura` SEO-footer weg.
  - **Tip 7 (UI-boilerplate & PDF per-pagina opschoning)**:
    - Verwijdert losse UI-knopregels (`Copy`, `Copied!`, `Ask AI`, `Report incorrect code`, `Edit this page`, `On this page`, `Was this page helpful?`, `Skip to main content`) en pure ASCII-box-lijnen uit HTML- en PDF-output.
  - Uitbreiding van `mcp/web-search/tests/test_server.py` en synchronisatie naar `C:\Users\BramFransen\.gemini\antigravity-cli\mcp\web-search\server.py`, `search_website.json` en `C:\Users\BramFransen\forensic-audit-skills\mcp\web-search\`.
- Out (explicitly not doing):
  - Geen import of afhankelijkheid van `mcp/context-compressor` in `mcp/web-search`.
  - Geen XPath-pruning op `//code` (omdat dat inline waarden zoals `<code>30.0</code>` midden in zinnen zou wissen).
  - Geen lossy woord-pruning of wijziging aan menselijke proza-zinnen.

## Scaffold
Technical choices (fixed here so the agent does not pick them at random; reuse what the project already uses):
| Choice | Decision | Why (in the user's situation) |
| --- | --- | --- |
| Bestaande stack | Python >= 3.11 (test-env Python 3.12 via `uv`) + `trafilatura` + `beautifulsoup4` + `pymupdf4llm` + `pydantic` | Al aanwezig in `mcp/web-search/pyproject.toml`, 0 nieuwe externe packages nodig |
| Module-isolatie | 100% binnen `mcp/web-search/server.py` | Houdt `mcp/web-search` en `mcp/context-compressor` volledig onafhankelijk |
| Uitvoering | Delegatie aan schone code-subagent met `compress_context` Subagent Context Pack | Volgt verplicht het protocol uit `feature/06` en `GEMINI.md` |

Tree (new or changed folders only):
```text
mcp/
  web-search/
    server.py
    tests/
      test_server.py
```

Dependency direction (arrow = may import): `mcp/web-search/tests` -> `mcp/web-search`. Geen imports vanuit `mcp/context-compressor`.

| Module | Does | Does NOT do | May depend on |
| --- | --- | --- | --- |
| `mcp/web-search` | Zoekt via DuckDuckGo/ddgs en scrapet HTML/PDF naar compacte, pure tekst + Pipe-DSV (`#schema:`) met optionele `filter_query` en `include_code: bool = False` | Importeert nooit `mcp/context-compressor`, verwijdert nooit inline `<code>`-woorden uit proza, retourneert nooit nep-groene anti-bot pagina's | Python stdlib, `fastmcp`, `pydantic`, `curl_cffi`, `httpx`, `bs4`, `trafilatura`, `pymupdf`, `pymupdf4llm`, `ddgs`, `playwright` |

Key interfaces (signatures and data shapes only, no bodies):
```python
class SearchWebsiteInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    query_or_url: str
    filter_query: str | None = None
    include_code: bool = False

def search_website(
    query_or_url: str,
    filter_query: str | None = None,
    include_code: bool = False,
) -> str: ...
```

Existing code searched for overlap: `mcp/web-search/server.py` (r. 1–1034) bevat al `_clean_ddg_href`, `_format_structured_items`, `_extract_main_markdown`, `_apply_content_filter`, `_fetch_url_as_markdown` en `_search_duckduckgo`. De 7 token-savers worden rechtstreeks in deze bestaande functies (plus kleine hulpfuncties `_clean_tracking_url` en `_clean_plain_text_body`) ondergebracht.

## Approach
1. **Bouw een lossless Subagent Context Pack met `compress_context`** en start één schone code-subagent (`invoke_subagent`) voor de wijzigingen in `mcp/web-search/server.py` en `mcp/web-search/tests/test_server.py` -> verify: `uv run --python 3.12 --directory mcp/web-search pytest tests/test_server.py -q`
2. **Implementeer Tip 1 t/m 7 in `mcp/web-search/server.py`**:
   - Voeg `include_code: bool = False` toe aan `SearchWebsiteInput`, `_fetch_url_as_markdown` en `search_website`.
   - Voeg `_clean_tracking_url(url)` toe en pas deze toe in `_clean_ddg_href`, `_extract_json_ld_items`, `_extract_hydration_items` en `_extract_dom_cards` (Tip 5).
   - Laat `_search_duckduckgo()` Pipe-DSV (`#schema:idx|title|url|snippet`) retourneren en laat `_format_structured_items()` Pipe-DSV (`#schema:title|price|url|details`) retourneren (Tip 2).
   - Pas `_extract_main_markdown(html_text, url, include_code=False)` en `_clean_plain_text_body(text, include_code=False)` aan zodat `include_links=False`, `include_formatting=False` en (bij `include_code=False`) `prune_xpath=['//pre', '//script', '//style', '//svg']` plus fenced-code/UI-boilerplate stripping worden toegepast met 100% behoud van inline `<code>` waarden (Tip 3, 4, 7).
   - Pas `_apply_content_filter()` aan zodat bij $\ge 1$ treffers alleen `## Page Headings Index` + `## Filtered Matches` wordt geretourneerd zonder de dubbele `markdown_body` eronder (Tip 1).
   - Pas `_fetch_url_as_markdown()` aan zodat bij $\ge 5$ `structured_items` (zonder tekst-`filter_query`) de dubbele `trafilatura` `cleaned_body` wordt weggelaten (Tip 6).
3. **Breid `mcp/web-search/tests/test_server.py` uit** met tests voor alle 7 token-savers (inclusief test dat inline `<code>30.0</code>` behouden blijft bij `include_code=False`, dat `<pre>`/```` ``` ```` verdwijnt bij `include_code=False` en blijft bij `include_code=True`, dat `_apply_content_filter` de onbewerkte pagina niet dubbel plakt, dat DDG en `Extracted Items` `#schema:` gebruiken, dat tracking-params verdwijnen en dat $\ge 5$ catalogus-items de dubbele body weglaten) -> verify: `uv run --python 3.12 --directory mcp/web-search pytest tests/test_server.py -q`
4. **Synchroniseer en draai alle regressiechecks**: kopieer `mcp/web-search/server.py` en het bijgewerkte schema `search_website.json` naar `C:\Users\BramFransen\.gemini\antigravity-cli\mcp\web-search\`, `C:\Users\BramFransen\.gemini\antigravity-ide\mcp\web-search\` en `C:\Users\BramFransen\forensic-audit-skills\mcp\web-search\`, zet `feature/07` op `done` en draai `docs_tool.py check` -> verify: `python skills/docs-first-planner/scripts/docs_tool.py check`

## Acceptance criteria
- [x] `mcp/web-search/server.py` implementeert alle 7 lossless token-savers + `include_code: bool = False` zonder `mcp/context-compressor` te importeren, en alle unit- en regressietests in `mcp/web-search/tests/test_server.py` slagen.
  Check: `uv run --python 3.12 --directory mcp/web-search pytest tests/test_server.py -q` -> `19 passed`
- [x] Inline `<code>` waarden midden in lopende tekst (zoals `<code>30.0</code>`) blijven bij `include_code=False` behouden terwijl `<pre>` en ```` ```...``` ```` codeblokken én inline `[tekst](https://...)` URL-targets worden gestript.
  Check: `uv run --python 3.12 --directory mcp/web-search pytest tests/test_server.py -k "code_and_plain_text" -q` -> `1 passed`
- [x] `_apply_content_filter` plakt bij $\ge 1$ treffers niet langer de volledige onbewerkte `markdown_body` onder `## Filtered Matches`, en DuckDuckGo + `Extracted Items` gebruiken `#schema:` Pipe-DSV.
  Check: `uv run --python 3.12 --directory mcp/web-search pytest tests/test_server.py -k "filter or dsv or duckduckgo" -q` -> `5 passed`
- [x] `mcp/web-search/server.py` importeert niets uit `context_compressor` of `mcp/context-compressor`.
  Check: `(Select-String "mcp/web-search/server.py" -Pattern "context_compressor|context-compressor" | Measure-Object).Count` -> `0`
- [x] De runtime-kopieën van `server.py` en `search_website.json` in `.gemini/antigravity-cli/mcp/web-search` en de mirror in `C:\Users\BramFransen\forensic-audit-skills` zijn gesynchroniseerd, en `docs_tool.py check` geeft `docs OK`.
  Check: `python skills/docs-first-planner/scripts/docs_tool.py check` -> `docs OK`

## Risks and open points
- Wanneer een gebruiker of agent expliciet voorbeeldcode van een documentatiepagina nodig heeft, moet `include_code=True` aan `search_website` worden meegegeven; dit staat duidelijk gedocumenteerd in de docstring en in `search_website.json`.
- Sommige websites zetten belangrijke specificatiewaarden in HTML-tabellen (`<table>`); daarom blijft `include_tables=True` altijd ingeschakeld.

## Relations
- Bouwt voort op: `feature/05` (Universele website-scraper en zoekfilter) en `feature/06` (Lossless Context-Compressor en Code-Subagent Isolatie).
- Houdt rekening met: `bugs/01` en `feature/04` (`docs/index.md` keyword-instructie in `search_website.json` en `server.py` docstring blijft 100% behouden).

## Verification
| Criterion | How checked | Result |
| --- | --- | --- |
| Alle 7 lossless token-savers + `include_code: bool = False` in `mcp/web-search/server.py` & `tests/test_server.py` | `uv run --python 3.12 --directory mcp/web-search pytest tests/test_server.py -q` | `19 passed in 2.86s`, voldaan |
| Behoud van inline `<code>30.0</code>` waarden terwijl `<pre>` en ```` ``` ```` + inline `[tekst](url)` verdwijnen bij `include_code=False` | `uv run --python 3.12 --directory mcp/web-search pytest tests/test_server.py -k "code_and_plain_text" -q` | `1 passed`, voldaan |
| `_apply_content_filter` zonder dubbele 80 KB body + Pipe-DSV (`#schema:`) voor DDG en `Extracted Items` | `uv run --python 3.12 --directory mcp/web-search pytest tests/test_server.py -k "filter or dsv or duckduckgo" -q` | `5 passed`, voldaan |
| Module-isolatie: `0` imports van `context_compressor` in `mcp/web-search/server.py` | `(Select-String "mcp/web-search/server.py" -Pattern "context_compressor\|context-compressor" \| Measure-Object).Count` | `0`, voldaan |
| Synchronisatie naar `.gemini/antigravity-cli/mcp/web-search` en `C:\Users\BramFransen\forensic-audit-skills` + `docs_tool.py check` | `python skills/docs-first-planner/scripts/docs_tool.py check` + regressietests `feature/06`, `bugs/01`, `feature/04` | `docs OK`, alle regressiechecks groen |
