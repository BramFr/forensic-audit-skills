---
id: bugs/04
title: Behoud zichtbare artikel-codeblokken (<pre>) als platte tekst en strip alleen onzichtbare website-code
category: bugs
status: done
summary: Laat zichtbare <pre>/codeblokken in artikelen altijd als platte tekst staan (zonder ``` fences) en strip alleen <script>/<style>/<svg> en trailing # op koppen.
tags: [mcp, web-search, trafilatura, pre, plain-text, bugfix]
created: 2026-10-27
updated: 2026-10-27
related: [feature/05, feature/07]
---

# Behoud zichtbare artikel-codeblokken (<pre>) als platte tekst en strip alleen onzichtbare website-code

## Why
Bij het scrapen van `https://trafilatura.readthedocs.io/en/latest/usage-python.html` ontbraken alle zichtbare codevoorbeelden uit het artikel (zoals `# define document and load it with LXML\nfrom trafilatura import extract...`). De wens *"de opmaak van de website hoef ik niet, puur de tekst, alles m.b.t. code mag geskipt worden"* doelde op **onzichtbare website-/opmaakcode** (`<script>`, `<style>`, `<svg>`, `<noscript>`, `<iframe>`, HTML-tags, CSS, inline link-URLs `[tekst](https://...)` en Markdown-fences ```` ``` ````), en **niet** op zichtbare voorbeeldcode (`<pre>`) die onderdeel is van de uitleg op de webpagina zelf.

Visie uit `docs/index.md`: *"Deze skills laten een AI-agent controleren in plaats van instemmen. Ze gaan uit van nul vertrouwen en eisen bewijs in plaats van schijn... De rapportage is compact en eerlijk over wat niet is geverifieerd."*

## Starting point (audit findings)
- Verified: Reproductie (`⚙️ EXECUTED` op `https://trafilatura.readthedocs.io/en/latest/usage-python.html`) toonde dat het LXML-voorbeeld (`# define document and load it with LXML ... 'Here is the main text.'`) ontbrak in de output van `search_website`.
- Verified: Root cause in `mcp/web-search/server.py` (`⚙️ EXECUTED` inspectie van r. 899–958, blast radius: 2 functies `_extract_main_markdown` en `_clean_plain_text_body`):
  1. `_extract_main_markdown` gaf bij `include_code=False` `prune_xpath=["//pre", "//script", "//style", "//svg"]` mee aan `trafilatura.extract()`, waardoor alle `<pre>` blokken uit de DOM werden geknipt.
  2. `_clean_plain_text_body` voerde `re.sub(r"```[\s\S]*?```", "", working)` uit, waardoor de volledige inhoud tussen code-fences werd gewist i.p.v. alleen de fence-markering (` ``` `).
  3. Op kopregels stripte `re.sub(r"\s+[#¶]+\s*$", "", ...)` het Sphinx permalink-teken `#` niet wanneer het zonder spatie tegen het laatste woord aan plakte (`# Python usage#`).
- Verified: Volgens de W3C HTML5-specificatie voor `<pre>` (`https://w3c.github.io/html-reference/pre.html`, `🔎 SOURCED`) representeert `<pre>` *"a block of preformatted text"* dat tot de zichtbare documentinhoud behoort, in tegenstelling tot `<script>` en `<style>` (`https://dev.w3.org/html5/spec-LC/scripting-1.html`, `🔎 SOURCED`).
- Verified: Live test (`⚙️ EXECUTED`) op `https://trafilatura.readthedocs.io/en/latest/usage-python.html` met `prune_xpath=['//script', '//style', '//svg', '//noscript', '//iframe']` (zonder `//pre`) bewijst dat `HAS LXML BLOCK: True` (`13.652` tekens puur tekst inclusief alle 14 codevoorbeelden).

## Decisions (from the grill)
| Question | Decision | Reason |
| --- | --- | --- |
| Hoe wil je dat zichtbare codeblokken op een webpagina (zoals het LXML-voorbeeld op `trafilatura.readthedocs.io`) standaard in de output verschijnen? | Zichtbare `<pre>`/codeblokken van het artikel **altijd standaard meesturen als platte tekst** (zonder ```` ``` ```` Markdown-fences), en alleen onzichtbare website-code (`<script>`, `<style>`, `<svg>`, `<noscript>`, inline link-URLs, `**opmaak**` en trailing `#` op koppen) strippen | Behoudt 100% van de zichtbare uitleg en codevoorbeelden op een webpagina terwijl website- en Markdown-opmaakbloat verdwijnt |

## Scope
- In:
  - In `_extract_main_markdown()` (`mcp/web-search/server.py`): verwijder `//pre` uit `prune_xpath` en gebruik altijd `prune_xpath=["//script", "//style", "//svg", "//noscript", "//iframe"]`.
  - In `_clean_plain_text_body()` (`mcp/web-search/server.py`): verwijder bij `include_code=False` **nooit** de inhoud tussen ```` ```...``` ```` of `~~~...~~~`, maar strip alleen de fence-regels zelf (`^\s*(?:```|~~~)[^\n]*$`) en inline backtick-wrappers (`` `term` `` -> `term`). Bij `include_code=True` blijven ook de ```` ``` ```` fence-regels staan.
  - Vervang de trailing permalink-regex op koppen (`\s+[#¶]+\s*$`) door `\s*[#¶]+\s*$` zodat `# Python usage#` netjes `# Python usage` wordt.
  - Pas de unit tests in `mcp/web-search/tests/test_server.py` aan zodat gecontroleerd wordt dat zichtbare `<pre>` codeblokken (zoals `def big_block(): pass` en `# define document and load it with LXML`) én inline `<code>30.0</code>` **standaard aanwezig blijven als platte tekst** (zonder ```` ``` ```` fences bij `include_code=False`, en mét ```` ``` ```` fences bij `include_code=True`), terwijl `<script>`, `<style>`, `<svg>` en inline `[link](https://...)` URLs verdwijnen.
  - Synchroniseer naar `.gemini/antigravity-cli/mcp/web-search/` en `C:\Users\BramFransen\forensic-audit-skills\`.
- Out (explicitly not doing):
  - Geen zichtbare `<pre>` of `<code>` inhoud uit artikelpagina's verwijderen.

## Approach
1. **Bouw een gecomprimeerd Subagent Context Pack met `compress_context`** en laat de code-subagent `_extract_main_markdown`, `_clean_plain_text_body` en `tests/test_server.py` bijwerken + synchroniseren -> verify: `uv run --python 3.12 --directory mcp/web-search pytest tests/test_server.py -q`
2. **Verifieer live op `https://trafilatura.readthedocs.io/en/latest/usage-python.html`** dat `# define document and load it with LXML` t/m `'Here is the main text.'` volledig in de `search_website`-output zit en dat koppen geen plakkende `#` meer hebben -> verify: `uv run --python 3.12 --directory mcp/web-search python -c "from server import search_website; out=search_website('https://trafilatura.readthedocs.io/en/latest/usage-python.html'); assert 'define document and load it with LXML' in out and 'Here is the main text.' in out and '# Python usage#' not in out; print('LIVE CHECK OK')"`
3. **Zet `bugs/04` op `done`, werk `docs/index.md` bij en draai `docs_tool.py check`** -> verify: `python skills/docs-first-planner/scripts/docs_tool.py check`

## Acceptance criteria
- [x] Zichtbare `<pre>` en codeblok-inhoud (zoals `# define document and load it with LXML` en inline `<code>30.0</code>`) blijft standaard (`include_code=False`) 100% behouden als platte tekst zonder ```` ``` ```` fences, terwijl `<script>`, `<style>`, `<svg>` en inline link-URLs worden gestript.
  Check: `uv run --python 3.12 --directory mcp/web-search pytest tests/test_server.py -q` -> `19 passed`
- [x] Kopregels hebben geen achterblijvende Sphinx `#` of `¶` permalink-tekens meer (`# Python usage` i.p.v. `# Python usage#`).
  Check: `uv run --python 3.12 --directory mcp/web-search pytest tests/test_server.py -k "code_and_plain_text" -q` -> `1 passed`
- [x] De runtime-kopieën en mirror zijn gesynchroniseerd en `docs_tool.py check` geeft `docs OK`.
  Check: `python skills/docs-first-planner/scripts/docs_tool.py check` -> `docs OK`

## Risks and open points
- Geen: zichtbare voorbeeldcode op documentatiepagina's blijft nu altijd behouden als platte tekst, terwijl onzichtbare HTML/JS/CSS-code (`<script>`, `<style>`, `<svg>`) en Markdown-opmaakbloat wegblijven.

## Relations
- Corrigeert en verfijnt: `feature/07` (Tip 4: alleen onzichtbare website-code en Markdown-fences strippen, nooit zichtbare `<pre>` artikel-inhoud).

## Verification
| Criterion | How checked | Result |
| --- | --- | --- |
| Zichtbare `<pre>` voorbeeldcode + inline `<code>` blijft 100% behouden als platte tekst zonder ```` ``` ```` fences | `uv run --python 3.12 --directory mcp/web-search pytest tests/test_server.py -q` + live test op `usage-python.html` | `19 passed in 2.90s` + `LIVE TRAFILATURA PAGE CHECK OK`, voldaan |
| Sphinx permalink `#`/`¶` achter kopregels gestript (`# Python usage` i.p.v. `# Python usage#`) | `uv run --python 3.12 --directory mcp/web-search pytest tests/test_server.py -k "code_and_plain_text" -q` | `1 passed`, voldaan |
| Synchronisatie naar runtime & mirror + `docs_tool.py check` | `python skills/docs-first-planner/scripts/docs_tool.py check` | `docs OK`, voldaan |
