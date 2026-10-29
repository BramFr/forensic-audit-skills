---
id: feature/10
title: Lossless token-fixes in context-compressor en web-search (enkel tekst-transport, link-compactie, nooit-groter-guard)
category: feature
status: done
summary: output_schema=None in beide MCP-servers, [ID](ID-slug.md)->pad in compressor-output en guard dat compact nooit groter is dan raw.
tags: [mcp, context-compressor, web-search, token-efficiency, lossless, structured-content, benchmark]
created: 2026-10-29
updated: 2026-10-29
related: [feature/06, feature/08, feature/09]
---

# Lossless token-fixes in context-compressor en web-search (enkel tekst-transport, link-compactie, nooit-groter-guard)

## Why
"De rapportage is compact en eerlijk over wat niet is geverifieerd." Een benchmark (tiktoken `o200k_base`) toont dat de gescopete modi van `compress_context` 61–98% besparen, maar de index-aanroep van elke planner-run maar 2,8%, de volledig-bestand-modus 0–3% en TOML zelfs -0,4% (groter dan raw). Minder irrelevante tokens verbetert ook de kwaliteit van het model (Lost in the Middle, arXiv 2307.03172). Eis van de gebruiker: kwaliteit 100% gelijk, dus alleen strikt lossless wijzigingen.

## Starting point (audit findings)
- Verified: FastMCP 4.1.1 (Antigravity-Python 3.13) en 4.1.4 (uv-venv) sturen bij `-> str` zowel tekst als `structuredContent {"result": ...}` (in-memory `Client`-probe). `@mcp.tool(output_schema=None)` geeft `structured_content=None` met identieke tekst (probe). Patroon op 2 plekken: `mcp/context-compressor/server.py:688` en `mcp/web-search/server.py:1388`.
- Verified: Antigravity geeft het model de tekst 1x (live `compress_context`-aanroep, geen `{"result": ...}` zichtbaar) -> 0% modelwinst in Antigravity, alleen kleiner transport.
- Verified: link -> pad (`[bugs/01](bugs/01-slug.md)` -> `bugs/01-slug.md`) scheelt 3,5% op de Fase-1 index-aanroep (1880 -> 1815 tok); TOML compact = 258 vs raw 257 tok.
- Verified: MCP-spec 2025-06-18 (tools): "a tool that returns structured content SHOULD also return the serialized JSON in a TextContent block" (🔎); Anthropic "Effective context engineering": token-efficient tools, geen bloated tool sets (🔎).
- Corrected: eerdere schatting "≈50% per response" door het structured duplicaat was fout (geen van beide clients geeft beide aan het model). Inline `# Lx-Ly` op de def-regel maakt `--signatures` juist groter (-0,1% .. +1,3%) en vervalt.
- Unverified: Claude Code stuurt alléén `structuredContent` naar het model (GitHub issue anthropics/claude-code#55677, gelezen; lokaal niet getest, `claude` niet geïnstalleerd). Berekende meerkosten daar: +1,1% (index), +3,1% (sectie), +6,0% (`--signatures`) plus ge-escapete `\n`. Tokenizer `o200k_base` is een proxy voor Claude/Gemini (🔍).

## Decisions (from the grill)
| Question | Decision | Reason |
| --- | --- | --- |
| Wat betekent "kwaliteit 100% hetzelfde"? | Strikt lossless: alleen L1, L3, L4 | Gebruiker eist 100% gelijke informatie; rijfilter (B) kan overlap missen |
| `mcp/web-search` meenemen in L1? | Ja, beide servers | Zelfde oorzaak en fix; patroon projectbreed oplossen |
| Benchmark vooraf en achteraf? | Ja, met outputs bewaard en byte-vergelijking (omgekeerde L3 van nieuw == oud) | Bewijs dat de winst echt is en de inhoud 100% gelijk blijft |

## Scope
- In:
  - L1: `@mcp.tool(output_schema=None)` in `mcp/context-compressor/server.py` en `mcp/web-search/server.py`, met test.
  - L3: link-compactie in compressor-output, alleen als de linktekst exact gelijk is aan het pad tot de eerste `-` of `.` na de laatste `/` (deterministisch terug te rekenen), met tegentest.
  - L4: in volledig-bestand-modus (`section=None`) de raw tekst teruggeven als de compacte versie langer is, met test over alle ondersteunde repo-bestanden.
  - `MODULE.md` bijwerken; sync naar `C:\Users\BramFransen\forensic-audit-skills` (Antigravity draait dat pad) en `C:\Users\BramFransen\.gemini\antigravity-cli\mcp\web-search\server.py`.
  - Benchmark vooraf/achteraf met lossless-bewijs.
- Out (explicitly not doing):
  - Rijfilter op index-items (optie B), inkorten van `Annotated`-signatures (L5), inline regelnummers (L6).
  - Wijziging van het index-formaat in `docs_tool.py`; nieuwe tools of parameters; `tiktoken` als runtime-dependency.

## Approach
Code-stappen worden uitgevoerd door een schone code-subagent met een lossless `compress_context` Subagent Context Pack.
1. Benchmark vooraf: outputs van alle cases bewaren + tokens meten.
2. context-compressor: `@mcp.tool(output_schema=None)` + test via in-memory `Client` (`structured_content is None`, tekst gelijk).
3. web-search: idem + zelfde test.
4. context-compressor: link-compactie (L3) + test op index-rij + tegentest (niet-prefix-link blijft ongewijzigd; omgekeerde berekening geeft origineel).
5. context-compressor: nooit-groter-guard (L4) + test over alle ondersteunde repo-bestanden (`len(out) <= len(raw)`) met behoud van de woordvolgorde-lossless-check.
6. `MODULE.md` bijwerken; mirrors syncen; benchmark achteraf + lossless-vergelijking; cijfers in `## Verification`; Check-aantal in feature/08 bijwerken.

## Acceptance criteria
- [x] Beide servers sturen geen structured duplicaat meer.
  Check: `(Select-String mcp/*/server.py -Pattern '@mcp\.tool\(output_schema=None\)' | Measure-Object).Count` -> `2`
  Check: `(Select-String mcp/*/server.py -Pattern '@mcp\.tool\(\)' | Measure-Object).Count` -> `0`
- [x] Tests context-compressor (structured, L3 + tegentest, L4 over repo-bestanden, lossless) slagen.
  Check: `uv run --directory mcp/context-compressor pytest tests/test_server.py -q` -> `passed`, 0 failed
- [x] Tests web-search (incl. structured) slagen.
  Check: `uv run --directory mcp/web-search pytest tests/test_server.py -q` -> `passed`, 0 failed
- [x] Verboden afhankelijkheden blijven weg.
  Check: `(Select-String "mcp/context-compressor/server.py" -Pattern "curl_cffi|ddgs|playwright|trafilatura|prune_text" | Measure-Object).Count` -> `0`
- [x] Benchmark achteraf: elke case is byte-gelijk aan vooraf na omgekeerde L3 (of gelijk aan raw bij L4); index-aanroep ≥ 3% kleiner dan vooraf; geen case groter. (manual, cijfers onder Verification)
- [x] Mirrors identiek (repo vs `C:\Users\BramFransen\forensic-audit-skills` en `.gemini\config\skills`): byte-vergelijking -> `0` diffs. (manual)
- [x] Docs consistent.
  Check: `python skills/docs-first-planner/scripts/docs_tool.py check` -> `docs OK`

## Risks and open points
- Claude Code-effect lokaal niet bevestigd; acceptatie hangt er niet van af.
- Code die `structuredContent` programmatisch leest (geen bekend in dit project) krijgt die niet meer.
- Antigravity moet de MCP-servers herstarten om de nieuwe versie te laden.

## Relations
- Bouwt voort op feature/06 en feature/08 (Check-aantal "11 passed" bijwerken) en feature/09 (web-search).

## Verification
Datum: 2026-10-29. Benchmark op bevroren invoerbestanden (zelfde input vooraf en achteraf), tokenizer `o200k_base`. Kwaliteitsbewijs per case: output achteraf is byte-gelijk aan vooraf, of na omgekeerde L3 byte-gelijk, of gelijk aan het raw bestand (L4).

#schema:case|before_tok|after_tok|delta|quality
P1 index vision+kw+items+modules|1988|1918|-3.5%|lossless (L3 omkeerbaar)
P1 index Items,Modules|1566|1496|-4.5%|lossless (L3 omkeerbaar)
P1 index full|1992|1922|-3.5%|lossless (L3 omkeerbaar)
14 overige cases (frontmatter, headings, secties, signatures, symbolen, SKILL.md, MODULE.md, TOML)|-|-|0.0%|byte-identiek
TOTAAL 17 cases|25056|24846|-0.8%|100% lossless (0 DIFF)
MCP-transport `structuredContent`|310|0|-100%|tekst ongewijzigd (305 tok)

- TOML blijft 1 token groter dan raw: de compacte versie is 1 teken korter (alleen de laatste newline weg), maar `o200k_base` telt `"]` + newline als 1 token. Geen echte groei; de L4-guard vergelijkt op tekens en grijpt terecht niet in.
- Keuze tijdens bouw: een kleine CSV zonder quotes wordt in volledig-bestand-modus nu raw teruggegeven (DSV was langer); een CSV met quotes, waar DSV korter is, blijft DSV. De assertie in de test uit feature/08 is daarop aangepast.
- `uv run --directory mcp/context-compressor pytest tests/test_server.py -q` -> `15 passed`
- `uv run --directory mcp/web-search pytest tests/test_server.py -q` -> `23 passed`
- `@mcp.tool(output_schema=None)` -> `2`; `@mcp.tool()` -> `0`; verboden afhankelijkheden -> `0`
- Regressie feature/06 (7 / 9 / 7 verwijzingen) en feature/08: geslaagd.
- Gesynchroniseerd naar `C:\Users\BramFransen\forensic-audit-skills` en `C:\Users\BramFransen\.gemini\antigravity-cli\mcp\web-search\server.py`. Herstart de MCP-servers in Antigravity om de nieuwe versie te laden.
