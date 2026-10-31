---
id: bugs/05
title: Pydantic ValidationError bij search_website({"query": ...}) en consolidatie van MCP-paden op D:\Github Projects
category: bugs
status: done
summary: Voeg AliasChoices toe aan search_website en compress_context, maak query_or_url expliciet in skills en verwijs mcp_config.json naar D:\Github Projects.
tags: [mcp, web-search, context-compressor, pydantic, aliaschoices, tool-schema, query-or-url, mcp-config, bugfix]
created: 2026-10-30
updated: 2026-10-30
related: [bugs/01, feature/05, feature/06, feature/09, feature/10, feature/11]
---

# Pydantic ValidationError bij search_website({"query": ...}) en consolidatie van MCP-paden op D:\Github Projects

## Symptom, expected behaviour, how to reproduce
- **Symptom:** Tijdens het uitvoeren van `/docs-first-planner` riep een AI-agent `web-search/search_website({"query":"bento-grid-ui dark-mode-ui site:nngroup.com skeleton screens perceived performance"})` aan. De FastMCP-laag weigerde de aanroep met een Pydantic V2 `ValidationError` (`query_or_url: Missing required argument`, `query: Unexpected keyword argument`). Daarnaast wezen de MCP-serverpaden in `~/.gemini/config/mcp_config.json` en een aantal `Check:`-regels in `./docs` naar een verwijderde map `C:\Users\BramFransen\forensic-audit-skills`.
- **Expected behaviour:**
  1. De skill-, regel- en tool-beschrijvingen noemen bij elk zoekvoorbeeld expliciet de parameternaam `query_or_url="..."` (en `file_path="..."` bij `compress_context`), zodat de agent standaard de canonieke sleutel stuurt.
  2. Wanneer een agent uit gewoonte tóch `{"query": "..."}`, `{"url": "..."}` of `{"q": "..."}` (of `{"filter": "..."}` / `{"keywords": "..."}` bij `search_website`, en `{"path": "..."}` / `{"file": "..."}` of `{"root": "..."}` bij `compress_context`) stuurt, accepteert FastMCP dit transparant via `Field(validation_alias=AliasChoices(...))` zonder dat het gepubliceerde JSON-schema groter wordt en terwijl `extra="forbid"` voor onbekende parameters intact blijft.
  3. `~/.gemini/config/mcp_config.json` en de `Check:`-regels in `./docs` verwijzen uitsluitend naar `D:\Github Projects\forensic-audit-skills` en `~/.gemini/config/skills` (geen tweede kopie op `C:\Users\BramFransen\forensic-audit-skills` meer).
- **How to reproduce:** Roep via `fastmcp.Client(server.mcp)` `await client.call_tool("search_website", {"query": "test"})` aan en observeer `ToolError: 2 validation errors for call[search_website]`.
- **Root cause (verified):** Drievoudige oorzaak (`⚙️ EXECUTED` + `🔎 SOURCED`):
  1. **Geen `validation_alias=AliasChoices(...)` op de `@mcp.tool`-functiesignatuur (`mcp/web-search/server.py:1389` en `mcp/context-compressor/server.py:739`):** FastMCP (v4.1.x) valideert de inkomende JSON-argumenten via een Pydantic `TypeAdapter` rechtstreeks tegen de functieparameters van `@mcp.tool` vóórdat de functie-body (`SearchWebsiteInput` / `CompressContextInput`) wordt bereikt (`https://gofastmcp.com/servers/tools`, `🔎 SOURCED`). Omdat `query_or_url` geen `AliasChoices` had, leverde `{"query": "..."}` direct twee validatiefouten op.
  2. **Impliciete parameternaam in `SKILL.md` en `audit-brief.md`:** In `skills/forensic-audit/SKILL.md:61`, `skills/docs-first-planner/SKILL.md:62` en `skills/docs-first-planner/references/audit-brief.md:19` stonden alleen positionele voorbeelden (`search_website("<query>")` en `search_website("https://...")`) zonder de sleutelnaam `query_or_url=` te noemen (*Anthropic: Writing effective tools for AI agents*, `https://www.anthropic.com/engineering/writing-tools-for-agents`, `🔎 SOURCED`).
  3. **Verwijderde tweede map `C:\Users\BramFransen\forensic-audit-skills` in `~/.gemini/config/mcp_config.json`:** `mcp_config.json` r. 6–20 verwees naar `C:\Users\BramFransen\forensic-audit-skills\mcp\...`, terwijl die map op schijf niet meer bestaat (`exists: False`), waardoor de MCP-servers bij het opstarten faalden en 4 `Check:`-regels in `bugs/01`, `feature/05`, `feature/09` en `feature/11` braken.

## Observed error
```text
● web-search/search_website({"query":"bento-grid-ui dark-mode-ui site:nngroup.com skeleton screens perceived performance"})
  ⎿  Error: 2 validation errors for call[search_website]
     query_or_url
       Missing required argument [type=missing_argument, input_value={'query': 'bento-grid-ui ... perceived performance'}, input_type=dict]
         For further information visit https://errors.pydantic.dev/2.14/v/missing_argument
     query
       Unexpected keyword argument [type=unexpected_keyword_argument, input_value='bento-grid-ui dark-mode-...s perceived performance', input_type=str]
         For further information visit https://errors.pydantic.dev/2.14/v/unexpected_keyword_argument
```

- **Discover:** Domein: Model Context Protocol (MCP) tool-schema's, FastMCP Python parameter-validatie, Pydantic V2 `AliasChoices` en AI-agent tool-ergonomie. Bestudeerde primaire bronnen: MCP Specification 2025-06-18 Server Tools (`https://modelcontextprotocol.io/specification/2025-06-18/server/tools`, `🔎 SOURCED`), FastMCP Tools Documentation (`https://gofastmcp.com/servers/tools`, `🔎 SOURCED`), Pydantic V2 Field & Alias Documentation (`https://docs.pydantic.dev/latest/concepts/fields/` en `https://docs.pydantic.dev/latest/concepts/alias/`, `🔎 SOURCED`), Anthropic Engineering *Writing effective tools for AI agents* (`https://www.anthropic.com/engineering/writing-tools-for-agents`, `🔎 SOURCED`), JSON Schema Reference (`https://json-schema.org/understanding-json-schema/reference/object`, `🔎 SOURCED`), IETF RFC 9413 *Maintaining Robust Protocols* (`https://datatracker.ietf.org/doc/html/rfc9413`, `🔎 SOURCED`), OWASP Top 10 for LLM Applications `LLM06:2025 Excessive Agency` (`https://genai.owasp.org/llmrisk/llm062025-excessive-agency/`, `🔎 SOURCED`) en Gemini CLI MCP Server Docs (`https://google-gemini.github.io/gemini-cli/docs/tools/mcp-server.html`, `🔎 SOURCED`).
- **Quote:** `2 validation errors for call[search_website] — query_or_url: Missing required argument [type=missing_argument, ...] — query: Unexpected keyword argument [type=unexpected_keyword_argument, ...]`.
- **Signal:** De `call[search_website]` Pydantic `TypeAdapter`-validatie in FastMCP (`server.py:1389`), vóórdat `SearchWebsiteInput` op r. 1434 wordt aangeroepen.
- **Guard:** Strikt schema-toezicht (`additionalProperties: false` en `ConfigDict(extra="forbid", str_strip_whitespace=True)` plus niet-lege string-validatie) is een bewuste fail-closed guard tegen willekeurige of lege parameters (`OWASP LLM06:2025`). De fix behoudt deze guard volledig en staat alleen expliciet gedefinieerde synoniemen toe via `AliasChoices`.
- **Hypotheses:**
  1. *H1 (FastMCP TypeAdapter weigert `{"query": "..."}` vóór `SearchWebsiteInput`):* Getest via `fastmcp.Client(server.mcp)` (`⚙️ EXECUTED`) -> **Bevestigd** (exact dezelfde `ToolError` gereproduceerd).
  2. *H2 (`Field(validation_alias=AliasChoices(...))` op `@mcp.tool` lost de fout op zonder het JSON-schema te vergroten):* Getest via in-memory FastMCP `Client`-probe (`⚙️ EXECUTED`) -> **Bevestigd**: `inputSchema` blijft 100% identiek (`required: ["query_or_url"]`, `additionalProperties: false`), `{"query": "..."}` en `{"url": "..."}` slagen, en `{"bogus": "x"}` faalt nog steeds met `unexpected_keyword_argument`.
  3. *H3 (`mcp_config.json` verwijst naar een verwijderde map `C:\Users\BramFransen\forensic-audit-skills`):* Getest via `pathlib.Path(r'C:\Users\BramFransen\forensic-audit-skills').exists()` (`⚙️ EXECUTED`) -> **Bevestigd** (`False`).
- **Fix:** (1) Voeg `validation_alias=AliasChoices(...)` toe aan `mcp/web-search/server.py` (`query_or_url` -> `'query_or_url', 'query', 'url', 'q'`; `filter_query` -> `'filter_query', 'filter', 'keywords'`) en aan `mcp/context-compressor/server.py` (`file_path` -> `'file_path', 'path', 'file', 'filepath'`; `workspace_root` -> `'workspace_root', 'root', 'cwd'`); (2) maak `query_or_url="..."` expliciet in de skills, referenties, regelbestanden en tool-schema's; (3) zet de paden in `~/.gemini/config/mcp_config.json` en de `Check:`-regels in `bugs/01`, `feature/05`, `feature/09` en `feature/11` om naar `D:\Github Projects\forensic-audit-skills` en synchroniseer `~/.gemini/config/skills` en `~/.gemini/antigravity-*/mcp/`.
- **Confirm:** Bewijs met unit- en opposite-tests via `fastmcp.Client` in beide pytest-suites dat zowel de canonieke namen als de aliassen slagen, dat een onbekende parameter (`{"bogus": "x"}`) en een lege string (`{"query": "   "}`) nog steeds falen, dat de `inputSchema` ongewijzigd is, en dat alle `Check:`-regels en `docs_tool.py check` slagen.

## Starting point (audit findings)
- Verified: `mcp/web-search/server.py:145-188` en `1388-1448` (`⚙️ EXECUTED`) gebruiken `query_or_url: Annotated[str, Field(...)]` zonder `validation_alias`. FastMCP valideert op de functiesignatuur (`call[search_website]`) vóórdat `SearchWebsiteInput` wordt aangeroepen (`🔎 SOURCED`: `https://gofastmcp.com/servers/tools`).
- Verified: `mcp/context-compressor/server.py:32-69` en `738-785` (`⚙️ EXECUTED`) hebben exact dezelfde structuur voor `file_path` en `workspace_root` zonder `validation_alias`.
- Verified: In-memory `fastmcp.Client`-test (`⚙️ EXECUTED`) bewijst dat `Field(validation_alias=AliasChoices(...))` op `@mcp.tool`-parameters in FastMCP 4.1.x de aliassen accepteert, onbekende parameters (`{"bogus": "x"}`) blokkeert, en het gegenereerde JSON-schema (`inputSchema`) byte-voor-byte gelijk houdt (`🔎 SOURCED`: `https://docs.pydantic.dev/latest/concepts/alias/`).
- Verified: In `skills/forensic-audit/SKILL.md:61`, `skills/docs-first-planner/SKILL.md:62` en `skills/docs-first-planner/references/audit-brief.md:19` (`⚙️ EXECUTED`) stond `search_website("<query>")` zonder de parameternaam `query_or_url=` expliciet te noemen.
- Verified: `C:\Users\BramFransen\.gemini\config\mcp_config.json:6-20` (`⚙️ EXECUTED`) verwees naar `C:\Users\BramFransen\forensic-audit-skills\mcp\...`, terwijl die map niet meer bestaat (`exists: False`).
- Corrected: De eerdere afspraak uit `bugs/01`, `feature/05`, `feature/09` en `feature/11` om een tweede volledige repo-kopie op `C:\Users\BramFransen\forensic-audit-skills` bij te houden vervalt; `D:\Github Projects\forensic-audit-skills` is voortaan de enige repo-locatie voor `mcp_config.json`.
- Unverified: none (alle 10 auditpunten en alle antwoorden uit fase 3.5 zijn met `🔎 SOURCED` + `⚙️ EXECUTED` geverifieerd; `0` bron-gaps).

## Decisions (from the grill)
| Question | Decision | Reason |
| --- | --- | --- |
| Hoe voorkomen we dat een AI-agent bij `search_website` crasht op `{"query": "..."}` i.p.v. `{"query_or_url": "..."}`? | Beide doen: `AliasChoices` in `server.py` + expliciete `query_or_url=` naamgeving in alle skills, regels en tool-descriptions | Voorkomt de fout bij de bron (prompt/schema) én vangt afwijkende modellen aan de achterkant foutloos op met behoud van `extra="forbid"` |
| Moeten we ditzelfde patroon ook meteen projectbreed dichttimmeren voor `compress_context`? | Ja, neem ook `mcp/context-compressor/server.py` mee (`path`/`file`/`filepath` -> `file_path`, `root`/`cwd` -> `workspace_root`) met een ongewijzigd JSON-schema | Sluit dezelfde klasse `ValidationError` projectbreed uit voor beide MCP-servers zonder extra schema-tokens |
| Hoe lossen we het ontbreken van `C:\Users\BramFransen\forensic-audit-skills` (waarnaar `mcp_config.json` en 4 `Check:`-regels verwijzen) op? | Pas `~/.gemini/config/mcp_config.json` en de `Check:`-regels in `./docs` aan zodat alles rechtstreeks naar `D:\Github Projects\forensic-audit-skills` wijst (geen tweede kopie op `C:\` meer) | Eén single source of truth op `D:\Github Projects\forensic-audit-skills`; voorkomt synchronisatie-drift en dubbele mappen |

## Scope
- In:
  1. **`AliasChoices` in `mcp/web-search/server.py` + tests in `mcp/web-search/tests/test_server.py`**:
     - Voeg `AliasChoices` (uit `pydantic`) toe aan zowel `SearchWebsiteInput` als de `@mcp.tool(output_schema=None)` signatuur van `search_website`:
       - `query_or_url`: `validation_alias=AliasChoices("query_or_url", "query", "url", "q")`
       - `filter_query`: `validation_alias=AliasChoices("filter_query", "filter", "keywords")`
     - Voeg in `mcp/web-search/tests/test_server.py` een async `fastmcp.Client`-test toe die bewijst dat (a) `{"query": "..."}`, `{"url": "..."}`, `{"q": "..."}` en `{"filter": "..."}` slagen, (b) `inputSchema` exact `required: ["query_or_url"]` en `additionalProperties: false` behoudt zonder extra properties, en (c) opposite tests voor `{"bogus": "x"}` en `{"query": "   "}` falen met een `ToolError`.
  2. **`AliasChoices` in `mcp/context-compressor/server.py` (`+ MODULE.md`) + tests in `mcp/context-compressor/tests/test_server.py`**:
     - Voeg `AliasChoices` toe aan zowel `CompressContextInput` als de `@mcp.tool(output_schema=None)` signatuur van `compress_context`:
       - `file_path`: `validation_alias=AliasChoices("file_path", "path", "file", "filepath")`
       - `workspace_root`: `validation_alias=AliasChoices("workspace_root", "root", "cwd")`
     - Werk `mcp/context-compressor/MODULE.md` bij en voeg in `mcp/context-compressor/tests/test_server.py` een async `fastmcp.Client`-test + opposite test (`{"bogus": "x"}`) toe.
  3. **Expliciete `query_or_url=` naamgeving in tool-schema's, skills en regels**:
     - Vermeld in de `description` van `search_website` (`mcp/web-search/server.py`, `C:\Users\BramFransen\.gemini\antigravity-cli\mcp\web-search\search_website.json` en `C:\Users\BramFransen\.gemini\antigravity-ide\mcp\web-search\search_website.json`) en in `skills/docs-first-planner/SKILL.md`, `skills/docs-first-planner/references/audit-brief.md`, `skills/forensic-audit/SKILL.md`, `skills/forensic-security-audit/SKILL.md`, `skills/forensic-site-audit/SKILL.md`, `GEMINI.md`, `CLAUDE.md` en `.cursor/rules/forensic-audit.mdc` expliciet `search_website(query_or_url="...")`.
  4. **Consolidatie van MCP-paden naar `D:\Github Projects\forensic-audit-skills`**:
     - Werk `C:\Users\BramFransen\.gemini\config\mcp_config.json` bij zodat `web-search` en `context-compressor` direct starten vanuit `D:\Github Projects\forensic-audit-skills\mcp\...`.
     - Werk de `Check:`-regels in `docs/bugs/01-*.md`, `docs/feature/05-*.md`, `docs/feature/09-*.md` en `docs/feature/11-*.md` bij zodat ze de synchronisatie met `C:\Users\BramFransen\.gemini\config\skills` en `.gemini\antigravity-*\mcp\` controleren i.p.v. de verwijderde map `C:\Users\BramFransen\forensic-audit-skills`, en zet de 4 items weer op `done`.
     - Synchroniseer alle 8 skill-bestanden naar `C:\Users\BramFransen\.gemini\config\skills` en de MCP-bestanden/schema's naar `C:\Users\BramFransen\.gemini\antigravity-cli\mcp\` en `C:\Users\BramFransen\.gemini\antigravity-ide\mcp\`.
- Out (explicitly not doing):
  - Geen herbouw van de verwijderde map `C:\Users\BramFransen\forensic-audit-skills`.
  - Geen loslaten van `extra="forbid"` / `additionalProperties: false`.
  - Geen extra properties in het gepubliceerde JSON-schema van `search_website` of `compress_context`.

## Approach
Code-stappen worden uitgevoerd door een schone code-subagent met een lossless `compress_context` Subagent Context Pack (`mcp/context-compressor`).
1. **Delegeer de code- en testwijzigingen in `mcp/web-search/` en `mcp/context-compressor/` aan een schone code-subagent** (`AliasChoices` op `SearchWebsiteInput`/`search_website` en `CompressContextInput`/`compress_context` + `fastmcp.Client` unit- en opposite-tests in beide testsuites + update van `mcp/context-compressor/MODULE.md`) -> verify: `uv run --directory mcp/web-search pytest tests/test_server.py -q` en `uv run --directory mcp/context-compressor pytest tests/test_server.py -q`
2. **Werk de skill-, referentie- en regelbestanden (`skills/*/SKILL.md`, `skills/docs-first-planner/references/audit-brief.md`, `GEMINI.md`, `CLAUDE.md`, `.cursor/rules/forensic-audit.mdc`) en beide `search_website.json` / `compress_context.json` schema's bij** met expliciete `query_or_url=` voorbeelden, en synchroniseer naar `C:\Users\BramFransen\.gemini\config\skills` en `C:\Users\BramFransen\.gemini\antigravity-*\mcp\` -> verify: `(Select-String skills/*/SKILL.md,skills/docs-first-planner/references/audit-brief.md,GEMINI.md,CLAUDE.md,.cursor/rules/forensic-audit.mdc -Pattern "query_or_url" -List | Measure-Object).Count`
3. **Werk `C:\Users\BramFransen\.gemini\config\mcp_config.json` en de `Check:`-regels van `bugs/01`, `feature/05`, `feature/09` en `feature/11` bij** zodat alles naar `D:\Github Projects\forensic-audit-skills` en `.gemini` wijst, draai alle regressiechecks, zet `bugs/01`, `feature/05`, `feature/09`, `feature/11` en `bugs/05` op `done`, en regenereer de index -> verify: `python skills/docs-first-planner/scripts/docs_tool.py check`

## Acceptance criteria
- [x] `mcp/web-search/server.py` en `mcp/context-compressor/server.py` gebruiken `validation_alias=AliasChoices(...)` op zowel hun Pydantic input-model als hun `@mcp.tool(output_schema=None)` functiesignatuur.
  Check: `(Select-String mcp/*/server.py -Pattern "AliasChoices" | Measure-Object).Count` -> `10`
- [x] Alle unit- en opposite-tests in `mcp/web-search/tests/test_server.py` (inclusief `fastmcp.Client`-test voor `{"query": "..."}`, `{"url": "..."}`, ongewijzigd JSON-schema en afwijzing van `{"bogus": "x"}` / lege query) slagen.
  Check: `uv run --directory mcp/web-search pytest tests/test_server.py -q` -> `passed`
- [x] Alle unit- en opposite-tests in `mcp/context-compressor/tests/test_server.py` (inclusief `fastmcp.Client`-test voor `{"path": "..."}` en afwijzing van `{"bogus": "x"}`) slagen.
  Check: `uv run --directory mcp/context-compressor pytest tests/test_server.py -q` -> `passed`
- [x] Alle 4 de skills (`skills/*/SKILL.md`), `references/audit-brief.md`, `GEMINI.md`, `CLAUDE.md` en `.cursor/rules/forensic-audit.mdc` noemen expliciet `query_or_url` bij `search_website`.
  Check: `(Select-String skills/*/SKILL.md,skills/docs-first-planner/references/audit-brief.md,GEMINI.md,CLAUDE.md,.cursor/rules/forensic-audit.mdc -Pattern "query_or_url" -List | Measure-Object).Count` -> `8`
- [x] `C:\Users\BramFransen\.gemini\config\mcp_config.json` verwijst voor `web-search` en `context-compressor` naar `D:\Github Projects\forensic-audit-skills\mcp\...` (`0` verwijzingen naar `C:\Users\BramFransen\forensic-audit-skills`), en alle `skills/`-bestanden zijn byte-voor-byte gesynchroniseerd met `C:\Users\BramFransen\.gemini\config\skills`.
  Check: `py -c "import json,pathlib; cfg=json.dumps(json.loads(pathlib.Path(r'C:\Users\BramFransen\.gemini\config\mcp_config.json').read_text(encoding='utf-8'))); loc=pathlib.Path(r'C:\Users\BramFransen\.gemini\config\skills'); rep=pathlib.Path(r'D:\Github Projects\forensic-audit-skills\skills'); print(('BramFransen\\\\forensic-audit-skills' not in cfg) and ('Github Projects\\\\forensic-audit-skills' in cfg) and sum((loc/p.relative_to(rep)).read_bytes()!=p.read_bytes() for p in rep.rglob('*') if p.is_file() and '__pycache__' not in p.parts)==0)"` -> `True`
- [x] `docs_tool.py check` geeft `docs OK` en de bijgewerkte regressiechecks van `bugs/01`, `feature/05`, `feature/09` en `feature/11` slagen.
  Check: `python skills/docs-first-planner/scripts/docs_tool.py check` -> `docs OK`

## Risks and open points
- Na het bijwerken van `C:\Users\BramFransen\.gemini\config\mcp_config.json` moeten de MCP-servers in een nieuwe of herstarte Antigravity-sessie worden geladen om actief te worden in de native MCP-toolset.

## Relations
- Bouwt voort op en actualiseert de pad-checks van: `bugs/01`, `feature/05`, `feature/06`, `feature/09`, `feature/10`, `feature/11`.

## Verification
| Criterion | How checked | Result |
| --- | --- | --- |
| `AliasChoices` op `SearchWebsiteInput`/`search_website` en `CompressContextInput`/`compress_context` | `(Select-String mcp/*/server.py -Pattern "AliasChoices" \| Measure-Object).Count` | `10` (5 in `mcp/web-search/server.py`, 5 in `mcp/context-compressor/server.py`), voldaan |
| `mcp/web-search` unit- en opposite-tests (`{"query": "..."}`, `{"url": "..."}`, `{"q": "..."}`, `{"filter": "..."}`, schema-integriteit & opposite tests op `{"bogus": "x"}` en `{"query": "   "}`) | `uv run --directory mcp/web-search pytest tests/test_server.py -q` | `24 passed in 4.16s`, voldaan |
| `mcp/context-compressor` unit- en opposite-tests (`{"path": "..."}`, `{"file": "..."}`, `{"root": "..."}`, `{"cwd": "..."}`, schema-integriteit, boundary check `0` & opposite tests op `{"bogus": "x"}` en `{"path": "   "}`) | `uv run --directory mcp/context-compressor pytest tests/test_server.py -q` + module boundary check | `16 passed in 1.98s`, boundary check `0`, voldaan |
| Expliciete `query_or_url=` naamgeving in alle 8 skill-, referentie- en regelbestanden + 2x `search_website.json` | `(Select-String skills/*/SKILL.md,skills/docs-first-planner/references/audit-brief.md,GEMINI.md,CLAUDE.md,.cursor/rules/forensic-audit.mdc -Pattern "query_or_url" -List \| Measure-Object).Count` | `8` bestanden + beide `search_website.json` schema's bijgewerkt, voldaan |
| Pad-consolidatie in `C:\Users\BramFransen\.gemini\config\mcp_config.json` en 100% byte-identieke sync naar `.gemini\config\skills` en `.gemini\antigravity-*\mcp\` | `Check:` uitgevoerd (`True` en `0` diffs) | `True` en `0` byte-verschillen, voldaan |
| `docs_tool.py index --strict`, `docs_tool.py check` en alle regressiechecks van `bugs/01`, `feature/05`, `feature/09` en `feature/11` | Alle `Check:`-regels en `docs_tool.py check` uitgevoerd | `docs OK`, alle checks groen |
