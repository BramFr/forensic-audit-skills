# Boundaries: see MODULE.md
import contextlib
import json
import re
import sys
from pathlib import Path
from typing import Annotated, Any

with contextlib.redirect_stdout(sys.stderr):
    from fastmcp import FastMCP
    from pydantic import BaseModel, ConfigDict, Field, field_validator

mcp = FastMCP("context-compressor")

_HEADING_RE = re.compile(r"^(#{1,6})\s+(.*?)\s*#*\s*$")
_FENCE_RE = re.compile(r"^\s*(`{3,}|~{3,})")
_UNESCAPED_PIPE_RE = re.compile(r"(?<!\\)\|")
_TABLE_SEP_CELL_RE = re.compile(r"^(:?)-{2,}(:?)$")
_SCALAR_TYPES = (str, int, float, bool)


class CompressContextInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    file_path: str = Field(
        description=(
            "Relative or absolute path to a .md, .txt, or .json file inside the project workspace."
        )
    )
    section: str | None = Field(
        default=None,
        description=(
            "Optional Markdown heading name (case-insensitive substring match) to extract only that "
            "section up to the next heading of the same or higher level."
        ),
    )
    dsv_for_flat_lists: bool = Field(
        default=True,
        description=(
            "When True (default), converts flat, dense JSON lists of >= 2 scalar objects into "
            "Positional Pipe-DSV (#schema:col1|col2...) and compacts Markdown tables."
        ),
    )
    workspace_root: str | None = Field(
        default=None,
        description=(
            "Optional explicit workspace root directory. Defaults to current working directory; "
            "paths outside workspace_root are rejected."
        ),
    )

    @field_validator("file_path")
    @classmethod
    def _validate_file_path(cls, value: str) -> str:
        if not value or not value.strip():
            raise ValueError("file_path must not be empty")
        return value


def _resolve_safe_path(file_path: str, workspace_root: str | None) -> Path | None:
    """Resolve target path and verify it stays strictly within workspace_root and is a file."""
    try:
        root = Path(workspace_root).resolve() if workspace_root else Path.cwd().resolve()
        target = (root / file_path).resolve()
    except (OSError, RuntimeError, ValueError):
        return None
    if not target.is_relative_to(root) or not target.is_file():
        return None
    return target


def _is_scalar(value: Any) -> bool:
    return value is None or isinstance(value, _SCALAR_TYPES)


def _format_dsv_scalar(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, bool):
        return "true" if value else "false"
    text = str(value)
    text = text.replace("\r\n", " ").replace("\r", " ").replace("\n", " ")
    return text.replace("|", r"\|")


def _can_convert_to_pipe_dsv(data: Any) -> tuple[bool, list[str]]:
    """Check if JSON data is a flat, dense list of >= 2 non-empty scalar dicts."""
    if not isinstance(data, list) or len(data) < 2:
        return False, []

    all_keys: list[str] = []
    seen_keys: set[str] = set()

    for row in data:
        if not isinstance(row, dict) or not row:
            return False, []
        for k, v in row.items():
            if not isinstance(k, str) or not _is_scalar(v):
                return False, []
            if k not in seen_keys:
                seen_keys.add(k)
                all_keys.append(k)

    if not all_keys:
        return False, []

    total_keys = len(all_keys)
    for row in data:
        present_count = sum(
            1 for k in all_keys if k in row and row[k] is not None
        )
        if present_count / total_keys < 0.8:
            return False, []

    return True, all_keys


def _compress_json_content(raw_text: str, dsv_for_flat_lists: bool, file_path: str) -> str:
    try:
        data = json.loads(raw_text)
    except json.JSONDecodeError as exc:
        return f"ERROR: Ongeldige JSON in '{file_path}': {exc}"

    if dsv_for_flat_lists:
        eligible, all_keys = _can_convert_to_pipe_dsv(data)
        if eligible:
            header = "#schema:" + "|".join(_format_dsv_scalar(k) for k in all_keys)
            lines = [header]
            for row in data:
                lines.append(
                    "|".join(_format_dsv_scalar(row.get(k)) for k in all_keys)
                )
            return "\n".join(lines)

    return json.dumps(data, separators=(",", ":"), ensure_ascii=False)


def _extract_markdown_section(text: str, section_query: str) -> str | None:
    """Extract a Markdown heading block by case-insensitive substring match outside code fences."""
    needle = section_query.strip().casefold()
    lines = text.splitlines()

    in_fence = False
    fence_marker = ""
    start_idx: int | None = None
    target_level: int = 0

    for idx, line in enumerate(lines):
        fence_match = _FENCE_RE.match(line)
        if fence_match:
            marker = fence_match.group(1)
            if not in_fence:
                in_fence = True
                fence_marker = marker[0]
            elif marker[0] == fence_marker and len(marker) >= 3:
                in_fence = False
                fence_marker = ""
            continue

        if in_fence:
            continue

        heading_match = _HEADING_RE.match(line)
        if not heading_match:
            continue

        level = len(heading_match.group(1))
        heading_text = heading_match.group(2).strip()

        if start_idx is None:
            if needle in heading_text.casefold():
                start_idx = idx
                target_level = level
        else:
            if level <= target_level:
                return "\n".join(lines[start_idx:idx])

    if start_idx is not None:
        return "\n".join(lines[start_idx:])
    return None


def _compact_table_line(line: str) -> str:
    stripped = line.strip()
    if not (stripped.startswith("|") and stripped.endswith("|") and len(stripped) >= 2):
        return line.rstrip()

    inner = stripped[1:-1]
    raw_cells = _UNESCAPED_PIPE_RE.split(inner)
    compacted_cells: list[str] = []
    for cell in raw_cells:
        c = cell.strip()
        sep_match = _TABLE_SEP_CELL_RE.match(c)
        if sep_match:
            c = f"{sep_match.group(1)}-{sep_match.group(2)}"
        compacted_cells.append(c)
    return "|" + "|".join(compacted_cells) + "|"


def _compact_markdown_or_text(text: str, compact_tables: bool = True) -> str:
    """Compact blank lines and Markdown tables while preserving frontmatter and code fences verbatim."""
    lines = text.splitlines()
    if not lines:
        return ""

    out: list[str] = []
    idx = 0

    # Preserve YAML frontmatter at top of file verbatim
    if lines[0].strip() == "---":
        end_fm: int | None = None
        for scan_idx in range(1, len(lines)):
            if lines[scan_idx].strip() in ("---", "..."):
                end_fm = scan_idx
                break
        if end_fm is not None:
            out.extend(lines[: end_fm + 1])
            idx = end_fm + 1

    in_fence = False
    fence_char = ""
    fence_len = 0
    blank_streak = 0

    for line in lines[idx:]:
        fence_match = _FENCE_RE.match(line)
        if fence_match:
            marker = fence_match.group(1)
            if not in_fence:
                in_fence = True
                fence_char = marker[0]
                fence_len = len(marker)
            elif marker[0] == fence_char and len(marker) >= fence_len:
                in_fence = False
                fence_char = ""
                fence_len = 0
            blank_streak = 0
            out.append(line)
            continue

        if in_fence:
            out.append(line)
            continue

        if not line.strip():
            blank_streak += 1
            if blank_streak == 1:
                out.append("")
            continue

        blank_streak = 0
        if compact_tables and line.lstrip().startswith("|") and line.rstrip().endswith("|"):
            out.append(_compact_table_line(line))
        else:
            out.append(line.rstrip())

    while out and out[0] == "":
        out.pop(0)
    while out and out[-1] == "":
        out.pop()

    return "\n".join(out)


@mcp.tool()
def compress_context(
    file_path: Annotated[
        str,
        Field(
            description=(
                "Relative or absolute path to a .md, .txt, or .json file inside the project workspace."
            )
        ),
    ],
    section: Annotated[
        str | None,
        Field(
            default=None,
            description=(
                "Optional Markdown heading name (case-insensitive substring match) to extract only that "
                "section up to the next heading of the same or higher level."
            ),
        ),
    ] = None,
    dsv_for_flat_lists: Annotated[
        bool,
        Field(
            default=True,
            description=(
                "When True (default), converts flat, dense JSON lists of >= 2 scalar objects into "
                "Positional Pipe-DSV (#schema:col1|col2...) and compacts Markdown tables."
            ),
        ),
    ] = True,
    workspace_root: Annotated[
        str | None,
        Field(
            default=None,
            description=(
                "Optional explicit workspace root directory. Defaults to current working directory; "
                "paths outside workspace_root are rejected."
            ),
        ),
    ] = None,
) -> str:
    """Losslessly compress a workspace .md, .txt, or .json file for subagent context packs.

    Supports Markdown section extraction, table compaction, RFC 8259 JSON minification, and
    Positional Pipe-DSV (#schema:col1|col2...) for flat lists with N >= 2.
    """
    validated = CompressContextInput(
        file_path=file_path,
        section=section,
        dsv_for_flat_lists=dsv_for_flat_lists,
        workspace_root=workspace_root,
    )

    target = _resolve_safe_path(validated.file_path, validated.workspace_root)
    if target is None:
        return f"ERROR: Pad buiten workspace of bestand niet gevonden: '{validated.file_path}'."

    try:
        raw_text = target.read_text(encoding="utf-8")
    except Exception as exc:
        return f"ERROR: Kan bestand '{validated.file_path}' niet lezen: {exc}"

    if target.suffix.lower() == ".json":
        return _compress_json_content(
            raw_text,
            dsv_for_flat_lists=validated.dsv_for_flat_lists,
            file_path=validated.file_path,
        )

    content = raw_text
    if validated.section is not None and validated.section.strip():
        extracted = _extract_markdown_section(content, validated.section)
        if extracted is None:
            return f"ERROR: Sectie '{validated.section}' niet gevonden in '{validated.file_path}'."
        content = extracted

    return _compact_markdown_or_text(
        content, compact_tables=validated.dsv_for_flat_lists
    )


if __name__ == "__main__":
    mcp.run()
