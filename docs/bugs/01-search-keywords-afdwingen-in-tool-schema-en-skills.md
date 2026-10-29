---
id: bugs/01
title: Search keywords worden overgeslagen na lange context of door ontbrekende tool-schema instructie
category: bugs
status: done
summary: Dwing ## Search keywords (incl. visie/schaal prio-termen) af in search_website.json, server.py docstring en SKILL.md en sync mappen.
tags: [planner, forensic-audit, search-keywords, web-search, mcp, tool-schema, sync, bugfix]
created: 2026-10-25
updated: 2026-10-27
related: [feature/04, feature/05, bugs/02, feature/06, feature/09]
---

# Search keywords worden overgeslagen na lange context of door ontbrekende tool-schema instructie

## Symptom, expected behaviour, how to reproduce
- **Symptom:** Tijdens het uitvoeren van `/docs-first-planner` op `D:\Github Projects\InfraDoc` (een project met een gevulde `## Search keywords`-sectie in `D:\Github Projects\InfraDoc\docs\index.md`) voerde de agent 5 zoekopdrachten uit via `web-search/search_website` zonder één enkel zoekwoord uit `## Search keywords` mee te sturen.
- **Expected behaviour:** Voorafgaand aan élke zoekactie met `search_website` controleert de agent of `./docs/index.md` een `## Search keywords`-sectie heeft en stuurt verplicht 1 tot 3 passende termen mee (`{gekozen keywords} {zoekvraag}`): bij architectuur-, UI-, canvas-, performance- en schaalvragen altijd 1–2 visie/schaal-priotermen (zoals de leidende eerste termen in de lijst, bijv. `MSP`, `multi-tenant`, `500+-nodes`), en bij specifieke protocol-, RFC- of standaardvragen 1–2 relevante technische domeintermen uit `## Search keywords` (zoals `DHCP-discovery`, `network-topology`). Een zoekopdracht zonder termen uit een aanwezige `## Search keywords` telt als `🚫 NOT SEARCHED` (procesfout).
- **How to reproduce:** Start een `/docs-first-planner`-sessie in een project met een groot aantal bestanden en docs-items (zoals `InfraDoc`), laat de agent ~100+ tool-calls doen tussen het lezen van `docs/index.md` en het uitvoeren van `search_website`, en observeer dat de agent vlak voor het zoeken `search_website.json` leest en kale queries verstuurt.
- **Root cause (verified):** Drievoudige oorzaak (`⚙️ EXECUTED` + `🔎 SOURCED`):
  1. **Geen instructie op de tool-call grens (`search_website.json` & `server.py`):** Vlak voor het aanroepen van een lazy-loaded MCP-tool leest de agent verplicht het schema `search_website.json` (in sessie `bd77e24e` op stap 518, na 118 tussenliggende stappen sinds het lezen van `docs/index.md` op stap 400). Dat schema bevatte alleen `"Search DuckDuckGo for a query, or fetch a webpage/PDF as Markdown for an http(s) URL."` zonder enige herinnering aan `./docs/index.md` of `## Search keywords` (*Lost in the Middle*, Liu et al., `https://arxiv.org/abs/2307.03172`, `🔎 SOURCED`).
  2. **Onduidelijk onderscheid tussen visie/schaal-termen en technische domeintermen in `SKILL.md`:** In `SKILL.md` stond de waarschuwing dat algemene termen specifieke RFC/API-zoekopdrachten kunnen vervuilen, zonder expliciet te maken dat de leidende visie/schaal-termen (de eerste termen in `## Search keywords`) wél standaard meesturen bij architectuur/UI/schaal-punten en dat bij pure protocol/RFC-lookups altijd 1–2 technische domeintermen uit `## Search keywords` gebruikt moeten worden (en dus nooit `0` termen).
  3. **Verouderde tweede installatiemap (`C:\Users\BramFransen\forensic-audit-skills`):** In `~/.gemini/config/mcp_config.json` verwijst `web-search` naar `C:\Users\BramFransen\forensic-audit-skills`, waar nog een verouderde kopie stond met slechts 2 van de 4 skills en `0` vermeldingen van `Search keywords`.

## Observed error
```text
● web-search/search_website({"query_or_url":"rfc 2131 dhcpdiscover dhcpoffer"})
  ⎿  # DuckDuckGo Search Results for: `rfc 2131 dhcpdiscover dhcpoffer`
● web-search/search_website({"query_or_url":"https://www.freesoft.org/CIE/RFC/2131/23.htm"})
  ⎿  # Source: https://www.freesoft.org/CIE/RFC/2131/23.htm
● web-search/search_website({"query_or_url":"locally administered mac address ieee 802"})
  ⎿  # DuckDuckGo Search Results for: `locally administered mac address ieee 802`
● web-search/search_website({"query_or_url":"https://www.ieee802.org/1/pages/802c.html"})
  ⎿  # Source: https://www.ieee802.org/1/pages/802c.html
● web-search/search_website({"query_or_url":"mdn stroke-dashoffset svg"})
  ⎿  # DuckDuckGo Search Results for: `mdn stroke-dashoffset svg`
● web-search/search_website({"query_or_url":"https://developer.mozilla.org/en-US/docs/Web/SVG/Reference/Attribute/stroke-dashoffset"})
  ⎿  # Source: https://developer.mozilla.org/en-US/docs/Web/SVG/Reference/Attribute/s...
● web-search/search_website({"query_or_url":"w3c wcag 2.3.3 animation from interactions"})
  ⎿  # DuckDuckGo Search Results for: `w3c wcag 2.3.3 animation from interactions`
● web-search/search_website({"query_or_url":"https://www.w3.org/WAI/WCAG21/Understanding/animation-from-interactions.html"})
  ⎿  # Source: https://www.w3.org/WAI/WCAG21/Understanding/animation-from-interaction...
● web-search/search_website({"query_or_url":"reactflow nodesdraggable false animated edges"})
  ⎿  # DuckDuckGo Search Results for: `reactflow nodesdraggable false animated edges`
● web-search/search_website({"query_or_url":"https://reactflow.dev/examples/edges/animating-edges"})
  ⎿  # Source: https://reactflow.dev/examples/edges/animating-edges
```

- **Discover:** Domein: AI Agent Skills, Model Context Protocol (MCP) tool-schema's en Information Retrieval / Controlled Vocabulary Query Expansion. Bestudeerde primaire normen en specificaties: MCP Specification (`https://modelcontextprotocol.io/specification/2025-06-18/server/tools`, `🔎 SOURCED`), FastMCP Tool Schema Docs (`https://gofastmcp.com/servers/tools`, `🔎 SOURCED`), ISO 25964-1:2011 + open primaire tegenhanger NISO ISO 25964 Schema (`https://www.niso.org/schemas/iso25964`, `🔎 SOURCED`), W3C SKOS Simple Knowledge Organization System Reference (`https://www.w3.org/TR/skos-reference/`, `🔎 SOURCED`), DuckDuckGo Search Syntax (`https://duckduckgo.com/duckduckgo-help-pages/results/syntax`, `🔎 SOURCED`), arXiv 2509.07794 Query Expansion Survey (`https://arxiv.org/html/2509.07794`, `🔎 SOURCED`), en arXiv 2307.03172 Lost in the Middle (`https://arxiv.org/abs/2307.03172`, `🔎 SOURCED`).
- **Quote:** `web-search/search_website({"query_or_url":"rfc 2131 dhcpdiscover dhcpoffer"})` ... `web-search/search_website({"query_or_url":"reactflow nodesdraggable false animated edges"})` (0 van de 5 queries bevatten een term uit `## Search keywords`).
- **Signal:** Stap 518 in transcript `bd77e24e`: de agent leest `search_website.json` vlak voor de eerste `call_mcp_tool`, nadat `docs/index.md` 118 stappen eerder (stap 400) was gelezen, en stuurt in stap 520 direct een kale query zonder keywords.
- **Guard:** De eis in `forensic-audit` en `docs-first-planner` om 1–3 passende termen uit `## Search keywords` te kiezen (en nooit de hele lijst van 50 woorden in één query te dumpen) is een bewuste kwaliteitsbewaking tegen query-drift. De fix versterkt deze guard door `0` gekozen termen bij een aanwezige `## Search keywords` expliciet als `🚫 NOT SEARCHED` te bestempelen en de instructie direct in `search_website.json` te plaatsen.
- **Hypotheses:**
  1. *H1 (Context-afstand & kaal MCP tool-schema):* Getest via transcript-inspectie (`bd77e24e`) en lezen van `search_website.json` (`⚙️ EXECUTED`) -> **Bevestigd** (118 stappen tussen `index.md` en `search_website`, en `search_website.json` vermeldde `## Search keywords` niet).
  2. *H2 (Onvoorwaardelijk meesturen van ruwe prio-termen zoals `MSP 500+-nodes` bij elke RFC-query):* Getest via live `search_website` (`⚙️ EXECUTED`) -> **Weerlegd voor pure protocol-queries, bevestigd voor architectuur/UI/schaal-queries**: bij `rfc 2131` veroorzaakt `MSP multi-tenant 500+-nodes` Microsoft 365 SEO-ruis terwijl `DHCP-discovery network-topology rfc 2131` zuivere RFC-treffers geeft; bij `reactflow animated edges` levert `500 nodes` juist wél de cruciale `reactflow.dev/learn/advanced-use/performance` bron op.
  3. *H3 (Verouderde installatiemappen):* Getest via bestandsvergelijking (`⚙️ EXECUTED`) -> **Bevestigd**: `C:\Users\BramFransen\forensic-audit-skills` miste `feature/04` volledig.
- **Fix:** (1) Zet de verplichte `## Search keywords`-check en het onderscheid tussen visie/schaal-priotermen en technische domeintermen rechtstreeks in de tool- en parameterbeschrijving van `mcp/web-search/server.py`, `C:\Users\BramFransen\.gemini\antigravity-cli\mcp\web-search\search_website.json` en `C:\Users\BramFransen\.gemini\antigravity-ide\mcp\web-search\search_website.json`; (2) scherp alle 4 de `SKILL.md`-bestanden, `references/audit-brief.md`, `references/plan-template.md`, `GEMINI.md`, `CLAUDE.md` en `.cursor/rules/forensic-audit.mdc` aan zodat de eerste termen in `## Search keywords` als leidende visie/schaal-priotermen gelden voor architectuur/UI/performance-vragen, technische domeintermen voor protocol/RFC-vragen, en `0` gekozen termen bij een aanwezige `## Search keywords` als `🚫 NOT SEARCHED` telt; (3) synchroniseer zowel `C:\Users\BramFransen\.gemini\config\skills` als `C:\Users\BramFransen\forensic-audit-skills`.
- **Confirm:** Verifieer met `Check:`-commando's dat alle 3 de MCP-bestanden (`server.py` + 2x `search_website.json`) en alle 9 skill-/regelbestanden de aangescherpte instructie bevatten en dat beide lokale installatiemappen (`~/.gemini/config/skills` én `C:\Users\BramFransen\forensic-audit-skills`) 0 byte-verschillen hebben met de repo.

## Starting point (audit findings)
- Verified: `D:\Github Projects\InfraDoc\docs\index.md` (r. 8–9, `⚙️ EXECUTED`) bevat een geldige `## Search keywords` met 57 termen waaronder `MSP, managed-service-provider, multi-tenant, 100+-tenants, 500+-devices-per-tenant, 500+-nodes`.
- Verified: In transcript `bd77e24e` (`⚙️ EXECUTED`) las de agent `InfraDoc/docs/index.md` in stap 400, voerde daarna 117 stappen code- en repo-inspectie uit, las in stap 518 `C:\Users\BramFransen\.gemini\antigravity-cli\mcp\web-search\search_website.json`, en riep in stappen 520–540 `search_website` aan zonder keywords.
- Verified: `search_website.json` (in zowel `antigravity-cli` als `antigravity-ide`) en `mcp/web-search/server.py` (r. 451–452) bevatten `0` verwijzingen naar `./docs/index.md` of `## Search keywords` (`⚙️ EXECUTED`).
- Verified: Live zoekproeven met `search_website` (`⚙️ EXECUTED` + `🔎 SOURCED` op `https://reactflow.dev/learn/advanced-use/performance`, `https://www.niso.org/schemas/iso25964` en `https://arxiv.org/html/2509.07794`) tonen aan dat visie/schaal-termen (`500 nodes`, `MSP`, `multi-tenant`) essentieel zijn bij architectuur-, UI- en performance-zoekopdrachten, terwijl technische domeintermen (`DHCP-discovery`, `network-topology`) essentieel zijn bij RFC/protocol-zoekopdrachten, en dat tekens zoals `+` in `500+-nodes` in de zoekopdracht als normale woorden (`500 nodes`) moeten worden meegestuurd i.v.m. DuckDuckGo-operatoren (`https://duckduckgo.com/duckduckgo-help-pages/results/syntax`, `🔎 SOURCED`).
- Verified: `C:\Users\BramFransen\forensic-audit-skills` (waarnaar `~/.gemini/config/mcp_config.json` verwijst) liep achter op `D:\Github Projects\forensic-audit-skills` (`⚙️ EXECUTED`).
- Corrected: Eerdere aanname uit `feature/04` dat een instructie alleen in `SKILL.md` voldoende is wanneer de agent een lazy-loaded MCP-tool pas na >100 tussenstappen aanroept.
- Unverified: Geen bron-gaps (`0` punten met `⚠️` of `🚫`).

## Decisions (from the grill)
| Question | Decision | Reason |
| --- | --- | --- |
| Hoe lossen we het overslaan van `## Search keywords` en de wens voor `prio_key_search` op? | Alleen de tekst in `SKILL.md` (en bijbehorende referenties/regels) en `search_website.json` (+ `server.py` docstring) aanscherpen en de lokale mappen synchroniseren, zonder extra parameter/validatie in `server.py` en zonder het `[term1, term2, ...]` formaat in `index.md` te splitsen | Houdt de MCP-tool en `index.md` eenvoudig en backward-compatible, terwijl de agent zowel in de skill als exact op het moment van de tool-call (`search_website.json`) wordt herinnerd aan de verplichte project- en prio-keywords |

## Scope
- In:
  - Aanscherpen van de tool- en parameterbeschrijving in `mcp/web-search/server.py` (docstring + Pydantic `Field`), `C:\Users\BramFransen\.gemini\antigravity-cli\mcp\web-search\search_website.json` en `C:\Users\BramFransen\.gemini\antigravity-ide\mcp\web-search\search_website.json` zodat de agent vlak voor elke `search_website`-aanroep verplicht `./docs/index.md` (`## Search keywords`) controleert en 1–3 passende termen meestuurt.
  - Aanscherpen van `skills/docs-first-planner/SKILL.md`, `skills/docs-first-planner/references/audit-brief.md`, `skills/docs-first-planner/references/plan-template.md`, `skills/forensic-audit/SKILL.md`, `skills/forensic-security-audit/SKILL.md`, `skills/forensic-site-audit/SKILL.md`, `GEMINI.md`, `CLAUDE.md`, `.cursor/rules/forensic-audit.mdc` en `README.md`:
    1. De eerste ~5–8 termen in `## Search keywords` staan voor de kernvisie en schaal van het project (prio-termen, zoals `MSP, multi-tenant, 500+-nodes` in InfraDoc).
    2. Bij architectuur-, ontwerp-, UI/canvas-, performance- en schaalpunten stuurt de agent altijd 1–2 van deze visie/schaal-priotermen mee; bij diepe protocol-, RFC-, W3C- of API-spec-punten stuurt de agent 1–2 passende technische domeintermen uit `## Search keywords` mee (en verwijdert zoek-operatortekens zoals `+` uit een term wanneer die de zoekmachine verstoren, bijv. `500 nodes` i.p.v. `500+-nodes`).
    3. Wanneer `./docs/index.md` met `## Search keywords` aanwezig is, is `0` meegestuurde project-keywords verboden en telt die zoekopdracht als `🚫 NOT SEARCHED` (procesfout).
  - Volledige synchronisatie van alle skills en gewijzigde bestanden naar zowel `C:\Users\BramFransen\.gemini\config\skills` als `C:\Users\BramFransen\forensic-audit-skills`.
- Out (explicitly not doing):
  - Geen nieuwe verplichte parameters of runtime-blokkades in de Python-code van `mcp/web-search/server.py`.
  - Geen wijziging aan het platte `[term1, term2, ...]` formaat van `## Search keywords` in `./docs/index.md` of `D:\Github Projects\InfraDoc\docs\index.md`.
  - Geen IT- of MSP-specifieke woorden hardcoden in de universele skill-instructies.

## Approach
1. Werk de docstring en `Field`-beschrijving van `search_website` in `mcp/web-search/server.py` én de JSON-schema's in `C:\Users\BramFransen\.gemini\antigravity-cli\mcp\web-search\search_website.json` en `C:\Users\BramFransen\.gemini\antigravity-ide\mcp\web-search\search_website.json` bij met de verplichte `./docs/index.md` (`## Search keywords`) regel -> verify: `(Select-String "mcp/web-search/server.py","C:\Users\BramFransen\.gemini\antigravity-cli\mcp\web-search\search_website.json","C:\Users\BramFransen\.gemini\antigravity-ide\mcp\web-search\search_website.json" -Pattern "Search keywords" -List | Measure-Object).Count`
2. Scherp de `## Search keywords`-instructie aan in `skills/docs-first-planner/SKILL.md`, `skills/docs-first-planner/references/audit-brief.md`, `skills/docs-first-planner/references/plan-template.md`, `skills/forensic-audit/SKILL.md`, `skills/forensic-security-audit/SKILL.md`, `skills/forensic-site-audit/SKILL.md`, `GEMINI.md`, `CLAUDE.md`, `.cursor/rules/forensic-audit.mdc` en `README.md` (leidende visie/schaal-priotermen voorop in `## Search keywords`, 1–2 visie/schaaltermen bij architectuur/UI/schaal vs. 1–2 technische domeintermen bij protocol/RFC, en `0` keywords = `🚫 NOT SEARCHED`) -> verify: `(Select-String skills/*/SKILL.md,skills/docs-first-planner/references/audit-brief.md -Pattern "NOT SEARCHED" -List | Measure-Object).Count`
3. Synchroniseer alle 8 skill-bestanden naar `C:\Users\BramFransen\.gemini\config\skills` én synchroniseer de volledige repo (`skills/`, `mcp/web-search/`, `CLAUDE.md`, `GEMINI.md`, `.cursor/rules/forensic-audit.mdc`, `README.md`, `EXAMPLES.md`) naar `C:\Users\BramFransen\forensic-audit-skills` -> verify: Python byte-vergelijking op beide doelmappen geeft `0` verschillen.
4. Voer de pytest-suite van `mcp/web-search` en `docs_tool.py check` uit -> verify: `py skills/docs-first-planner/scripts/docs_tool.py check`

## Acceptance criteria
- [x] `mcp/web-search/server.py` en beide `search_website.json` tool-schema's (`antigravity-cli` en `antigravity-ide`) bevatten in hun tool-/parameterbeschrijving de verplichte check op `./docs/index.md` en `## Search keywords` (1–3 passende termen per zoekopdracht).
  Check: `(Select-String "mcp/web-search/server.py","C:\Users\BramFransen\.gemini\antigravity-cli\mcp\web-search\search_website.json","C:\Users\BramFransen\.gemini\antigravity-ide\mcp\web-search\search_website.json" -Pattern "Search keywords" -List | Measure-Object).Count` -> `3`
- [x] Alle 4 de skills (`skills/*/SKILL.md`), `references/audit-brief.md`, `references/plan-template.md`, `GEMINI.md`, `CLAUDE.md` en `.cursor/rules/forensic-audit.mdc` leggen vast dat de leidende visie/schaal-termen vooraan in `## Search keywords` staan (voor architectuur/UI/schaal-vragen), technische domeintermen voor protocol/spec-vragen worden gekozen, en een zoekopdracht zonder termen uit een aanwezige `## Search keywords` als `🚫 NOT SEARCHED` telt.
  Check: `(Select-String skills/*/SKILL.md,skills/docs-first-planner/references/audit-brief.md,skills/docs-first-planner/references/plan-template.md,GEMINI.md,CLAUDE.md,.cursor/rules/forensic-audit.mdc -Pattern "Search keywords" -List | Measure-Object).Count` -> `9`
- [x] Alle 8 bestanden in `skills/` zijn byte-voor-byte identiek tussen deze repo en `C:\Users\BramFransen\.gemini\config\skills`.
  Check: `py -c "import pathlib; loc=pathlib.Path(r'C:\Users\BramFransen\.gemini\config\skills'); rep=pathlib.Path(r'D:\Github Projects\forensic-audit-skills\skills'); print(sum((loc/p.relative_to(rep)).read_bytes()!=p.read_bytes() for p in rep.rglob('*') if p.is_file()))"` -> `0`
- [x] Alle kernbestanden (`skills/`, `mcp/web-search/server.py`, `CLAUDE.md`, `GEMINI.md`, `.cursor/rules/forensic-audit.mdc`, `README.md`) in `C:\Users\BramFransen\forensic-audit-skills` zijn byte-voor-byte identiek aan `D:\Github Projects\forensic-audit-skills`.
  Check: `py -c "import pathlib; a=pathlib.Path(r'C:\Users\BramFransen\forensic-audit-skills'); b=pathlib.Path(r'D:\Github Projects\forensic-audit-skills'); files=['CLAUDE.md','GEMINI.md','README.md','.cursor/rules/forensic-audit.mdc','mcp/web-search/server.py']+[p.relative_to(b).as_posix() for p in (b/'skills').rglob('*') if p.is_file()]; print(sum(not (a/f).exists() or (a/f).read_bytes()!=(b/f).read_bytes() for f in files))"` -> `0`
- [x] `docs_tool.py check` geeft `docs OK` en alle regressiechecks van `feature/01` t/m `feature/04` slagen.
  Check: `python skills/docs-first-planner/scripts/docs_tool.py check` -> `docs OK`

## Risks and open points
- Wanneer Antigravity bij een grote update de gecachete MCP-schema's in `.gemini/antigravity-cli/mcp/web-search/search_website.json` opnieuw genereert vanuit `server.py`, zorgt de bijgewerkte docstring en Pydantic `Field(description=...)` in `server.py` ervoor dat de instructie ook na regeneratie behouden blijft.

## Relations
- Verbetert en borgt: `feature/04`.

## Verification
| Criterion | How checked | Result |
| --- | --- | --- |
| `Search keywords` in `server.py` + 2x `search_website.json` (`antigravity-cli` & `antigravity-ide`) | `Check:` uitgevoerd (`Select-String`) + `pytest mcp/web-search/tests/test_server.py` | `3`, en `10 passed` in pytest, voldaan |
| `Search keywords` (incl. visie/schaal prio-termen + `🚫 NOT SEARCHED` bij 0 keywords) in 9 skill-/regelbestanden | `Check:` uitgevoerd (`Select-String`) | `9`, voldaan |
| 100% byte-identieke sync naar `C:\Users\BramFransen\.gemini\config\skills` | `Check:` uitgevoerd (Python byte-vergelijking over alle 8 bestanden) | `0` verschillen, voldaan |
| 100% byte-identieke sync naar `C:\Users\BramFransen\forensic-audit-skills` | `Check:` uitgevoerd (Python byte-vergelijking over alle 13 kernbestanden) | `0` verschillen, voldaan |
| `docs_tool.py check` en regressiechecks op `feature/01` t/m `feature/04` | `docs_tool.py index --strict`, `docs_tool.py check` en alle `Check:`-regels van `feature/01` t/m `feature/04` uitgevoerd | `docs OK`, alle checks geslaagd |
| Regressiecheck (2026-10-27): `Search keywords` in 9 skill-/regelbestanden | `(Select-String skills/*/SKILL.md,skills/docs-first-planner/references/audit-brief.md,skills/docs-first-planner/references/plan-template.md,GEMINI.md,CLAUDE.md,.cursor/rules/forensic-audit.mdc -Pattern "Search keywords" -List \| Measure-Object).Count` | Hersteld via `feature/06` (`bugs/02`): output opnieuw `9`, en `0` byte-verschillen op alle sync-mappen, voldaan |
