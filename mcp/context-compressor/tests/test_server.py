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
    assert (
        compress_context(file_path="items.csv", workspace_root=str(tmp_path))
        == "#schema:id|name|score\n1|Alpha|95\n2|Beta|88"
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

