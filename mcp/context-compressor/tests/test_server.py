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
    assert "|Column A|Column B|" in out
    assert "|-|:-:|" in out
    assert r"|a \| b|cell 4|" in out
    assert "Intro text" not in out
    assert "## Next Section" not in out
    assert "\n\n\n" not in out


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
