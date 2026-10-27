---
summary: Lossless MCP context-compressor (Markdown-secties, RFC 8259 JSON-minificatie en Pipe-DSV vanaf N>=2) voor subagents.
keywords: [mcp, context-compressor, lossless, section-scoping, dsv, json-minification, subagent]
depends_on: []
status: done
---
# mcp/context-compressor

## Purpose
Levert een 100% lossless, deterministische FastMCP-server (`compress_context`) waarmee een hoofdagent alléén de relevante Markdown-sectie, compacte tabellen (Pipe-DSV vanaf $N \ge 2$ vlakke rijen) of geminificeerde JSON (`separators=(',',':')`) klaarzet voor een schone code-subagent zonder context rot.

## Boundaries
- **Does**: Leest `.md`, `.txt` en `.json` bestanden binnen de project-workspace; extraheert optioneel één specifieke Markdown-sectie op kopnaam (`section`); compacteert witruimte en Markdown-tabellen zonder codeblokken, inline-code, URL's, paden of hoofdletters aan te tasten; minificeert `.json` volgens RFC 8259 en zet vlakke, dense lijsten vanaf $N \ge 2$ records om naar `#schema:col1|col2...` Pipe-DSV met `\|`-escaping.
- **Does NOT do**: Doet **geen** lossy statistische woord-pruning (`IDF_DICT` / `prune_text`), zet tekst of identifiers nooit om naar kleine letters (`text.lower()`), vertaalt nooit naar Hanzi, doet geen netwerk-/HTTP-calls of web-scraping (dat leeft in `mcp/web-search`), en leest nooit bestanden buiten `workspace_root`.
- **May depend on**: Python stdlib (`json`, `re`, `pathlib`, `typing`), `fastmcp`, `pydantic`. **Must not depend on**: `mcp/web-search`, `curl_cffi`, `ddgs`, `playwright`, `trafilatura`.

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
