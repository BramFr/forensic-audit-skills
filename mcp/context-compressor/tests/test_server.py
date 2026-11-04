from pathlib import Path
import sys

import pytest
from pydantic import ValidationError

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from server import CompressContextInput, compress_context  # noqa: E402


def test_pydantic_contract_extra_forbid():
    """R6(7): Extra unknown field in CompressContextInput must raise ValidationError."""
    valid = CompressContextInput(file_path="docs/index.md", section="Compact report")
    assert valid.file_path == "docs/index.md"
    assert valid.section == "Compact report"
    assert valid.dsv_for_flat_lists is True

    with pytest.raises(ValidationError):
        CompressContextInput(file_path="docs/index.md", unknown_extra_field="rejected")

    with pytest.raises(ValidationError):
        CompressContextInput(file_path="   ")


def test_json_minification_nested_sparse_and_single_record(tmp_path: Path):
    """R6(1): Nested, sparse, or single-record JSON must be RFC 8259 minified, not Pipe-DSV."""
    single_file = tmp_path / "single.json"
    single_file.write_text(
        '[\n  {\n    "id": "R1",\n    "host": "srv-linux-01"\n  }\n]\n',
        encoding="utf-8",
    )
    out_single = compress_context(
        file_path="single.json", workspace_root=str(tmp_path)
    )
    assert out_single == '[{"id":"R1","host":"srv-linux-01"}]'

    nested_file = tmp_path / "nested.json"
    nested_file.write_text(
        '[\n  {"id": 1, "meta": {"ip": "10.0.0.15"}},\n  {"id": 2, "meta": {"ip": "10.0.0.16"}}\n]',
        encoding="utf-8",
    )
    out_nested = compress_context(
        file_path="nested.json", workspace_root=str(tmp_path)
    )
    assert out_nested == '[{"id":1,"meta":{"ip":"10.0.0.15"}},{"id":2,"meta":{"ip":"10.0.0.16"}}]'

    sparse_file = tmp_path / "sparse.json"
    sparse_file.write_text(
        '[\n  {"a": 1, "b": 2, "c": 3, "d": 4},\n  {"a": 5}\n]',
        encoding="utf-8",
    )
    out_sparse = compress_context(
        file_path="sparse.json", workspace_root=str(tmp_path)
    )
    assert out_sparse == '[{"a":1,"b":2,"c":3,"d":4},{"a":5}]'


def test_json_flat_list_to_pipe_dsv_with_escaping(tmp_path: Path):
    """R6(2): Flat dense list with N>=2 scalar records must convert to Pipe-DSV with pipe escaping."""
    flat_file = tmp_path / "hosts.json"
    flat_file.write_text(
        """[
  {
    "id": "H1",
    "hostname": "srv-linux-01",
    "ip": "10.0.0.15",
    "rule": "allow|ssh\\nport 22",
    "active": true
  },
  {
    "id": "H2",
    "hostname": "srv-linux-02",
    "ip": "10.0.0.16",
    "rule": "deny|all",
    "active": false
  }
]""",
        encoding="utf-8",
    )
    out_dsv = compress_context(
        file_path="hosts.json", workspace_root=str(tmp_path)
    )
    expected_lines = [
        "#schema:id|hostname|ip|rule|active",
        r"H1|srv-linux-01|10.0.0.15|allow\|ssh port 22|true",
        r"H2|srv-linux-02|10.0.0.16|deny\|all|false",
    ]
    assert out_dsv == "\n".join(expected_lines)

    out_minified = compress_context(
        file_path="hosts.json",
        dsv_for_flat_lists=False,
        workspace_root=str(tmp_path),
    )
    assert out_minified.startswith('[{"id":"H1","hostname":"srv-linux-01"')


def test_markdown_section_extraction_and_table_compaction(tmp_path: Path):
    """R6(3): Extract only the requested Markdown section up to the next same/higher heading."""
    md_file = tmp_path / "guide.md"
    md_file.write_text(
        """---
summary: Guide fixture
status: active
---
# Main Document

Intro text that should not be included when scoping to a section.

## Compact report

Keep CamelCaseIdentifier and https://example.org/api/v1 intact.


| Column A | Column B |
| --- | :---: |
| cell 1 | cell 2 |
| a \\| b | cell 4 |

### Sub-heading inside Compact report

Details under sub-heading.

## Next Section

This section must be excluded.
""",
        encoding="utf-8",
    )

    out = compress_context(
        file_path="guide.md",
        section="Compact report",
        workspace_root=str(tmp_path),
    )
    assert "## Compact report" in out
    assert "### Sub-heading inside Compact report" in out
    assert "Details under sub-heading." in out
    assert "#schema:Column A|Column B" in out
    assert "cell 1|cell 2" in out
    assert r"a \| b|cell 4" in out
    assert "Intro text" not in out
    assert "## Next Section" not in out
    assert "\n\n\n" not in out

    out_no_dsv = compress_context(
        file_path="guide.md",
        section="Compact report",
        dsv_for_flat_lists=False,
        workspace_root=str(tmp_path),
    )
    assert "|Column A|Column B|" in out_no_dsv
    assert "|-|:-:|" in out_no_dsv
    assert r"|a \| b|cell 4|" in out_no_dsv


def test_preservation_of_casing_identifiers_urls_ips_hosts_and_fences(tmp_path: Path):
    """R6(4): Preserve casing, CamelCase, URLs, IPs, hostnames, and code blocks."""
    md_file = tmp_path / "technical.md"
    code_block = (
        "```python\n"
        "def verifyHostConnection(hostName: str = 'srv-linux-01'):\n"
        "    # ## Compact report inside fence must not split section\n"
        "\n"
        "\n"
        "    return 'https://10.0.0.15:8443/HealthCheck'\n"
        "```"
    )
    md_file.write_text(
        f"""---
owner: SecOpsTeam
---
# Runbook

Connect to `srv-linux-01` at `10.0.0.15` via `CompressContextInput` and
https://intranet.local/StatusPage.



{code_block}
""",
        encoding="utf-8",
    )

    out = compress_context(
        file_path="technical.md", workspace_root=str(tmp_path)
    )
    assert "owner: SecOpsTeam" in out
    assert "srv-linux-01" in out
    assert "10.0.0.15" in out
    assert "CompressContextInput" in out
    assert "https://intranet.local/StatusPage" in out
    assert code_block in out


def test_opposite_path_traversal_rejected(tmp_path: Path):
    """R6(5): Path traversal outside workspace_root or missing file must fail closed with ERROR:."""
    outside_file = tmp_path.parent / "outside_secret.txt"
    outside_file.write_text("top secret", encoding="utf-8")

    out_traversal = compress_context(
        file_path="../../Windows/win.ini",
        workspace_root=str(tmp_path),
    )
    assert out_traversal.startswith("ERROR:")

    out_parent = compress_context(
        file_path="../outside_secret.txt",
        workspace_root=str(tmp_path),
    )
    assert out_parent.startswith("ERROR:")


def test_opposite_missing_section_returns_error(tmp_path: Path):
    """R6(6): Requesting a non-existent section must return an explicit ERROR: string."""
    md_file = tmp_path / "doc.md"
    md_file.write_text("# First Heading\n\nSome content.\n", encoding="utf-8")

    out = compress_context(
        file_path="doc.md",
        section="NonExistentSectionName",
        workspace_root=str(tmp_path),
    )
    assert out == "ERROR: Sectie 'NonExistentSectionName' niet gevonden in 'doc.md'."


def test_ext1_python_and_ts_ast_signatures_and_symbols(tmp_path: Path):
    """Ext1: Python AST --signatures, symbol extraction, and TS/JS support."""
    py_file = tmp_path / "sample_mod.py"
    py_file.write_text(
        '''import os
from pathlib import Path

MAX_RETRIES: int = 3


class AuditRunner( object ):
    """Runs forensic checks."""
    timeout: int = 30

    def run_check(self, target: str) -> bool:
        """Execute a check."""
        return Path(target).exists()


@staticmethod
def helper_func(x: int, y: int = 1) -> int:
    """Compute sum."""
    res = x + y


    return res
''',
        encoding="utf-8",
    )

    sig_out = compress_context(
        file_path="sample_mod.py",
        section="--signatures",
        workspace_root=str(tmp_path),
    )
    assert "import os" in sig_out
    assert "MAX_RETRIES: int = 3" in sig_out
    assert "class AuditRunner(object):" in sig_out
    assert "def run_check(self, target: str) -> bool: ..." in sig_out
    assert "def helper_func(x: int, y: int=1) -> int: ...  # Compute sum." in sig_out
    assert "res = x + y" not in sig_out

    sym_out = compress_context(
        file_path="sample_mod.py",
        section="helper_func,run_check",
        workspace_root=str(tmp_path),
    )
    assert "# L11-L13" in sym_out
    assert "return Path(target).exists()" in sym_out
    assert "# L16-L22" in sym_out
    assert "res = x + y" in sym_out
    assert "MAX_RETRIES" not in sym_out

    missing_sym = compress_context(
        file_path="sample_mod.py",
        section="non_existent_sym",
        workspace_root=str(tmp_path),
    )
    assert missing_sym.startswith("ERROR: Symbool 'non_existent_sym' niet gevonden")

    full_py = compress_context(
        file_path="sample_mod.py",
        workspace_root=str(tmp_path),
    )
    assert "\n\n\n" not in full_py

    ts_file = tmp_path / "client.ts"
    ts_file.write_text(
        """import { Request } from './http';

export interface RouteConfig {
  path: string;
  status: number;
}

export function fetchRoute(path: string): RouteConfig {
  const clean = path.trim();
  return { path: clean, status: 200 };
}
""",
        encoding="utf-8",
    )
    ts_sig = compress_context(
        file_path="client.ts",
        section="--signatures",
        workspace_root=str(tmp_path),
    )
    assert "export interface RouteConfig" in ts_sig
    assert "export function fetchRoute(path: string): RouteConfig" in ts_sig
    assert "const clean" not in ts_sig

    ts_sym = compress_context(
        file_path="client.ts",
        section="fetchRoute",
        workspace_root=str(tmp_path),
    )
    assert "# L8-L11" in ts_sym
    assert "const clean = path.trim();" in ts_sym
    assert "interface RouteConfig" not in ts_sym


def test_ext2_markdown_frontmatter_headings_and_multi_section(tmp_path: Path):
    """Ext2: --frontmatter, --headings, and comma-separated multi-section extraction."""
    md_file = tmp_path / "plan.md"
    md_file.write_text(
        """---
id: feature/08
status: in-progress
---

# Plan Title

## Why
Token savings matter.

```python
# ## Fake Heading Inside Fence
```

## Decisions
We chose AST.

## Scope
In scope: 5 items.

## Acceptance criteria
Check all tests.
""",
        encoding="utf-8",
    )

    fm_out = compress_context(
        file_path="plan.md",
        section="--frontmatter",
        workspace_root=str(tmp_path),
    )
    assert fm_out == "---\nid: feature/08\nstatus: in-progress\n---"

    hd_out = compress_context(
        file_path="plan.md",
        section="--headings",
        workspace_root=str(tmp_path),
    )
    assert "L6: # Plan Title" in hd_out
    assert "L8: ## Why" in hd_out
    assert "L18: ## Scope" in hd_out
    assert "Fake Heading Inside Fence" not in hd_out

    multi_out = compress_context(
        file_path="plan.md",
        section="Why,Acceptance criteria",
        workspace_root=str(tmp_path),
    )
    assert "## Why\nToken savings matter." in multi_out
    assert "## Acceptance criteria\nCheck all tests." in multi_out
    assert "## Decisions" not in multi_out
    assert "## Scope" not in multi_out


def test_ext3_markdown_table_to_dsv_and_single_row_fallback(tmp_path: Path):
    """Ext3: Markdown tables with >=2 data rows convert to #schema: DSV; 1-row tables stay |col|."""
    md_file = tmp_path / "tables.md"
    md_file.write_text(
        """# Tables

## Multi Row
| ID | Name | Role |
| --- | --- | --- |
| 1 | Alice | Admin |
| 2 | Bob | Auditor |

## Single Row
| Key | Value |
| --- | --- |
| env | prod |
""",
        encoding="utf-8",
    )
    out = compress_context(file_path="tables.md", workspace_root=str(tmp_path))
    assert "#schema:ID|Name|Role\n1|Alice|Admin\n2|Bob|Auditor" in out
    assert "|Key|Value|\n|-|-|\n|env|prod|" in out


def test_ext4_nested_json_csv_tsv_yaml_toml(tmp_path: Path):
    """Ext4: JSON section filtering, nested dict flat-list DSV, CSV/TSV to DSV, and YAML/TOML compaction."""
    inv_file = tmp_path / "inventory.json"
    inv_file.write_text(
        """{
  "version": "1.0",
  "routes": [
    {"path": "/login", "status": 200},
    {"path": "/admin", "status": 403}
  ]
}""",
        encoding="utf-8",
    )

    out_routes = compress_context(
        file_path="inventory.json",
        section="routes",
        workspace_root=str(tmp_path),
    )
    assert out_routes == "#schema:path|status\n/login|200\n/admin|403"

    out_full_inv = compress_context(
        file_path="inventory.json",
        workspace_root=str(tmp_path),
    )
    assert "#key:routes\n#schema:path|status\n/login|200\n/admin|403" in out_full_inv

    out_bad_key = compress_context(
        file_path="inventory.json",
        section="missing_key",
        workspace_root=str(tmp_path),
    )
    assert out_bad_key.startswith("ERROR: Sleutel 'missing_key' niet gevonden")

    csv_file = tmp_path / "items.csv"
    csv_file.write_text("id,name,score\n1,Alpha,95\n2,Beta,88\n", encoding="utf-8")
    # L4: unquoted CSV DSV would be longer than raw, so the raw text is returned verbatim.
    assert (
        compress_context(file_path="items.csv", workspace_root=str(tmp_path))
        == "id,name,score\n1,Alpha,95\n2,Beta,88\n"
    )

    quoted_csv = tmp_path / "quoted.csv"
    quoted_csv.write_text(
        '"id","name","score"\n"1","Alpha Beta","95"\n"2","Gamma","88"\n', encoding="utf-8"
    )
    assert (
        compress_context(file_path="quoted.csv", workspace_root=str(tmp_path))
        == "#schema:id|name|score\n1|Alpha Beta|95\n2|Gamma|88"
    )

    toml_file = tmp_path / "pyproject.toml"
    toml_file.write_text(
        """# Full line comment
[project]
name = "demo"


version = "0.1.0"

[tool.pytest]
addopts = "-q"
""",
        encoding="utf-8",
    )
    out_toml = compress_context(
        file_path="pyproject.toml",
        section="project",
        workspace_root=str(tmp_path),
    )
    assert out_toml == '[project]\nname = "demo"\n\nversion = "0.1.0"'
    assert "# Full line comment" not in out_toml


# --- feature/10: structured output, reversible link compaction (L3), never-larger guard (L4) ---

import asyncio  # noqa: E402
import re  # noqa: E402

import fastmcp  # noqa: E402

from server import _link_ident, mcp  # noqa: E402

_REVERSE_RE = re.compile(r"(?<![\[(\w/.-])[A-Za-z0-9_]+(?:/[A-Za-z0-9_.-]+)+\.md(?![\])\w])")


def _reverse_links(text: str) -> str:
    """Benchmark reverse step: bare doc path P -> [ident(P)](P)."""
    return _REVERSE_RE.sub(lambda m: f"[{_link_ident(m.group(0))}]({m.group(0)})", text)


def test_l1_tool_call_has_no_structured_content(tmp_path: Path):
    """L1: tool result is text-only (no duplicated structuredContent) and equals direct output."""
    md = tmp_path / "doc.md"
    md.write_text("# Title\n\n\nSome text.\n", encoding="utf-8")
    args = {"file_path": "doc.md", "workspace_root": str(tmp_path)}

    async def _call():
        async with fastmcp.Client(mcp) as client:
            return await client.call_tool("compress_context", args)

    result = asyncio.run(_call())
    assert result.structured_content is None
    assert result.content[0].text == compress_context(**args)


def test_l3_index_table_link_compacted_and_reversible(tmp_path: Path):
    """L3: '[bugs/01](bugs/01-x.md)' becomes 'bugs/01-x.md' and the reverse rebuilds the row."""
    row = "| [bugs/01](bugs/01-x.md) | Fix search keywords | done |"
    md = tmp_path / "index.md"
    md.write_text(row + "\n", encoding="utf-8")
    out = compress_context(file_path="index.md", workspace_root=str(tmp_path))
    assert "bugs/01-x.md" in out
    assert "[bugs/01]" not in out
    assert _reverse_links("bugs/01-x.md") == "[bugs/01](bugs/01-x.md)"
    assert _reverse_links(out) == out.replace("bugs/01-x.md", "[bugs/01](bugs/01-x.md)")

    line = "See [feature/10](feature/10-x.md) for details."
    (tmp_path / "p.md").write_text(line + "\n", encoding="utf-8")
    out2 = compress_context(file_path="p.md", workspace_root=str(tmp_path))
    assert out2 == "See feature/10-x.md for details."
    assert _reverse_links(out2) == line


def test_l3_opposite_links_left_unchanged(tmp_path: Path):
    """L3 opposite: non-ident labels, http links, frontmatter and fenced code stay verbatim."""
    keep_lines = [
        "Module: [mcp/context-compressor](../mcp/context-compressor/MODULE.md)",
        "Index: [docs](docs/index.md)",
        "Web: [bugs/01](https://example.com/bugs/01-x.md)",
    ]
    text = (
        "---\n"
        "link: [bugs/01](bugs/01-x.md)\n"
        "---\n"
        + "\n".join(keep_lines)
        + "\n\n```\n[bugs/01](bugs/01-x.md)\n```\n"
    )
    (tmp_path / "o.md").write_text(text, encoding="utf-8")
    out = compress_context(file_path="o.md", workspace_root=str(tmp_path))
    for kl in keep_lines:
        assert kl in out
    assert "link: [bugs/01](bugs/01-x.md)" in out
    assert "```\n[bugs/01](bugs/01-x.md)\n```" in out


def test_l4_full_mode_never_larger_than_raw_for_repo_files():
    """L4: full-file output is never longer than the raw file for every supported repo file."""
    repo_root = Path(__file__).resolve().parents[3]
    exts = {".md", ".txt", ".json", ".py", ".ts", ".tsx", ".js", ".jsx",
            ".yaml", ".yml", ".toml", ".csv", ".tsv"}
    skip = {".venv", ".git", "__pycache__", ".pytest_cache", "node_modules"}
    checked = 0
    for p in repo_root.rglob("*"):
        if not p.is_file() or p.suffix.lower() not in exts:
            continue
        if any(part in skip for part in p.relative_to(repo_root).parts):
            continue
        try:
            raw = p.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        out = compress_context(file_path=str(p), workspace_root=str(repo_root))
        if out.startswith("ERROR:"):
            continue
        assert len(out) <= len(raw), f"{p} grew: {len(out)} > {len(raw)}"
        checked += 1
    assert checked > 0


def test_alias_choices_path_and_root_and_opposite_unknown_rejected(tmp_path: Path):
    """bugs/05: compress_context accepts path/file/filepath and root/cwd aliases via FastMCP without schema bloat, while rejecting unknown keys and empty paths."""
    from fastmcp.exceptions import ToolError
    import pytest

    from server import CompressContextInput

    md = tmp_path / "doc.md"
    md.write_text("# Header\n\n\nBody line.\n", encoding="utf-8")

    m = CompressContextInput.model_validate({"path": "doc.md", "root": str(tmp_path)})
    assert m.file_path == "doc.md"
    assert m.workspace_root == str(tmp_path)

    expected = compress_context(file_path="doc.md", workspace_root=str(tmp_path))

    async def _run():
        async with fastmcp.Client(mcp) as client:
            tools = await client.list_tools()
            tool = next(t for t in tools if t.name == "compress_context")
            schema = tool.input_schema if hasattr(tool, "input_schema") else tool.inputSchema
            assert schema["required"] == ["file_path"]
            assert schema.get("additionalProperties") is False
            assert set(schema["properties"].keys()) == {
                "file_path",
                "section",
                "dsv_for_flat_lists",
                "workspace_root",
                "filter_query",
            }

            r1 = await client.call_tool(
                "compress_context",
                {"path": "doc.md", "root": str(tmp_path)},
            )
            assert r1.content[0].text == expected

            r2 = await client.call_tool(
                "compress_context",
                {"file": "doc.md", "cwd": str(tmp_path)},
            )
            assert r2.content[0].text == expected

            r3 = await client.call_tool(
                "compress_context",
                {"filepath": "doc.md", "workspace_root": str(tmp_path)},
            )
            assert r3.content[0].text == expected

            with pytest.raises(ToolError):
                await client.call_tool("compress_context", {"bogus": "x"})

            with pytest.raises(ToolError):
                await client.call_tool("compress_context", {"path": "   "})

    asyncio.run(_run())


def test_feature18_signatures_field_description_ellipsis_and_opposite_symbol_verbatim(tmp_path: Path):
    """feature/18: --signatures replaces Field(..., description='< >20 chars >') in arg annotations with description=..., while keeping short descriptions, AliasChoices, defaults, first docstring line, and full symbol extraction verbatim (opposite test)."""
    py_file = tmp_path / "tool_mod.py"
    py_file.write_text(
        '''from typing import Annotated
from pydantic import AliasChoices, Field


def sample_tool(
    query_or_url: Annotated[
        str,
        Field(
            default="",
            validation_alias=AliasChoices("query_or_url", "query"),
            description="Very long tool argument description that exceeds twenty characters easily.",
        ),
    ] = "",
    short_arg: Annotated[
        int,
        Field(default=5, description="Short desc"),
    ] = 5,
) -> str:
    """First docstring line stays intact."""
    return query_or_url
''',
        encoding="utf-8",
    )

    sig_out = compress_context(
        file_path="tool_mod.py",
        section="--signatures",
        workspace_root=str(tmp_path),
    )
    assert "description=..." in sig_out
    assert "Very long tool argument description" not in sig_out
    assert "AliasChoices('query_or_url', 'query')" in sig_out
    assert "description='Short desc'" in sig_out
    assert "# First docstring line stays intact." in sig_out

    # Opposite test: explicit symbol extraction keeps full Field description verbatim
    sym_out = compress_context(
        file_path="tool_mod.py",
        section="sample_tool",
        workspace_root=str(tmp_path),
    )
    assert "Very long tool argument description that exceeds twenty characters easily." in sym_out


def test_feature18_strip_html_comments_outside_fences_and_preserve_inside_fences(tmp_path: Path):
    """feature/18: Full-line HTML comments outside fences/frontmatter are stripped and Tags commas compacted, while comments inside fences/frontmatter remain intact (opposite test)."""
    md_file = tmp_path / "index_sample.md"
    md_file.write_text(
        """---
note: <!-- keep frontmatter comment -->
---
# Docs index

## Items
<!-- INDEX:START -->
| ID | Status | Tags |
| --- | --- | --- |
| [bugs/01](bugs/01-fix.md) | done | mcp, web-search, bugfix |
| [feature/18](feature/18-bench.md) | in-progress | mcp, token-efficiency, dry |
<!-- INDEX:END -->

```html
<!-- keep fenced comment -->
```
""",
        encoding="utf-8",
    )
    out = compress_context(
        file_path="index_sample.md",
        section="Items",
        workspace_root=str(tmp_path),
    )
    assert "<!-- INDEX:START -->" not in out
    assert "<!-- INDEX:END -->" not in out
    assert "bugs/01-fix.md|done|mcp,web-search,bugfix" in out
    assert "feature/18-bench.md|in-progress|mcp,token-efficiency,dry" in out

    full_out = compress_context(
        file_path="index_sample.md",
        workspace_root=str(tmp_path),
    )
    assert "note: <!-- keep frontmatter comment -->" in full_out
    assert "<!-- keep fenced comment -->" in full_out
    assert "<!-- INDEX:START -->" not in full_out


def test_feature19_tiered_table_filter_query_and_index_budget(tmp_path: Path):
    """feature/19: filter_query projects non-matching rows in >=4-col tables to first 3 cols while keeping full 5 cols for matching rows and leaving non-table sections untouched; repo docs/index.md stays <= 10,240 B."""
    idx_file = tmp_path / "index.md"
    idx_file.write_text(
        """# Docs index

## Product vision
Zero-trust verification engine.

## Search keywords
[zero-trust, forensic-audit, sqlite-wal, rfc-9111]

## Items
| ID | Status | Title | Summary | Tags |
| --- | --- | --- | --- | --- |
| [bugs/01](bugs/01-fix.md) | done | Fix search keywords | Long unrelated summary about search keywords in tool schema | planner, bugfix |
| [feature/19](feature/19-sqlite.md) | in-progress | SQLite WAL cache & slim plan | Persistent sqlite3 WAL cache with RFC 9111 ETag revalidation | mcp, sqlite-wal, rfc-9111 |
""",
        encoding="utf-8",
    )
    filtered = compress_context(
        file_path="index.md",
        section="Product vision,Search keywords,Items",
        filter_query="sqlite wal",
        workspace_root=str(tmp_path),
    )
    assert "Zero-trust verification engine." in filtered
    assert "[zero-trust,forensic-audit,sqlite-wal,rfc-9111]" in filtered
    # Non-matching row projected to first 3 columns (ID|Status|Title)
    assert "bugs/01|done|Fix search keywords\n" in filtered
    assert "Long unrelated summary" not in filtered
    # Matching row retains all 5 columns
    assert (
        "feature/19|in-progress|SQLite WAL cache & slim plan|"
        "Persistent sqlite3 WAL cache with RFC 9111 ETag revalidation|mcp,sqlite-wal,rfc-9111"
        in filtered
    )

    # Repo docs/index.md 4-section budget check without filter_query must stay <= 10,240 B
    repo_root = Path(__file__).resolve().parents[3]
    repo_index = compress_context(
        file_path="docs/index.md",
        section="Product vision,Search keywords,Items,Modules",
        workspace_root=str(repo_root),
    )
    assert len(repo_index.encode("utf-8")) <= 10240


def test_feature19_slim_plan_read_by_default_and_opposite_non_plan_or_all_intact(tmp_path: Path):
    """feature/19: Reading a plan .md file with section=None automatically omits Starting point, Decisions, Scope, Approach, Acceptance criteria & Verification while keeping frontmatter, Why, Risks and Relations; section='Scope,Acceptance criteria' or section='--all' returns them in full, and non-plan .md files stay untouched (opposite test)."""
    plan_file = tmp_path / "19-sample-plan.md"
    plan_file.write_text(
        """---
id: feature/19
title: Sample Plan
category: feature
status: in-progress
summary: Slim plan read test
---

# Sample Plan

## Why
Eliminate 88% token bloat on full plan reads.

## Starting point (audit findings)
Heavy audit details that should be omitted on default section=None read.

## Decisions
Heavy grill table that should be omitted on default read.

## Scope
In scope: context-compressor and web-search.

## Approach
Step 1, Step 2, Step 3.

## Acceptance criteria
- [ ] All tests pass.

## Verification
Verified via pytest.

## Risks and open points
On-demand section loading remains 100% lossless.

## Relations
Related to feature/18.
""",
        encoding="utf-8",
    )

    slim_out = compress_context(
        file_path="19-sample-plan.md",
        workspace_root=str(tmp_path),
    )
    assert "id: feature/19" in slim_out
    assert "## Why\nEliminate 88% token bloat on full plan reads." in slim_out
    assert "## Risks and open points\nOn-demand section loading remains 100% lossless." in slim_out
    assert "## Relations\nRelated to feature/18." in slim_out
    assert "Heavy audit details" not in slim_out
    assert "Heavy grill table" not in slim_out
    assert "In scope: context-compressor" not in slim_out
    assert "Step 1, Step 2, Step 3." not in slim_out
    assert "All tests pass." not in slim_out
    assert "Verified via pytest." not in slim_out
    assert "<!-- Omitted plan sections" in slim_out

    # Explicit section extraction returns requested heavy sections in full
    scoped_out = compress_context(
        file_path="19-sample-plan.md",
        section="Scope,Acceptance criteria",
        workspace_root=str(tmp_path),
    )
    assert "In scope: context-compressor and web-search." in scoped_out
    assert "- [ ] All tests pass." in scoped_out

    # section="--all" returns all sections in full
    all_out = compress_context(
        file_path="19-sample-plan.md",
        section="--all",
        workspace_root=str(tmp_path),
    )
    assert "Heavy audit details" in all_out
    assert "In scope: context-compressor and web-search." in all_out
    assert "- [ ] All tests pass." in all_out
    assert "<!-- Omitted plan sections" not in all_out

    # Opposite test: non-plan .md file with section="Scope" heading keeps everything when section=None
    regular_md = tmp_path / "SKILL.md"
    regular_md.write_text(
        """---
name: sample-skill
description: Not a plan document
---
# Skill Guide

## Scope
This Scope section in a non-plan file must never be omitted!

## Approach
This Approach section in a non-plan file must also stay intact!
""",
        encoding="utf-8",
    )
    reg_out = compress_context(
        file_path="SKILL.md",
        workspace_root=str(tmp_path),
    )
    assert "This Scope section in a non-plan file must never be omitted!" in reg_out
    assert "This Approach section in a non-plan file must also stay intact!" in reg_out
    assert "<!-- Omitted plan sections" not in reg_out


def test_bugs06_slim_plan_keeps_2col_decisions_and_scope_out(tmp_path: Path):
    """bugs/06: Default slim plan-read (section=None) keeps 2-column Decisions (Question | Decision without Reason) and Scope (Out) while omitting Scope (In), Starting point, Approach, Acceptance criteria & Verification."""
    plan_file = tmp_path / "06-commitments-plan.md"
    plan_file.write_text(
        """---
id: bugs/06
title: Commitment Preservation Plan
category: bugs
status: in-progress
summary: Keep Decisions and Scope Out in slim plan reads
---

# Commitment Preservation Plan

## Why
Prevent re-proposing rejected patterns like mouse 3D tilt.

## Starting point (audit findings)
Heavy audit findings that should be omitted in slim mode.

## Decisions (from the grill)
| Question | Decision | Reason (incl. 2 pros & 2 cons) |
| --- | --- | --- |
| 1. Mouse 3D tilt? | **0% mouse influence (Keyboard-Only)** | +Pro 1: Zero style invalidation. +Pro 2: No motion sickness. -Con 1: None. -Con 2: None. |
| 2. Frame rotation? | **0deg upright frames** | +Pro 1: Maximum legibility at 5m. +Pro 2: Full 2x2 stage fill. -Con 1: None. -Con 2: None. |

## Scope
- **In**:
  - Update context-compressor and planner skill.
- **Out (explicitly not doing)**:
  - No mousemove 3D tilt or wheel scroll in presentation slides.
  - No -16deg frame rotation during reading.

## Approach
1. Step 1
2. Step 2

## Acceptance criteria
- [ ] All checks pass.
""",
        encoding="utf-8",
    )

    slim_out = compress_context(
        file_path="06-commitments-plan.md",
        workspace_root=str(tmp_path),
    )
    assert "## Decisions" in slim_out
    assert "1. Mouse 3D tilt?" in slim_out
    assert "**0% mouse influence (Keyboard-Only)**" in slim_out
    assert "2. Frame rotation?" in slim_out
    assert "**0deg upright frames**" in slim_out
    assert "Zero style invalidation" not in slim_out
    assert "No motion sickness" not in slim_out

    assert "## Scope" in slim_out
    assert "- **Out (explicitly not doing)**:" in slim_out
    assert "No mousemove 3D tilt or wheel scroll in presentation slides." in slim_out
    assert "No -16deg frame rotation during reading." in slim_out
    assert "Update context-compressor and planner skill." not in slim_out
    assert "Decisions (Reason)" in slim_out
    assert "Scope (In)" in slim_out

    # Explicit section="Decisions,Scope" and section="--all" still return 100% of Reason and In items
    full_sec = compress_context(
        file_path="06-commitments-plan.md",
        section="Decisions,Scope",
        workspace_root=str(tmp_path),
    )
    assert "Zero style invalidation" in full_sec
    assert "Update context-compressor and planner skill." in full_sec

    full_all = compress_context(
        file_path="06-commitments-plan.md",
        section="--all",
        workspace_root=str(tmp_path),
    )
    assert "Zero style invalidation" in full_all
    assert "Update context-compressor and planner skill." in full_all
    assert "Heavy audit findings" in full_all


def test_feature20_exact_vs_substring_heading_priority_and_range_deduplication(tmp_path: Path):
    """feature/20: Exact/prefix heading match takes priority over substring match, comma-containing headings and overlapping/nested multi-section ranges are deduplicated, and repo skill section reads stay <= 10,240 B."""
    doc = tmp_path / "skill_sample.md"
    doc.write_text(
        """# First-Principles Architect

Intro under top-level H1 that contains the substring 'Principles' in its title.

## Phase 0: Principles research (always, whatever the request)

Phase 0 normative instructions line 1.

### Sub-step inside Phase 0

Nested sub-step line 2.

## Principles

Exact H2 Principles section body.
""",
        encoding="utf-8",
    )

    # 1. Exact heading match priority: 'Principles' matches '## Principles', NOT '# First-Principles Architect'
    out_exact = compress_context(
        file_path="skill_sample.md",
        section="Principles",
        workspace_root=str(tmp_path),
    )
    assert "## Principles" in out_exact
    assert "Exact H2 Principles section body." in out_exact
    assert "# First-Principles Architect" not in out_exact
    assert "Intro under top-level H1" not in out_exact

    # 2. Heading containing a comma is not duplicated when split by ','
    out_comma = compress_context(
        file_path="skill_sample.md",
        section="Phase 0: Principles research (always, whatever the request)",
        workspace_root=str(tmp_path),
    )
    assert out_comma.count("## Phase 0: Principles research (always, whatever the request)") == 1
    assert out_comma.count("Phase 0 normative instructions line 1.") == 1

    # 3. Overlapping / nested sections ('Phase 0, Sub-step inside Phase 0') are merged without duplicate lines
    out_nested = compress_context(
        file_path="skill_sample.md",
        section="Phase 0,Sub-step inside Phase 0",
        workspace_root=str(tmp_path),
    )
    assert out_nested.count("Nested sub-step line 2.") == 1
    assert "## Principles" not in out_nested

    # 4. Opposite check: substring fallback still works when no exact/prefix match exists
    out_sub = compress_context(
        file_path="skill_sample.md",
        section="whatever the request",
        workspace_root=str(tmp_path),
    )
    assert "## Phase 0: Principles research (always, whatever the request)" in out_sub

    # 5. Repo skill section reads stay strictly <= 10,240 B
    repo_root = Path(__file__).resolve().parents[3]
    fa_sec = compress_context(
        file_path="skills/forensic-audit/SKILL.md",
        section="Principles,Pre-build use (principles research)",
        workspace_root=str(repo_root),
    )
    fpa_sec = compress_context(
        file_path="skills/first-principles-architect/SKILL.md",
        section="Phase 0: Principles research (always, whatever the request)",
        workspace_root=str(repo_root),
    )
    assert len(fa_sec.encode("utf-8")) <= 10240
    assert len(fpa_sec.encode("utf-8")) <= 10240
    assert fpa_sec.count("## Phase 0: Principles research (always, whatever the request)") == 1

