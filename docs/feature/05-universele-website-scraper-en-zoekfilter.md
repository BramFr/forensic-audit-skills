---
id: feature/05
title: Universele 3-laags website-scraper, anti-bot sessierotatie en URL+zoekfilter in web-search
category: feature
status: done
summary: Voeg 3-laags extractie (JSON-LD, SSR hydration, DOM-cards), anti-bot sessierotatie en URL+zoekfilter toe aan server.py.
tags: [web-search, mcp, scraper, json-ld, hydration, anti-bot, filter-query, forensic-audit]
created: 2026-10-26
updated: 2026-10-26
related: [bugs/01, feature/04, feature/06, feature/07, feature/09]
---

# Universele 3-laags website-scraper, anti-bot sessierotatie en URL+zoekfilter in web-search

## Why
Bij het rechtstreeks openen van e-commerce-, marktplaats- en zoekresultaatpagina's (zoals eBay, Coolblue en Marktplaats) faalt `mcp/web-search/server.py` op twee vlakken: (1) anti-bot/WAF-pagina's (`Error Page | eBay - Something went wrong on our end`, `splashui/challenge`) blokkeren eenmalige `chrome`-requests of worden door het ontbreken van soft-block detectie en een verouderde hardcoded `Chrome/131.0.0.0` User-Agent in Playwright ten onrechte als geldige pagina-inhoud teruggegeven; en (2) zelfs bij `HTTP 200` (1,44 MB HTML op eBay, 1,50 MB op Coolblue, 776 KB op Marktplaats) stript `trafilatura.extract()` alle productkaarten, prijzen en advertenties omdat het alleen lopende artikeltekst zoekt. Daarnaast ontbreekt de mogelijkheid om in één aanroep een URL gericht te filteren op basis van de zoekvraag van de gebruiker.
Visie uit `docs/index.md`: *"Ze gaan uit van nul vertrouwen en eisen bewijs in plaats van schijn... Ze werken in elk vakgebied: code, websites, beveiliging, planning, bakken, auto's, het trainen van een hond. De rapportage is compact en eerlijk over wat niet is geverifieerd."*

## Observed error & 7-step diagnosis (eBay `P8` failure)
```text
P8 (⚠️ Failed URL op eBay live HTML): Rechtstreeks openen van https://www.ebay.nl/sch/i.html?_nkw=nvidia+tesla+p40&_sop=15 gaf een anti-bot pagina (Something went wrong on our end); eBay-prijzen (P40 ~€ 245, MI50 32GB ~€ 497–€ 550) zijn daarom alleen geverifieerd via zoekresultaat-snippets (🔍).
```

- **Discover:** Domein: Web Scraping, HTTP/TLS Fingerprinting, Anti-Bot/WAF Challenge Handshakes en Structured Web Data Extraction (Schema.org JSON-LD, Next.js SSR Hydration, HTML5 DOM). Bestudeerde primaire bronnen: Trafilatura Core Functions (`https://trafilatura.readthedocs.io/en/latest/corefunctions.html`, `🔎 SOURCED`), `curl_cffi` Impersonate Targets (`https://curl-cffi.readthedocs.io/en/latest/impersonate/targets.html`, `🔎 SOURCED`), Cloudflare Challenges Troubleshooting (`https://developers.cloudflare.com/cloudflare-challenges/troubleshooting/challenge-solve-issues/`, `🔎 SOURCED`), Schema.org `ItemList` Specification (`https://schema.org/ItemList`, `🔎 SOURCED`), Next.js `getServerSideProps` & SSR Hydration (`https://nextjs.org/docs/pages/building-your-application/data-fetching/get-server-side-props`, `🔎 SOURCED`), W3C WAI Page Structure `<article>`/`<li>` (`https://www.w3.org/WAI/tutorials/page-structure/content/`, `🔎 SOURCED`), Playwright Python `Browser.new_context` (`https://playwright.dev/python/docs/api/class-browser`, `🔎 SOURCED`), DuckDuckGo Search Syntax (`https://duckduckgo.com/duckduckgo-help-pages/results/syntax`, `🔎 SOURCED`), en MCP Tools Specification (`https://modelcontextprotocol.io/specification/2025-06-18/server/tools`, `🔎 SOURCED`).
- **Quote:** `Rechtstreeks openen van https://www.ebay.nl/sch/i.html?_nkw=nvidia+tesla+p40&_sop=15 gaf een anti-bot pagina (Something went wrong on our end)` — exact gereproduceerd in `mcp/web-search/server.py` (`SORRY\n\nSomething went wrong on our end\n\n0.6b661702.1792995278.8668249\n\nPlease go back and try again.`, `⚙️ EXECUTED`).
- **Signal:** Drievoudig signaal bij de bron in `mcp/web-search/server.py`:
  1. `_http_get` (r. 95–116) maakt per aanroep een wegwerp-`Session(impersonate="chrome")` aan en gooit de door Akamai/eBay gezette initiële sessiecookies (`12` cookies bij `splashui/challenge`) direct weg zonder retry op dezelfde sessie of TLS-profielrotatie (`safari260`, `safari184`, `firefox144`).
  2. `_fetch_html_via_browser` (r. 133–178) stuurt een hardcoded `Chrome/131.0.0.0` User-Agent mee terwijl de lokale Chrome-installatie `Chrome/155.0.0.0` draait (directe TLS/Client-Hints mismatch bij Akamai -> `HTTP 403 Error Page | eBay`), en mist een check op anti-bot/error-pagina's waardoor `"SORRY Something went wrong on our end"` door `trafilatura` als valide artikeltekst (`100` chars) wordt geëxtraheerd.
  3. `_html_to_markdown` (r. 337–352) gebruikt uitsluitend `trafilatura.extract()` + `_extract_portal_headlines()`, waardoor op `HTTP 200` catalogus-/zoekpagina's van 0,77–1,50 MB HTML alle productkaarten, JSON-LD `ItemList`-items en `__NEXT_DATA__`-advertenties worden weggegooid.
- **Guard:** Het fail-closed principe uit `forensic-audit` (Principle 4, r. 65: een `ERROR:` of geblokkeerde pagina telt nooit als `🔎 SOURCED`) en het Pydantic-contract (`extra="forbid"`) zijn bewuste guards. De fix voldoet aan deze guards door anti-bot/error-pagina's die na alle fallbacks nog steeds geblokkeerd zijn expliciet als `ERROR:` te laten falen (nooit fake-green) en `extra="forbid"` op `SearchWebsiteInput` te behouden.
- **Hypotheses:**
  1. *H1 (Wegwerp-sessie en einzelgänger `chrome` TLS-profiel op Akamai/eBay):* Getest met `curl_cffi` (`⚙️ EXECUTED`) -> **Bevestigd**: eenmalige `chrome`-aanroep geeft `403` of `200 splashui/challenge` (`13.276` bytes, `12` cookies), terwijl hergebruik van dezelfde sessie met profielrotatie (`safari260` / `safari184`) bij de vervolgstap met die `12`->`14` cookies direct de volledige `1.440.481` bytes HTML (`HTTP 200`) oplevert.
  2. *H2 (Hardcoded `Chrome/131.0.0.0` UA in Playwright Tier 3):* Getest met Playwright (`⚙️ EXECUTED`) -> **Bevestigd**: de lokale browser rapporteert `Chrome/155.0.0.0` in Client-Hints terwijl `server.py` `Chrome/131.0.0.0` forceert, en `_fetch_html_via_browser` controleert niet of de gerenderde pagina een anti-bot blokkade is.
  3. *H3 (`trafilatura.extract()` negeert gestructureerde e-commerce/marktplaats-data):* Getest op live HTML van eBay (`1,44 MB`), Coolblue (`1,50 MB`) en Marktplaats (`776 KB`) (`⚙️ EXECUTED`) -> **Bevestigd**: `trafilatura` extraheert `0` producten, terwijl een generieke 3-laags extractor op exact dezelfde HTML `22` complete producten uit Coolblue (JSON-LD `ItemList`), `60` advertenties uit Marktplaats (`__NEXT_DATA__` hydration JSON + `33` DOM-cards) en `20+` GPU-aanbiedingen incl. prijzen uit eBay (generieke DOM-cards) haalt.
- **Fix:** (1) Voeg `_is_antibot_or_error_page()` en sessie-hergebruik met TLS-profielrotatie (`chrome`, `safari260`, `safari184`, `firefox144`, `safari184_ios`) toe aan `_http_get`, en verwijder de hardcoded `Chrome/131.0.0.0` UA uit `_fetch_html_via_browser`; (2) breid `_html_to_markdown` uit met een universele, domeinneutrale 3-laags gestructureerde extractor (Laag A: Schema.org `application/ld+json` `ItemList`/`Product`/`Offer`; Laag B: SSR hydration JSON zoals `__NEXT_DATA__`; Laag C: generieke DOM repeating cards zoals `.s-card`, `.s-item`, `.product-card`, `.hz-Listing`, `<article>`, gededupliceerd tot 1 regel per item met max. 60 items); (3) ondersteun zowel een optionele `filter_query` parameter als inline `"https://... <zoekfilter>"` in `query_or_url` (met automatische `site:<domein> <zoekfilter>` DuckDuckGo-fallback wanneer op een start-/overzichtspagina 0 items matchen); (4) synchroniseer repo, `C:\Users\BramFransen\forensic-audit-skills`, `C:\Users\BramFransen\.gemini\config\skills` en beide `search_website.json` schema's.
- **Confirm:** Bewijs met unit- en integratietests in `pytest` (inclusief opposite test dat een anti-bot pagina `"Something went wrong on our end"` als `ERROR:` faalt wanneer alle fallbacks falen, en nooit als valide Markdown doorglipt) en verifieer `0` restanten van `Chrome/131.0.0.0`.

## Starting point (audit findings)
- Verified: In `mcp/web-search/server.py` (r. 95–116, `⚙️ EXECUTED`) gebruikt `_http_get` uitsluitend een eenmalige `curl_requests.Session(impersonate="chrome")` en mist detectie op HTTP 200 challenge-redirects zoals `ebay.nl/splashui/challenge` (`Sorry voor de onderbreking...`, `13.276` bytes).
- Verified: In `mcp/web-search/server.py` (r. 147–151, `⚙️ EXECUTED`) staat `Chrome/131.0.0.0` hardcoded als `user_agent` in `_fetch_html_via_browser`, wat botst met de geïnstalleerde `Chrome/155.0.0.0` en geen anti-bot detectie uitvoert op `page.content()`.
- Verified: In `mcp/web-search/server.py` (r. 337–352, `⚙️ EXECUTED`) haalt `_html_to_markdown` op `https://www.ebay.nl/sch/i.html?_nkw=nvidia+tesla+p40&_sop=15` slechts `482` chars op uit `1.440.800` bytes HTML (`0` prijzen/producten), op `https://www.coolblue.nl/home-cinema-sets` slechts `652` chars SEO-footer uit `1.500.093` bytes HTML (`0` producten), en op `https://www.marktplaats.nl/q/venray/?msockid=0f99aa54e56a64bb2bacbda7e4a365f9` slechts `2.410` chars zijbalk-filters uit `776.454` bytes HTML (`0` advertenties).
- Verified: Blast radius in de workspace en gekoppelde installaties (`⚙️ EXECUTED`):
  1. `D:\Github Projects\forensic-audit-skills\mcp\web-search\server.py` + `tests/test_server.py`
  2. `C:\Users\BramFransen\forensic-audit-skills\mcp\web-search\server.py` + `tests/test_server.py` (het live pad in `C:\Users\BramFransen\.gemini\antigravity-cli\mcp_config.json`)
  3. `C:\Users\BramFransen\.gemini\antigravity-cli\mcp\web-search\search_website.json` en `C:\Users\BramFransen\.gemini\antigravity-ide\mcp\web-search\search_website.json`
- Corrected: Aanname dat `trafilatura.extract(..., favor_recall=True)` + `_extract_portal_headlines()` voldoende zijn voor e-commerce-, marktplaats- en zoekresultaatpagina's; `trafilatura` is ontworpen voor artikeltekst (`https://trafilatura.readthedocs.io/en/latest/corefunctions.html`, `🔎 SOURCED`) en verwijdert productgrids en JSON-hydratiedata.
- Unverified: Websites die een interactieve menselijke CAPTCHA-puzzel of verplichte inlog achter een betaalmuur afdwingen blijven (conform het fail-closed principe) `ERROR:` geven wanneer alle geautomatiseerde TLS-profielen en headless Chrome worden geweigerd.

## Decisions (from the grill)
| Question | Decision | Reason |
| --- | --- | --- |
| Welke scope voor het scrapen en doorzoeken van websites in `mcp/web-search/server.py`? | Universele 3-laags extractie (JSON-LD + SSR hydration JSON + generieke DOM-cards) + slimme sessie/profiel-rotatie én de mogelijkheid om in één aanroep een URL + zoekfilter mee te geven | Werkt domeinneutraal op elke webshop, marktplaats of overzichtspagina zonder fragiele site-specifieke scrapers, en laat de agent direct filteren op de vraag van de gebruiker |
| Hoe richten we het URL+zoekfilter contract in `search_website` en de vastlegging in `./docs` in? | Opslaan als `feature/05` (met het 7-stappen eBay-diagnoseblok), ondersteun zowel optionele `filter_query` parameter als inline `'https://... <zoekfilter>'` + automatische `site:<domein>` fallback bij 0 treffers op de pagina, en voeg 4 nieuwe zoektermen toe aan `## Search keywords` in `docs/index.md` | Volledig backward-compatible met bestaande `search_website(query_or_url)` aanroepen en houdt `docs/index.md` leidend |

## Scope
- In:
  - **Anti-bot detectie & sessie-/TLS-profielrotatie (`_is_antibot_or_error_page` + `_http_get`)**: herken zowel HTTP >= 400 als HTTP 200 anti-bot/challenge-pagina's (`Something went wrong on our end`, `Error Page | eBay`, `Sorry voor de onderbreking`, `Pardon Our Interruption`, `splashui/challenge`, `Just a moment...`, `Attention Required! | Cloudflare`, `Access Denied`, `cc=botnet`), hergebruik de `curl_cffi` sessie bij cookie-handshakes en roteer over `("chrome", "safari260", "safari184", "firefox144", "safari184_ios")`.
  - **Playwright Tier 3 native UA & fail-closed check (`_fetch_html_via_browser`)**: verwijder de hardcoded `Chrome/131.0.0.0` User-Agent (`0 leftovers`), gebruik de dynamische native browser-UA (met `HeadlessChrome` -> `Chrome`), en controleer via `_is_antibot_or_error_page` dat een geblokkeerde browserpagina nooit als geldige Markdown wordt teruggegeven.
  - **Universele 3-laags listing- & content-extractor (`_html_to_markdown`)**:
    1. *Laag A (Schema.org JSON-LD)*: extraheer `Product`, `Offer` en `ItemList` items uit `<script type="application/ld+json">` (titel, URL, prijs/valuta, voorraadstatus, rating, beschrijving).
    2. *Laag B (SSR Hydration JSON)*: extraheer listing-objecten uit `<script id="__NEXT_DATA__">` en vergelijkbare state-scripts (titel, prijs in centen/euro's, URL/`vipUrl`, locatie/stad, beschrijving).
    3. *Laag C (Generieke DOM-cards)*: extraheer herhalende product-/zoekresultaatkaarten (`li`/`div`/`article` met card/item/listing/product/result classes), filter UI-ruis (`Nieuw venster of tabblad`, `Bewaren in Mijn Favorieten`, dummy honeypot `itm/123456`) weg en dedupliceer elk onderwerp tot exact **1 regel per item** (max. 60 items voor overzichtelijkheid op schaal).
  - **URL + zoekfilter (`filter_query` én inline `"https://... <zoekfilter>"`)**:
    - Voeg een optionele parameter `filter_query: str | None = None` toe aan `SearchWebsiteInput` en `search_website`, én splits automatisch inline zoektermen achter een URL in `query_or_url` (bijv. `"https://www.coolblue.nl/home-cinema-sets sonos"`).
    - Filter geëxtraheerde items en tekstblokken op de zoektermen en toon de matchende resultaten bovenaan; als de geopende pagina 0 treffers voor het filter bevat (bijv. een algemene startpagina), voer dan automatisch een aanvullende `site:<domein> <filter_query>` zoekopdracht uit.
  - **Synchronisatie & tests**: breid `mcp/web-search/tests/test_server.py` uit met tests voor alle nieuwe lagen + opposite test voor anti-bot fail-closed gedrag, werk beide `search_website.json` schema's (`antigravity-cli` en `antigravity-ide`) bij, voeg `JSON-LD-ItemList, SSR-hydration-extraction, TLS-fingerprint-rotation, anti-bot-detection` toe aan `## Search keywords` in `docs/index.md`, en synchroniseer alles byte-identiek naar `C:\Users\BramFransen\forensic-audit-skills` en `C:\Users\BramFransen\.gemini\config\skills`.
- Out (explicitly not doing):
  - Geen site-specifieke scrapers of aparte tools per webshop (alles blijft binnen de ene generieke `search_website` tool).
  - Geen externe betaalde CAPTCHA-solvers of proxy-diensten.
  - Geen verzwakking van de fail-closed regel: als een URL na alle profielen en Playwright nog steeds een anti-bot/error-pagina geeft, retourneert `search_website` een eerlijke `ERROR:`.

## Approach
1. Verwijder de hardcoded `Chrome/131.0.0.0` User-Agent uit `_fetch_html_via_browser` en implementeer `_is_antibot_or_error_page` + sessie-hergebruik met TLS-profielrotatie (`chrome`, `safari260`, `safari184`, `firefox144`, `safari184_ios`) in `mcp/web-search/server.py` -> verify: `(Select-String "mcp/web-search/server.py" -Pattern "Chrome/131.0.0.0" | Measure-Object).Count`
2. Implementeer de universele 3-laags extractor (`_extract_json_ld_items`, `_extract_hydration_items`, `_extract_dom_cards`) en het URL+zoekfilter (`filter_query` parameter + inline `"https://... <zoekfilter>"` + `site:<domein>` fallback) in `mcp/web-search/server.py`, en werk beide `search_website.json` schema-bestanden (`antigravity-cli` en `antigravity-ide`) bij -> verify: `(Select-String "mcp/web-search/server.py","C:\Users\BramFransen\.gemini\antigravity-cli\mcp\web-search\search_website.json","C:\Users\BramFransen\.gemini\antigravity-ide\mcp\web-search\search_website.json" -Pattern "filter_query" -List | Measure-Object).Count`
3. Voeg unit- en opposite-tests toe aan `mcp/web-search/tests/test_server.py` (voor JSON-LD `ItemList`, `__NEXT_DATA__` hydration, generieke DOM-cards, `filter_query` + inline URL-filter, en fail-closed `ERROR:` bij `"Something went wrong on our end"`) en draai `pytest` -> verify: `py -3.13 -m pytest mcp/web-search/tests/test_server.py -q`
4. Synchroniseer alle gewijzigde bestanden naar `C:\Users\BramFransen\forensic-audit-skills` en `C:\Users\BramFransen\.gemini\config\skills`, werk `## Search keywords` in `docs/index.md` bij, regenereer de index en voer `docs_tool.py check` plus alle regressiechecks uit -> verify: `python skills/docs-first-planner/scripts/docs_tool.py check`

## Acceptance criteria
- [x] `mcp/web-search/server.py` bevat geen hardcoded `Chrome/131.0.0.0` User-Agent meer (`0` restanten) en detecteert anti-bot/challenge-pagina's (`_is_antibot_or_error_page`) met automatische TLS-profielrotatie (`safari260`, `safari184`, `firefox144`).
  Check: `(Select-String "mcp/web-search/server.py" -Pattern "Chrome/131.0.0.0" | Measure-Object).Count` -> `0`
- [x] `mcp/web-search/server.py` bevat de universele 3-laags extractie (`_extract_json_ld_items`, `_extract_hydration_items`, `_extract_dom_cards`) én ondersteunt zowel de optionele `filter_query` parameter als inline `"https://... <zoekfilter>"` (vastgelegd in `server.py` en beide `search_website.json` schema's).
  Check: `(Select-String "mcp/web-search/server.py","C:\Users\BramFransen\.gemini\antigravity-cli\mcp\web-search\search_website.json","C:\Users\BramFransen\.gemini\antigravity-ide\mcp\web-search\search_website.json" -Pattern "filter_query" -List | Measure-Object).Count` -> `3`
- [x] Alle unit- en opposite-tests in `mcp/web-search/tests/test_server.py` (inclusief anti-bot fail-closed test op `"Something went wrong on our end"`, JSON-LD extractie, `__NEXT_DATA__` extractie, DOM-card extractie en URL+zoekfilter) slagen.
  Check: `py -3.13 -m pytest mcp/web-search/tests/test_server.py -q` -> `passed`
- [x] `docs/index.md` bevat de 4 nieuwe zoektermen (`JSON-LD-ItemList`, `SSR-hydration-extraction`, `TLS-fingerprint-rotation`, `anti-bot-detection`) onder `## Search keywords`, en `C:\Users\BramFransen\forensic-audit-skills` is byte-voor-byte gesynchroniseerd met deze repo.
  Check: `py -c "import pathlib; a=pathlib.Path(r'C:\Users\BramFransen\forensic-audit-skills'); b=pathlib.Path(r'D:\Github Projects\forensic-audit-skills'); files=['CLAUDE.md','GEMINI.md','README.md','.cursor/rules/forensic-audit.mdc','mcp/web-search/server.py','mcp/web-search/tests/test_server.py']+[p.relative_to(b).as_posix() for p in (b/'skills').rglob('*') if p.is_file()]; print(sum(not (a/f).exists() or (a/f).read_bytes()!=(b/f).read_bytes() for f in files))"` -> `0`
- [x] `docs_tool.py check` geeft `docs OK` en de regressiechecks van `bugs/01` en `feature/04` slagen.
  Check: `python skills/docs-first-planner/scripts/docs_tool.py check` -> `docs OK`

## Risks and open points
- Wanneer een externe website een interactieve CAPTCHA of verplichte login vereist die zowel door alle `curl_cffi` TLS-profielen als door lokale headless Chrome wordt geblokkeerd, geeft `_fetch_url_as_markdown` fail-closed `ERROR:` terug zodat de agent in een audit eerlijk terugvalt op een alternatieve primaire bron of `🔍 SNIPPET`.
- Grote cataloguspagina's kunnen honderden DOM-elementen bevatten; door het aantal geëxtraheerde gestructureerde items te begrenzen op maximaal 60 unieke items per pagina (of alle matchende items bij gebruik van `filter_query`) blijft de MCP-output compact en leesbaar.

## Relations
- Bouwt voort op: `bugs/01`, `feature/04`.

## Verification
| Criterion | How checked | Result |
| --- | --- | --- |
| `0` restanten van `Chrome/131.0.0.0` + `_is_antibot_or_error_page` & TLS-profielrotatie (`safari260`, `safari184`, `firefox144`) | `Check:` uitgevoerd (`Select-String`) + live test op `ebay.nl/sch/i.html?_nkw=nvidia+tesla+p40&_sop=15` | `0` restanten; live eBay scrape levert `48.438` chars met `31` `24GB`-matches op, voldaan |
| Universele 3-laags extractie + `filter_query` / inline URL-filter in `server.py` en 2x `search_website.json` | `Check:` uitgevoerd (`Select-String`) + live tests op Coolblue (`sonos`) en Marktplaats (`dakdekker`) | `3` bestanden bijgewerkt; Coolblue levert `22` producten (`5` Sonos-matches) en Marktplaats `31` advertenties (`1` dakdekker-match in Venray), voldaan |
| Unit- en opposite-tests in `mcp/web-search/tests/test_server.py` | `py -3.13 -m pytest mcp/web-search/tests/test_server.py -v` uitgevoerd | `14 passed in 2.90s` (incl. opposite test voor `"Something went wrong on our end"`), voldaan |
| `## Search keywords` uitgebreid en `C:\Users\BramFransen\forensic-audit-skills` 100% byte-identiek | `Check:` uitgevoerd (Python byte-vergelijking over alle 14 kernbestanden) | `0` verschillen, voldaan |
| `docs_tool.py check` en regressiechecks op `bugs/01` en `feature/04` | `docs_tool.py index --strict`, `docs_tool.py check` en alle `Check:`-regels van `bugs/01` en `feature/04` uitgevoerd | `docs OK`, alle regressiechecks geslaagd |
