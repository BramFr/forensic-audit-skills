---
summary: Lossless MCP context-compressor (Markdown multi-sectie/frontmatter/headings/Tabel-DSV, getrapte filter_query tabel-projectie, Slim Plan-Read op ./docs/<cat>/NN-*.md, Python/TS AST --signatures & symbolen, JSON/YAML/TOML/CSV) voor hoofdagent & subagents.
keywords: [mcp, context-compressor, lossless, ast, signatures, section-scoping, dsv, filter-query, slim-plan, json-minification, subagent]
depends_on: []
status: done
---
# mcp/context-compressor

## Purpose
Levert een 100% lossless, deterministische FastMCP-server (`compress_context`) waarmee zowel de hoofdagent (tijdens Fase 1 Progressive Reading en Fase 2 Audits) als schone read-only en code-subagents alléén de relevante Markdown-secties (`--frontmatter`, `--headings`, `--all`, `A,B,C`), getrapte `#schema:` tabellen (`filter_query`), slanke plan-overzichten (`section=None` op `./docs/<cat>/NN-*.md`), Python/JS/TS AST-signaturen (`--signatures`) of specifieke functies/klassen (`func1,ClassA`), Pipe-DSV tabellen (`#schema:col1|col2...`) of geminificeerde JSON/YAML/TOML/CSV inladen zonder context rot.

## Boundaries
- **Does**: Leest `.md`, `.txt`, `.json`, `.py`, `.ts`, `.tsx`, `.js`, `.jsx`, `.yaml`, `.yml`, `.toml`, `.csv` en `.tsv` bestanden binnen de project-workspace; accepteert op `file_path` transparant de Pydantic `AliasChoices("file_path", "path", "file", "filepath")`, op `workspace_root` `AliasChoices("workspace_root", "root", "cwd")` en op `filter_query` `AliasChoices("filter_query", "filter", "query", "keywords")` zonder het gepubliceerde JSON-schema te vergroten; extraheert optioneel één of meer komma-gescheiden secties (met voorrang voor exacte/prefix H2–H6 heading-matches boven H1/substring-matches en automatische deduplicatie van overlappende regelbereiken), symbolen of JSON-sleutels (`section`), `--frontmatter`, `--headings`, `--all` of `--signatures`; zet Markdown-tabellen ($\ge 2$ datarijen), `.csv`/`.tsv` en vlakke JSON-lijsten (top-level én genest binnen een dict) om naar `#schema:col1|col2...` Pipe-DSV met `\|`-escaping wanneer `dsv_for_flat_lists=True`; past bij `filter_query` getrapte kolom-projectie toe op tabellen met $\ge 4$ kolommen (matchende rijen behouden alle kolommen, niet-matchende rijen worden geprojecteerd naar de eerste 3 identificerende kolommen zoals `ID|Status|Title`); laat bij een standaard full-file read (`section=None`) op een `./docs/<cat>/NN-*.md` planbestand automatisch de zware secties (`## Starting point`, de 3e `Reason`-kolom van `## Decisions`, `## Scope (In)`, `## Approach`, `## Acceptance criteria`, `## Verification`) weg met behoud van een 2-koloms `## Decisions` (`Question | Decision`) en `## Scope (Out)` plus een `<!-- Omitted plan sections ... -->` verwijzing (volledig opvraagbaar via `section="Decisions,Scope,..."` of `section="--all"`); en extraheert Python/JS/TS functie- en klassesignaturen of volledige AST-symbolen met `# L<start>-L<end>` regelnummers (waarbij in `--signatures` modus lange `Field(..., description="...")` strings $> 20$ tekens in functie-argumentannotaties worden ingekort tot `Field(..., description=...)` met volledig behoud van type-annotaties, `AliasChoices`, defaults en de eerste docstring-regel). Buiten frontmatter en code-fences worden volregelige HTML-commentaren (`<!-- ... -->`) weggelaten en wordt een Markdown-link `[X](Y)` exact omkeerbaar ingekort tot `Y` alleen wanneer `Y` een relatief `.md`-pad met `/` zonder spaties is en `X == ident(Y)` (`head/` + `tail` tot de eerste `-` of `.`, bv. `[bugs/01](bugs/01-x.md)` → `bugs/01-x.md`). In volledige modus (geen `section`) is de uitvoer nooit langer dan het ruwe bestand; anders wordt de ruwe tekst teruggegeven.
- **Does NOT do**: Doet **geen** lossy statistische woord-pruning (`IDF_DICT` / `prune_text`), zet tekst of identifiers nooit om naar kleine letters (`text.lower()`), vertaalt nooit naar Hanzi, doet geen netwerk-/HTTP-calls of web-scraping (dat leeft in `mcp/web-search`), en leest nooit bestanden buiten `workspace_root`.
- **May depend on**: Python stdlib (`ast`, `csv`, `io`, `json`, `re`, `pathlib`, `typing`), `fastmcp`, `pydantic`. **Must not depend on**: `mcp/web-search`, `curl_cffi`, `ddgs`, `playwright`, `trafilatura`.

## Interfaces
```python
class CompressContextInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    file_path: str = Field(validation_alias=AliasChoices("file_path", "path", "file", "filepath"), ...)
    section: str | None = None
    dsv_for_flat_lists: bool = True
    workspace_root: str | None = Field(default=None, validation_alias=AliasChoices("workspace_root", "root", "cwd"), ...)
    filter_query: str | None = Field(default=None, validation_alias=AliasChoices("filter_query", "filter", "query", "keywords"), ...)

@mcp.tool(output_schema=None)
def compress_context(
    file_path: str,
    section: str | None = None,
    dsv_for_flat_lists: bool = True,
    workspace_root: str | None = None,
    filter_query: str | None = None,
) -> str: ...
```

## Checks
- `Check: (Select-String "mcp/context-compressor/*.py" -Pattern "curl_cffi|ddgs|playwright|trafilatura|prune_text" -ErrorAction SilentlyContinue | Measure-Object).Count -> 0`
