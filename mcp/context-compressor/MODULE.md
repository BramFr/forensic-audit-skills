---
summary: Lossless MCP context-compressor (Markdown multi-sectie/frontmatter/headings/Tabel-DSV, Python/TS AST --signatures & symbolen, JSON/YAML/TOML/CSV) voor hoofdagent & subagents.
keywords: [mcp, context-compressor, lossless, ast, signatures, section-scoping, dsv, json-minification, subagent]
depends_on: []
status: done
---
# mcp/context-compressor

## Purpose
Levert een 100% lossless, deterministische FastMCP-server (`compress_context`) waarmee zowel de hoofdagent (tijdens Fase 1 Progressive Reading en Fase 2 Audits) als schone read-only en code-subagents alléén de relevante Markdown-secties (`--frontmatter`, `--headings`, `A,B,C`), Python/JS/TS AST-signaturen (`--signatures`) of specifieke functies/klassen (`func1,ClassA`), Pipe-DSV tabellen (`#schema:col1|col2...`) of geminificeerde JSON/YAML/TOML/CSV inladen zonder context rot.

## Boundaries
- **Does**: Leest `.md`, `.txt`, `.json`, `.py`, `.ts`, `.tsx`, `.js`, `.jsx`, `.yaml`, `.yml`, `.toml`, `.csv` en `.tsv` bestanden binnen de project-workspace; extraheert optioneel één of meer komma-gescheiden secties, symbolen of JSON-sleutels (`section`), `--frontmatter`, `--headings` of `--signatures`; zet Markdown-tabellen ($\ge 2$ datarijen), `.csv`/`.tsv` en vlakke JSON-lijsten (top-level én genest binnen een dict) om naar `#schema:col1|col2...` Pipe-DSV met `\|`-escaping wanneer `dsv_for_flat_lists=True`; en extraheert Python/JS/TS functie- en klassesignaturen of volledige AST-symbolen met `# L<start>-L<end>` regelnummers.
- **Does NOT do**: Doet **geen** lossy statistische woord-pruning (`IDF_DICT` / `prune_text`), zet tekst of identifiers nooit om naar kleine letters (`text.lower()`), vertaalt nooit naar Hanzi, doet geen netwerk-/HTTP-calls of web-scraping (dat leeft in `mcp/web-search`), en leest nooit bestanden buiten `workspace_root`.
- **May depend on**: Python stdlib (`ast`, `csv`, `io`, `json`, `re`, `pathlib`, `typing`), `fastmcp`, `pydantic`. **Must not depend on**: `mcp/web-search`, `curl_cffi`, `ddgs`, `playwright`, `trafilatura`.

## Interfaces
```python
class CompressContextInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    file_path: str
    section: str | None = None
    dsv_for_flat_lists: bool = True
    workspace_root: str | None = None

@mcp.tool()
def compress_context(
    file_path: str,
    section: str | None = None,
    dsv_for_flat_lists: bool = True,
    workspace_root: str | None = None,
) -> str: ...
```

## Checks
- `Check: (Select-String "mcp/context-compressor/*.py" -Pattern "curl_cffi|ddgs|playwright|trafilatura|prune_text" -ErrorAction SilentlyContinue | Measure-Object).Count -> 0`
