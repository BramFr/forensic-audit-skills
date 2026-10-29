---
id: feature/06
title: Lossless Context-Compressor MCP en verplichte Code-Subagent Isolatie
category: feature
status: done
summary: Voeg mcp/context-compressor (sectie/DSV/JSON) toe en start bij elke codewijziging een schone code-subagent + fix bugs/02-03.
tags: [mcp, context-compressor, subagent, token-efficiency, dsv, planner, forensic-audit, sync]
created: 2026-10-27
updated: 2026-10-27
related: [bugs/01, bugs/02, bugs/03, feature/04, feature/05, feature/10]
---

# Lossless Context-Compressor MCP en verplichte Code-Subagent Isolatie

## Why
Lange AI-sessies lopen vast op *context rot*: zodra het contextvenster volraakt met zoekresultaten, logs en tussenstappen, zakt de nauwkeurigheid in het midden van de context met 15 tot 20 procentpunt (*Lost in the Middle*, `arXiv:2307.03172`). Door een tweede, 100% lossless FastMCP-server (`mcp/context-compressor`) toe te voegen én in alle vier de skills (`docs-first-planner`, `forensic-audit`, `forensic-security-audit`, `forensic-site-audit`) vast te leggen dat voor **élke codewijziging** (ook 1 regel code) een schone subagent in zijn eigen context-bubble wordt gestart met een gecomprimeerd **Subagent Context Pack**, besparen we 35% tot 89% context-tokens terwijl de code-agent op maximale scherpte werkt. Tegelijkertijd herstellen we de regressie uit `bugs/02` en `bugs/03` (`## Search keywords` in `docs-first-planner`).
Visie uit `docs/index.md`: *"Deze skills laten een AI-agent controleren in plaats van instemmen. Ze gaan uit van nul vertrouwen en eisen bewijs in plaats van schijn... De rapportage is compact en eerlijk over wat niet is geverifieerd."*

## Starting point (audit findings)
- Verified: Uitgevoerde codebase-scan (`Select-String`, `⚙️ EXECUTED`) op `skills/*/SKILL.md`, `CLAUDE.md`, `GEMINI.md` en `mcp/` toont `0` bestaande modules of instructies voor subagent-delegatie (`invoke_subagent`/`Agent`), DSV-compressie of `context-compressor`; `docs-first-planner` bevat wél al `MODULE.md`-scaffolding en *progressive reading* (`skills/docs-first-planner/SKILL.md:25-33`).
- Verified: Uitgevoerde Python-audit (`⚙️ EXECUTED`) en primaire bronnen bewijzen dat statistische IDF-pruning (`prune_text`), lowercase-tokenisatie en Chinese Hanzi-encoding **onbruikbaar** zijn voor code- en audit-context: ze verminken JSON-syntaxis (IETF RFC 8259, `https://datatracker.ietf.org/doc/html/rfc8259`, `🔎 SOURCED`), breken CamelCase-identifiers, URL's en Markdown-tabellen (CommonMark Spec 0.31.2, `https://spec.commonmark.org/`, `🔎 SOURCED`), verwijderen technische kernwoorden (`server`, `code`, `bestand`) als eerste (ISO 25964 / NISO, `https://www.niso.org/schemas/iso25964`, `🔎 SOURCED`) en veroorzaken kwaliteitsverlies op instructies (Microsoft Research LLMLingua-2, `https://www.microsoft.com/en-us/research/project/llmlingua/llmlingua-2/`, en `https://arxiv.org/html/2310.05736`, `🔎 SOURCED`).
- Verified: Lossless sectie-extractie (`section`) + tabel-/witruimte-compactie (`⚙️ EXECUTED` op deze repo) reduceert `docs/index.md` (`## Search keywords`) van `3.628` naar `1.010` tekens (**-72,2%**) en `skills/forensic-audit/SKILL.md` (`## Compact report`) van `20.532` naar `2.174` tekens (**-89,4%**) met **0% betekenisverlies**.
- Verified: BPE-doorrekening (`🧮 HAND-CALCULATED` op `o200k_base` / `cl100k_base` regels uit `https://tokenreference.com/tokenizers/o200k_base/`, `🔎 SOURCED`) en de File Format Token Accuracy Benchmark (`https://github.com/thoeltig/file-format-token-accuracy-benchmark-results`, `🔎 SOURCED`) tonen dat Pipe-DSV (`#schema:kol1|kol2...`, RFC 4180 `https://datatracker.ietf.org/doc/html/rfc4180`, `🔎 SOURCED`) vanaf **$N \ge 2$ vlakke rijen** netto tokens bespaart t.o.v. Compact JSON ($15 + 20N < 33N$, bij $N=10$: **-34,8%** t.o.v. JSON en **-48,8%** t.o.v. proza), terwijl `JSON_COMPACT` (`json.dumps(separators=(',',':'))`) wint bij $N=1$ en bij geneste of sparse data (98,5% vs. 73% nauwkeurigheid).
- Verified: Subagent-isolatie voorkomt *context rot* (Stanford Liu et al. `https://arxiv.org/abs/2307.03172` en The Stack Underflow `https://www.thestackunderflow.com/tutorials/subagent-isolation-context-rot/`, `🔎 SOURCED`) en wordt native ondersteund door zowel Antigravity (`invoke_subagent`) als Claude Code (`Agent` tool / `.claude/agents/`, `https://code.claude.com/docs/en/sub-agents` en `https://claude.com/resources/articles/subagents-in-claude-code`, `🔎 SOURCED`).
- Verified: Re-audit op FastMCP (`https://gofastmcp.com/servers/tools`, `🔎 SOURCED`) en OWASP MCP Security Cheat Sheet (`https://cheatsheetseries.owasp.org/cheatsheets/MCP_Security_Cheat_Sheet.html`, `🔎 SOURCED`): een tweede FastMCP-server (`mcp/context-compressor/server.py`) met Pydantic `extra="forbid"` en `Path.resolve().is_relative_to(workspace_root)` voorkomt path traversal buiten de workspace.
- Corrected: Regressie uit commit `b8b68f5` (`⚙️ EXECUTED`, vastgelegd in `bugs/02` en `bugs/03`) waarbij `skills/docs-first-planner/SKILL.md`, `references/audit-brief.md`, `references/plan-template.md` en `scripts/docs_tool.py` (`SKELETON`) hun `## Search keywords`-instructie verloren (`6` i.p.v. `9` treffers).
- Unverified: De `tiktoken` C-extensie is lokaal niet geïnstalleerd onder Python 3.15; BPE-token-aantallen zijn daarom handmatig berekend (`🧮`) volgens de geverifieerde `o200k_base` pre-segmentatieregels (`🔎`).

## Decisions (from the grill)
| Question | Decision | Reason |
| --- | --- | --- |
| Hoe breed bouwen we de token-efficiënte subagent-overdracht in en nemen we `bugs/02` & `bugs/03` mee? | In alle 4 de skills + `CLAUDE.md`/`GEMINI.md`/`.cursor` + direct de `Search keywords`-regressie (`bugs/02` en `bugs/03`) mee-repareren | Houdt alle skills en richtlijnen 100% consistent en herstelt direct de gefaalde regressiechecks op `bugs/01` en `feature/04` |
| Wanneer moet de hoofdagent bij het schrijven of aanpassen van code een aparte subagent starten? | **Altijd** een schone code-subagent starten voor élke codewijziging (ook voor 1 regel code), met een compact Subagent Context Pack | Garandeert dat code altijd in een volledig schone context-bubble zonder ruis uit de hoofdsessie wordt geschreven |
| Waar bouwen we de lossless context-compressor in? | Als een aparte, tweede FastMCP-server (`mcp/context-compressor/server.py`) naast `mcp/web-search`, geregistreerd in `mcp_config.json` | Maakt `compress_context` als native MCP-tool beschikbaar in alle gekoppelde AI-clients naast `search_website` |

## Scope
- In:
  - Nieuwe FastMCP-servermodule `mcp/context-compressor/` (`MODULE.md`, `pyproject.toml`, `README.md`, `server.py`, `tests/test_server.py`) met de tool `compress_context`:
    1. **Markdown/Tekst (`.md`, `.txt`)**: optionele sectie-extractie op kopnaam (`section`), behoud van YAML-frontmatter/codeblokken/inline-code/identifiers/hoofdletters, en lossless compactie van witregels en Markdown-tabellen (`| col |` -> `|col|`).
    2. **JSON (`.json`)**: valide RFC 8259 minificatie (`json.dumps(separators=(',',':'))`), of automatische conversie naar **Positional Pipe-DSV** (`#schema:k1|k2...` met `\|`-escaping) voor vlakke, dense lijsten vanaf **$N \ge 2$ records** (`dsv_for_flat_lists=True`).
    3. **Markdown-tabel naar DSV**: zet vlakke Markdown-tabellen met $\ge 2$ datarijen optioneel om naar `#schema:...` DSV-formaat.
    4. **Beveiliging (Guard)**: strikte padvalidatie via `Path.resolve().is_relative_to(workspace_root)` en Pydantic `ConfigDict(extra="forbid")`.
  - Registratie van `context-compressor` in `C:\Users\BramFransen\.gemini\config\mcp_config.json` en aanmaken van de tool-schema's in `C:\Users\BramFransen\.gemini\antigravity-cli\mcp\context-compressor\compress_context.json` en `C:\Users\BramFransen\.gemini\antigravity-ide\mcp\context-compressor\compress_context.json`.
  - Vastleggen van het **Code-Subagent Isolation & Context Pack Protocol** in alle 4 de skills (`skills/*/SKILL.md`), `references/plan-template.md`, `CLAUDE.md`, `GEMINI.md`, `.cursor/rules/forensic-audit.mdc` en `README.md`:
    - Bij **élke codewijziging** (nieuw bestand, module, feature, bugfix of 1-regelige aanpassing) start de hoofdagent verplicht een schone code-subagent (`invoke_subagent` in Antigravity, `Agent` tool in Claude Code; alleen fallback naar hoofdsessie als het platform geen subagent-tool biedt).
    - De hoofdagent stuurt geen ruwe chat-historie mee, maar een compact **Subagent Context Pack** (opgebouwd via `compress_context`): (1) `MODULE.md` / doelbestand-sectie, (2) exacte eisen/interfaces, (3) relevante bevindingen in DSV ($N \ge 2$ vlakke rijen) of `JSON_COMPACT` (genest/sparse), en (4) het verificatiecommando (`Check:` / `pytest`).
    - Wijzigingen aan **hetzelfde bestand** worden nooit door twee parallelle subagents tegelijk uitgevoerd, maar in één subagent gebundeld of strikt sequentieel gedraaid.
  - Herstel van de `## Search keywords`-regressie (`bugs/02` en `bugs/03`) in `skills/docs-first-planner/SKILL.md`, `references/audit-brief.md`, `references/plan-template.md` en `scripts/docs_tool.py` (`SKELETON`), en byte-identieke synchronisatie naar `C:\Users\BramFransen\.gemini\config\skills` en `C:\Users\BramFransen\forensic-audit-skills`.
- Out (explicitly not doing):
  - Geen lossy statistische woord-pruning (`IDF_DICT` / `prune_text`), geen lowercase-conversie, geen Chinese Hanzi-encoding en geen lokale LLMLingua/GPT-2 modellen.
  - Geen parallelle subagents die gelijktijdig hetzelfde bestand bewerken.
  - Geen toegang tot bestanden buiten de actieve project-workspace in `compress_context`.

## Scaffold
Technical choices (fixed here so the agent does not pick them at random; reuse what the project already uses):
| Choice | Decision | Why (in the user's situation) |
| --- | --- | --- |
| Framework / language | Python >= 3.11 (lokaal Python 3.13) + `fastmcp>=2.0.0` + `pydantic>=2.7.0` | Zelfde stack en Python 3.13-runtime als `mcp/web-search`, geen nieuwe zware dependencies nodig |
| Transport & Config | MCP `stdio` geregistreerd in `mcp_config.json` + JSON-schema in `.gemini/antigravity-*` | Draait lokaal zonder netwerkpoort of API-keys naast `web-search` |
| Compressie-engine | Pure Python stdlib (`json`, `re`, `pathlib`) binnen `mcp/context-compressor/server.py` | 100% deterministisch, lossless en razendsnel ($O(L)$ tijd) zonder externe C-extensies |

Tree (new or changed folders only):
```text
mcp/
  context-compressor/
    MODULE.md
    pyproject.toml
    README.md
    server.py
    tests/
      test_server.py
```

Dependency direction (arrow = may import): `mcp/context-compressor/tests` -> `mcp/context-compressor`. No cycles, and no imports from `mcp/web-search`.

| Module | Does | Does NOT do | May depend on |
| --- | --- | --- | --- |
| `mcp/context-compressor` | Lossless sectie-extractie (`.md`/`.txt`), tabel-compactie, RFC 8259 JSON-minificatie en Pipe-DSV conversie ($N \ge 2$) binnen de workspace via MCP tool `compress_context` | Geen lossy IDF/perplexity woord-pruning (`prune_text`), geen `text.lower()` op inhoud, geen netwerk/HTTP-calls (`curl_cffi`/`ddgs`/`playwright`), geen lezen buiten `workspace_root` | Python stdlib (`json`, `re`, `pathlib`), `fastmcp`, `pydantic` |

Key interfaces (signatures and data shapes only, no bodies):
```python
class CompressContextInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    file_path: str
    section: str | None = None
    dsv_for_flat_lists: bool = True
    workspace_root: str | None = None

def compress_context(
    file_path: str,
    section: str | None = None,
    dsv_for_flat_lists: bool = True,
    workspace_root: str | None = None,
) -> str: ...
```

Existing code searched for overlap: `Select-String -Path "skills\*\SKILL.md","mcp\*\*.py" -Pattern "subagent|invoke_subagent|DSV|prune|compress_context"` -> `0` bestaande modules of functies gevonden; nieuw module-pad `mcp/context-compressor` is vrij van overlap.

## Approach
1. **Implementeer module `mcp/context-compressor`** volgens het `MODULE.md`-contract (`pyproject.toml`, `README.md`, `server.py`, `tests/test_server.py` incl. unit-tests voor `.md`-secties, `.json`-minificatie, DSV vanaf $N \ge 2$, sparse JSON-behoud, en opposite tests voor path traversal `../` en behoud van hoofdletters/identifiers) -> verify: `py -3.13 -m pytest mcp/context-compressor/tests/test_server.py -q`
2. **Registreer `context-compressor` in MCP-configuraties en tool-schema's**: voeg de server toe aan `C:\Users\BramFransen\.gemini\config\mcp_config.json` en schrijf `compress_context.json` naar `C:\Users\BramFransen\.gemini\antigravity-cli\mcp\context-compressor\compress_context.json` en `C:\Users\BramFransen\.gemini\antigravity-ide\mcp\context-compressor\compress_context.json` -> verify: `(Select-String "C:\Users\BramFransen\.gemini\config\mcp_config.json","C:\Users\BramFransen\.gemini\antigravity-cli\mcp\context-compressor\compress_context.json","C:\Users\BramFransen\.gemini\antigravity-ide\mcp\context-compressor\compress_context.json" -Pattern "compress_context|context-compressor" -List | Measure-Object).Count`
3. **Herstel de `## Search keywords`-regressie (`bugs/02` en `bugs/03`) én voeg het Code-Subagent Isolation & Context Pack Protocol toe** aan alle 4 de skills (`skills/docs-first-planner/SKILL.md`, `skills/forensic-audit/SKILL.md`, `skills/forensic-security-audit/SKILL.md`, `skills/forensic-site-audit/SKILL.md`), `skills/docs-first-planner/references/audit-brief.md`, `skills/docs-first-planner/references/plan-template.md`, `skills/docs-first-planner/scripts/docs_tool.py` (`SKELETON`), `CLAUDE.md`, `GEMINI.md`, `.cursor/rules/forensic-audit.mdc` en `README.md` -> verify: `(Select-String skills/*/SKILL.md,skills/docs-first-planner/references/audit-brief.md,skills/docs-first-planner/references/plan-template.md,GEMINI.md,CLAUDE.md,.cursor/rules/forensic-audit.mdc -Pattern "Search keywords" -List | Measure-Object).Count`
4. **Synchroniseer en verifieer**: werk `## Search keywords` in `docs/index.md` bij, synchroniseer alle gewijzigde bestanden byte-identiek naar `C:\Users\BramFransen\.gemini\config\skills` en `C:\Users\BramFransen\forensic-audit-skills`, zet `bugs/01`, `bugs/02`, `bugs/03` en `feature/04` na geslaagde checks op `done`, regenereer de index + module-tabel (`docs_tool.py modules` & `docs_tool.py index --strict`) en draai `docs_tool.py check` -> verify: `python skills/docs-first-planner/scripts/docs_tool.py check`

## Acceptance criteria
- [x] `mcp/context-compressor/server.py` en `mcp/context-compressor/tests/test_server.py` bestaan, slagen voor alle unit- en opposite-tests (sectie-extractie, tabel-compactie, RFC 8259 JSON-minificatie, Pipe-DSV bij $N \ge 2$, behoud van casing/identifiers, en blokkade van path traversal buiten `workspace_root`), en bevatten geen verboden imports of lossy pruning (`0` hits op `curl_cffi|ddgs|playwright|prune_text`).
  Check: `py -3.13 -m pytest mcp/context-compressor/tests/test_server.py -q` -> `passed`
- [x] `mcp/context-compressor/server.py` respecteert de module-grenzen uit `mcp/context-compressor/MODULE.md` (geen netwerk-/scraper-imports en geen lossy `prune_text`).
  Check: `(Select-String "mcp/context-compressor/server.py" -Pattern "curl_cffi|ddgs|playwright|trafilatura|prune_text" | Measure-Object).Count` -> `0`
- [x] `context-compressor` (`compress_context`) is geregistreerd in `C:\Users\BramFransen\.gemini\config\mcp_config.json` en in beide `compress_context.json` schema's (`antigravity-cli` en `antigravity-ide`).
  Check: `(Select-String "C:\Users\BramFransen\.gemini\config\mcp_config.json","C:\Users\BramFransen\.gemini\antigravity-cli\mcp\context-compressor\compress_context.json","C:\Users\BramFransen\.gemini\antigravity-ide\mcp\context-compressor\compress_context.json" -Pattern "context-compressor|compress_context" -List | Measure-Object).Count` -> `3`
- [x] Alle 4 de skills (`skills/*/SKILL.md`), `CLAUDE.md`, `GEMINI.md` en `.cursor/rules/forensic-audit.mdc` verplichten het starten van een schone code-subagent voor élke codewijziging met een lossless Subagent Context Pack (`compress_context`).
  Check: `(Select-String skills/*/SKILL.md,GEMINI.md,CLAUDE.md,.cursor/rules/forensic-audit.mdc -Pattern "compress_context" -List | Measure-Object).Count` -> `7`
- [x] De `## Search keywords`-regressie (`bugs/02` en `bugs/03`) is hersteld: alle 9 skill-/regelbestanden bevatten `Search keywords` en `docs_tool.py` bevat `## Search keywords` in `SKELETON`.
  Check: `(Select-String skills/*/SKILL.md,skills/docs-first-planner/references/audit-brief.md,skills/docs-first-planner/references/plan-template.md,GEMINI.md,CLAUDE.md,.cursor/rules/forensic-audit.mdc -Pattern "Search keywords" -List | Measure-Object).Count` -> `9`
- [x] Alle `skills/`-bestanden en de repo-kopie in `C:\Users\BramFransen\forensic-audit-skills` (inclusief `mcp/context-compressor/`) zijn byte-voor-byte gesynchroniseerd en `docs_tool.py check` geeft `docs OK`.
  Check: `python skills/docs-first-planner/scripts/docs_tool.py check` -> `docs OK`

## Risks and open points
- Aanname BPE-telling: omdat `tiktoken` geen prebuilt wheel voor Python 3.15 had tijdens de audit, zijn de exacte BPE-token-aantallen handmatig doorgerekend (`🧮`) tegen de geverifieerde `o200k_base` regex-presegmentatieregels (`🔎`).
- Wanneer een agent draait in een CLI/IDE die geen subagent-tool (`invoke_subagent` of `Agent`) aanbiedt, valt de agent veilig terug op het laden van hetzelfde gecomprimeerde Context Pack in de huidige sessie zodat het werk niet blokkeert.
- Voor een wijziging van 1 regel code brengt het starten van een subagent een vaste opstart-overhead (~1k–2k systeemtokens) met zich mee; dit is een bewuste keuze van de gebruiker om 100% context-isolatie te garanderen bij elke code-actie.

## Relations
- Lost op en sluit: `bugs/02`, `bugs/03` (en herstelt `bugs/01`, `feature/04` naar `done`).
- Bouwt voort op: `feature/04`, `feature/05`.

## Verification
| Criterion | How checked | Result |
| --- | --- | --- |
| `mcp/context-compressor` unit- & opposite-tests (sectie-extractie, RFC 8259 JSON, Pipe-DSV bij $N \ge 2$, casing/identifiers, path-traversal guard) | `py -3.13 -m pytest mcp/context-compressor/tests/test_server.py -q` (zowel repo als live mirror) | `7 passed in 1.08s`, voldaan |
| Module-grenzen (`mcp/context-compressor/MODULE.md`): `0` verboden imports of lossy pruning | `Check:` uitgevoerd (`Select-String` op `curl_cffi\|ddgs\|playwright\|trafilatura\|prune_text`) | `0` treffers, voldaan (`MODULE.md` status op `done` gezet) |
| Registratie van `context-compressor` in `mcp_config.json` + 2x `compress_context.json` (`antigravity-cli` & `antigravity-ide`) | `Check:` uitgevoerd (`Select-String`) | `3` bestanden geverifieerd, voldaan |
| Verplichte Code-Subagent Isolation & `compress_context` Context Pack in 7 skill-/regelbestanden | `Check:` uitgevoerd (`Select-String`) | `7` bestanden geverifieerd, voldaan |
| Herstel van `Search keywords`-regressies (`bugs/02` en `bugs/03`) in 9 bestanden + `docs_tool.py` `SKELETON` | `Check:` uitgevoerd (`Select-String` -> `9` en `True`) | `9` en `True`, voldaan |
| 100% byte-identieke sync naar `.gemini/config/skills` en `C:\Users\BramFransen\forensic-audit-skills` + `docs_tool.py check` | Python byte-vergelijking (`gemini_skills_diff: 0`, `mirror_diff: 0`) + `docs_tool.py check` | `0` verschillen en `docs OK`, voldaan |
