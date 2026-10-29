---
id: feature/08
title: Uitbreiding Context-Compressor (AST Code-Extractie, Multi-Sectie, Tabel-DSV, JSON/YAML/TOML/CSV & Audit-Subagents)
category: feature
status: done
summary: Breid mcp/context-compressor uit met Python/JS/TS AST-extractie (--signatures & symbolen), multi-sectie/--frontmatter/--headings, Tabel->DSV, geneste JSON/YAML/TOML/CSV en Fase 1/2 skill-integratie.
tags: [mcp, context-compressor, ast, dsv, multi-section, subagent, token-efficiency, skills]
created: 2026-10-28
updated: 2026-10-28
related: [feature/05, feature/06, feature/07, bugs/04, feature/09, feature/10]
---

# Uitbreiding Context-Compressor (AST Code-Extractie, Multi-Sectie, Tabel-DSV, JSON/YAML/TOML/CSV & Audit-Subagents)

## Why
In `feature/06` is `mcp/context-compressor` (`compress_context`) gebouwd voor `.md`, `.txt` en vlakke `.json`-bestanden vlak vóór het starten van een code-subagent. In de praktijk laadt de hoofdagent tijdens **Fase 1 (Docs check)** en **Fase 2 (Forensic Audit / Security Scan)** echter nog steeds grote bronbestanden (`.py`, `.ts`, `.js`), meerdere Markdown-secties, Markdown-tabellen en geneste JSON-/config-bestanden (`site-inventory.json`, `pyproject.toml`, `.yaml`) in zijn eigen hoofdcontext. Door `compress_context` 100% lossless uit te breiden met 5 mogelijkheden (AST code-skeletten & functie-extractie, multi-sectie/`--frontmatter`/`--headings`, Markdown-tabel naar `#schema:` Pipe-DSV, geneste JSON/YAML/TOML/CSV en read-only Audit-Subagent Context Packs bij $\ge 3$ bestanden), besparen we 60% tot 99% BPE-tokens in zowel de hoofdsessie als de subagents met **0% kwaliteitsverlies**.

Visie uit `docs/index.md`: *"Deze skills laten een AI-agent controleren in plaats van instemmen. Ze gaan uit van nul vertrouwen en eisen bewijs in plaats van schijn... De rapportage is compact en eerlijk over wat niet is geverifieerd."*

## Starting point (audit findings)
- Verified: In `mcp/context-compressor/server.py` (`⚙️ EXECUTED` codebase-inspectie van r. 1–347) ondersteunt `compress_context` nu alleen `.md`, `.txt` en top-level `.json` met één enkele `section`-string, en compacteert `_compact_table_line` (r. 183–198) alleen spaties in Markdown-tabellen (`| col |` -> `|col|`) zonder `#schema:` conversie.
- Verified: Volgens de officiële Python `ast`-documentatie (`https://docs.python.org/3/library/ast.html`, `🔎 SOURCED`) bieden `ast.parse()`, `ast.get_source_segment()`, `ast.unparse()` en `FunctionDef`/`AsyncFunctionDef`/`ClassDef` exacte AST-extractie inclusief `lineno` en `end_lineno`. Real-time benchmark (`⚙️ EXECUTED` op `mcp/web-search/server.py`, 1.363 regels) bewijst dat `section="--signatures"` het tokengebruik verlaagt van `11.234` naar `1.978` tokens (**-82,4%**) en dat gerichte functie-extractie (`section="_apply_content_filter,_clean_plain_text_body"`) het verlaagt van `11.234` naar `1.162` tokens (**-89,7%**) met 0% verlies van code.
- Verified: Real-time benchmark (`⚙️ EXECUTED` op `docs/feature/06-lossless-context-compressor-en-code-subagent.md`) toont dat `section="--frontmatter"` `5.639` tokens reduceert naar `146` tokens (**-97,4%**), `section="--headings"` naar `59` tokens (**-99,0%**), en multi-sectie `section="Scope,Acceptance criteria"` naar `1.659` tokens (**-70,6%**).

## Decisions (from the grill)
| Question | Decision | Reason |
| --- | --- | --- |
| Wil je dat we alle 5 de gebenchmarkte uitbreidingen in zowel `mcp/context-compressor` als de 4 skills doorvoeren? | Ja, alle 5 de lossless uitbreidingen inbouwen in `mcp/context-compressor` én vastleggen in alle 4 de skills + na afloop een real-live benchmark opleveren | Levert maximale tokenreductie in zowel Fase 1 (Docs check), Fase 2 (Audit) als Fase 4/5 (Code-subagent) met 0% kwaliteitsverlies |

## Scope
- In:
  1. **Uitbreiding 1 — Python/JS/TS Broncode-extractie (`.py`, `.ts`, `.tsx`, `.js`, `.jsx`) in `mcp/context-compressor/server.py`**:
     - `section="--signatures"` (of `--outline`): extraheert voor `.py` via `ast.parse()` alle imports, korte top-level constanten, klassen en functie-/methode-signaturen met decorators, type-annotaties, 1e docstring-regel en `# L<start>-L<end>` regelnummers (en voor `.ts`/`.js` via regex/brace-matching alle `import`/`export`/`interface`/`type`/`class`/`function` signaturen met regelnummers).
     - `section="func1,ClassA"` (één of meer komma-gescheiden symbolen): extraheert de exacte broncode van de gevraagde functies, methoden of klassen inclusief decorators en `# L<start>-L<end>` header.
     - Zonder `section` op `.py`/`.ts`/`.js`: verwijdert meervoudige lege regels buiten strings zodat het bestand compact maar 100% valide blijft.
  2. **Uitbreiding 2 — Multi-Sectie (`section="A,B,C"`), `--frontmatter` en `--headings` op Markdown (`.md`, `.txt`)**:
     - `section="--frontmatter"`: retourneert uitsluitend het YAML-frontmatterblok (`--- ... ---`).
     - `section="--headings"`: retourneert alle Markdown-koppen (`#` t/m `######`) buiten code-fences met hun regelnummer (`L<nr>: ## Heading`).
     - `section="Why,Scope,Acceptance criteria"` (komma-gescheiden lijst): extraheert alle genoemde secties in één call in documentvolgorde.
  3. **Uitbreiding 3 — Markdown-Tabel -> Positional Pipe-DSV (`#schema:`) wanneer `dsv_for_flat_lists=True`**:
     - Zet Markdown-tabellen met $\ge 2$ datarijen (buiten code-fences) automatisch om naar `#schema:kol1|kol2...` gevolgd door `cel1|cel2...` zonder de `|---|---|` scheidingslijn en zonder voorloop-/achterloop-pipes. Bij `dsv_for_flat_lists=False` blijft de gecompacteerde Markdown-tabel (`|col|`) behouden.
  4. **Uitbreiding 4 — Geneste JSON-sleutels (`section` op `.json` + auto-DSV op geneste lijsten) + `.yaml`/`.yml`/`.toml`/`.csv`/`.tsv`**:
     - Op `.json`: ondersteunt `section="key1,key2"` om specifieke top-level sleutels uit een JSON-object te extraheren (bijv. `section="routes"` op `site-inventory.json`), en zet bij `dsv_for_flat_lists=True` óók vlakke lijsten van $\ge 2$ objecten **binnenin** een JSON-dict om naar `#schema:` Pipe-DSV onder `#key:<naam>`.
     - Op `.csv` en `.tsv`: parseert via Python `csv.reader` en zet direct om naar `#schema:col1|col2...` Pipe-DSV.
     - Op `.yaml`, `.yml` en `.toml`: stript volregelige `#`-commentaarregels en meervoudige witregels buiten strings.
  5. **Uitbreiding 5 — Skill- & Richtlijn-update (`skills/*/SKILL.md`, `GEMINI.md`, `CLAUDE.md`, `.cursor/rules/forensic-audit.mdc`, `README.md`, `mcp/context-compressor/MODULE.md` & `README.md`)**:
     - Leg vast dat `compress_context` in **3 fasen** wordt gebruikt:
       1. **Fase 1 (Progressive Reading):** `section="--frontmatter"`, `section="--headings"` en multi-sectie `section="Why,Scope"` op `.md` docs.
       2. **Fase 2 (Audit & Security Scan):** `section="--signatures"` en `section="sym1,sym2"` op `.py`/`.ts`/`.js` bronbestanden + `section="key"` op `.json`, én bij diepte-audits van $\ge 3$ bronbestanden het delegeren naar een read-only `research`-subagent met een gecomprimeerd Context Pack die rapporteert in `#schema:point|status|file_line|evidence`.
       3. **Fase 4/5 (Code-Subagent Isolation):** verplicht bij elke codewijziging een schone code-subagent starten met een Context Pack (`--signatures` + exacte doel-functies + plan-secties).
- Out (explicitly not doing):
  - Geen lossy woord-pruning (`IDF_DICT` / `prune_text`), geen wijziging van identifiers/casing, en geen netwerk-imports in `mcp/context-compressor`.

## Scaffold
Technical choices (fixed here so the agent does not pick them at random; reuse what the project already uses):
| Choice | Decision | Why (in the user's situation) |
| --- | --- | --- |
| AST & Parsers | Python stdlib `ast`, `csv`, `json`, `re`, `pathlib` | 100% deterministisch, 0 extra externe dependencies nodig in `mcp/context-compressor` |
| Bestandsformaten | `.md`, `.txt`, `.json`, `.py`, `.ts`, `.tsx`, `.js`, `.jsx`, `.yaml`, `.yml`, `.toml`, `.csv`, `.tsv` | Dekt alle documentatie-, broncode-, configuratie- en inventarisbestanden in audits en projecten |

Tree (new or changed folders only):
```text
mcp/
  context-compressor/
    MODULE.md
    README.md
    server.py
    tests/
      test_server.py
```

Dependency direction (arrow = may import): `mcp/context-compressor/tests` -> `mcp/context-compressor`. Geen imports uit `mcp/web-search`.

| Module | Does | Does NOT do | May depend on |
| --- | --- | --- | --- |
| `mcp/context-compressor` | Lossless compressie & gerichte extractie op `.md`/`.txt` (multi-sectie, `--frontmatter`, `--headings`, Tabel->DSV), `.py`/`.ts`/`.js` (AST `--signatures` & symbool-extractie), `.json` (sleutel-extractie, RFC 8259 minificatie, top-level & geneste Pipe-DSV), `.csv`/`.tsv` (Pipe-DSV) en `.yaml`/`.toml` (comment/whitespace stripping) binnen `workspace_root` | Geen lossy IDF/perplexity woord-pruning (`prune_text`), geen `text.lower()` op inhoud, geen netwerk/HTTP-calls (`curl_cffi`/`ddgs`/`playwright`), geen lezen buiten `workspace_root` | Python stdlib (`ast`, `csv`, `io`, `json`, `re`, `pathlib`, `typing`), `fastmcp`, `pydantic` |

## Approach
1. **Bouw een lossless Subagent Context Pack met `compress_context`** en start een schone code-subagent (`invoke_subagent`) voor `mcp/context-compressor/server.py`, `tests/test_server.py`, `MODULE.md`, `README.md` en de tool-schema's `compress_context.json` -> verify: `uv run --directory mcp/context-compressor pytest tests/test_server.py -q`
2. **Werk alle 4 de skills (`skills/*/SKILL.md`), `GEMINI.md`, `CLAUDE.md`, `.cursor/rules/forensic-audit.mdc` en `README.md` bij** met de uitgebreide Fase 1/2/4 `compress_context`-workflow en synchroniseer alles naar `.gemini` en `C:\Users\BramFransen\forensic-audit-skills` -> verify: `python skills/docs-first-planner/scripts/docs_tool.py check`
3. **Draai een Real-Live Benchmark (`⚙️ EXECUTED`)** op alle 5 de nieuwe `compress_context`-modi + een live A/B subagent-test en rapporteer de exacte token- en kwaliteitsresultaten aan de gebruiker.

## Acceptance criteria
- [x] `mcp/context-compressor/server.py` ondersteunt alle 5 de lossless uitbreidingen (AST `--signatures` & symbool-extractie op `.py`/`.ts`/`.js`, `--frontmatter`/`--headings`/multi-sectie op `.md`, Markdown-tabel -> `#schema:` Pipe-DSV bij `dsv_for_flat_lists=True`, geneste JSON-sleutels/lijsten + `.csv`/`.tsv`/`.yaml`/`.toml`), en alle unit- en opposite-tests slagen.
  Check: `uv run --directory mcp/context-compressor pytest tests/test_server.py -q` -> `15 passed` (was 11; +4 tests in feature/10)
- [x] `mcp/context-compressor/server.py` respecteert de module-grenzen uit `MODULE.md` (0 verboden imports of lossy `prune_text`).
  Check: `(Select-String "mcp/context-compressor/server.py" -Pattern "curl_cffi|ddgs|playwright|trafilatura|prune_text" | Measure-Object).Count` -> `0`
- [x] Alle 4 de skills (`skills/*/SKILL.md`), `GEMINI.md`, `CLAUDE.md` en `.cursor/rules/forensic-audit.mdc` beschrijven het gebruik van `compress_context` voor Fase 1 (`--frontmatter`/`--headings`/multi-sectie), Fase 2 (`--signatures` & read-only audit-subagents) en Fase 4/5 (code-subagents).
  Check: `(Select-String skills/*/SKILL.md,GEMINI.md,CLAUDE.md,.cursor/rules/forensic-audit.mdc -Pattern "--signatures" -List | Measure-Object).Count` -> `7`
- [x] Alle gewijzigde bestanden zijn gesynchroniseerd naar `.gemini` en `C:\Users\BramFransen\forensic-audit-skills`, en `docs_tool.py check` geeft `docs OK`.
  Check: `python skills/docs-first-planner/scripts/docs_tool.py check` -> `docs OK`

## Risks and open points
- Wanneer een `.py`-bestand een syntaxfout bevat waardoor `ast.parse()` faalt, valt `compress_context` bij broncode veilig terug op regel-/regex-extractie of compacte tekst zonder te crashen.

## Relations
- Bouwt voort op: `feature/06` (Lossless Context-Compressor en Code-Subagent Isolatie) en `feature/07` / `bugs/04`.

## Verification
| Criterion | How checked | Result |
| --- | --- | --- |
| Alle 5 lossless uitbreidingen in `mcp/context-compressor/server.py` & `tests/test_server.py` | `uv run --directory mcp/context-compressor pytest tests/test_server.py -q` | `11 passed in 0.85s`, voldaan |
| Module-grenzen (`MODULE.md`): 0 verboden imports of lossy `prune_text` | `(Select-String "mcp/context-compressor/server.py" -Pattern "curl_cffi\|ddgs\|playwright\|trafilatura\|prune_text" \| Measure-Object).Count` | `0`, voldaan |
| Fase 1/2/4 `compress_context` (`--signatures`, `--frontmatter`, `--headings`) in alle 7 skill-/regelbestanden | `(Select-String skills/*/SKILL.md,GEMINI.md,CLAUDE.md,.cursor/rules/forensic-audit.mdc -Pattern "--signatures" -List \| Measure-Object).Count` | `7`, voldaan |
| Synchronisatie naar `.gemini` en `C:\Users\BramFransen\forensic-audit-skills` + `docs_tool.py check` | `python skills/docs-first-planner/scripts/docs_tool.py check` | `docs OK`, voldaan |
