# Boundaries: see MODULE.md
import ast
import contextlib
import csv
import io
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
_CODE_EXTENSIONS = {".py", ".ts", ".tsx", ".js", ".jsx"}
_JS_TS_SIG_RE = re.compile(
    r"^\s*(?:export\s+(?:default\s+)?)?(?:import\s+|interface\s+\w+|type\s+\w+|(?:abstract\s+)?class\s+\w+|(?:async\s+)?function\s+\w+|(?:const|let|var)\s+\w+\s*(?::[^=]+)?=\s*(?:async\s*)?(?:\([^)]*\)|[A-Za-z_$][\w$]*)\s*=>)"
)
_JS_TS_METHOD_RE = re.compile(
    r"^\s{2,4}(?:(?:public|private|protected|static|readonly|async|override)\s+)*(?:get\s+|set\s+)?([A-Za-z_$][\w$]*)\s*(?:<[^>]*>)?\s*\([^;]*\)\s*(?::\s*[^{;]+)?\s*\{"
)


class CompressContextInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    file_path: str = Field(
        description=(
            "Relative or absolute path to a .md, .txt, .json, .py, .ts, .tsx, .js, .jsx, .yaml, .yml, .toml, .csv, or .tsv file inside the project workspace."
        )
    )
    section: str | None = Field(
        default=None,
        description=(
            "Optional selector: for .md/.txt use '--frontmatter', '--headings', or one/more comma-separated heading names ('Why,Scope'); "
            "for .py/.ts/.js use '--signatures' ('--outline') or comma-separated symbol names ('func1,ClassA'); "
            "for .json/.yaml/.toml use comma-separated top-level keys ('routes,version')."
        ),
    )
    dsv_for_flat_lists: bool = Field(
        default=True,
        description=(
            "When True (default), converts flat, dense JSON lists (top-level or nested under dict keys), "
            "Markdown tables (>= 2 data rows), and .csv/.tsv files into Positional Pipe-DSV (#schema:col1|col2...)."
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


def _list_to_pipe_dsv(data: list[dict[str, Any]], all_keys: list[str]) -> str:
    header = "#schema:" + "|".join(_format_dsv_scalar(k) for k in all_keys)
    lines = [header]
    for row in data:
        lines.append(
            "|".join(_format_dsv_scalar(row.get(k)) for k in all_keys)
        )
    return "\n".join(lines)


def _compress_json_content(
    raw_text: str,
    dsv_for_flat_lists: bool,
    file_path: str,
    section: str | None = None,
) -> str:
    try:
        data = json.loads(raw_text)
    except json.JSONDecodeError as exc:
        return f"ERROR: Ongeldige JSON in '{file_path}': {exc}"

    if section is not None and section.strip():
        if not isinstance(data, dict):
            return f"ERROR: Sectie-extractie op JSON vereist een JSON-object in '{file_path}'."
        req_keys = [k.strip() for k in section.split(",") if k.strip()]
        resolved_keys: list[str] = []
        lower_map = {k.casefold(): k for k in data.keys() if isinstance(k, str)}
        for rk in req_keys:
            if rk in data:
                resolved_keys.append(rk)
            elif rk.casefold() in lower_map:
                resolved_keys.append(lower_map[rk.casefold()])
            else:
                return f"ERROR: Sleutel '{rk}' niet gevonden in '{file_path}'."

        if len(resolved_keys) == 1:
            single_val = data[resolved_keys[0]]
            if isinstance(single_val, (list, dict)):
                data = single_val
            else:
                data = {resolved_keys[0]: single_val}
        else:
            data = {k: data[k] for k in resolved_keys}

    if dsv_for_flat_lists:
        eligible, all_keys = _can_convert_to_pipe_dsv(data)
        if eligible:
            return _list_to_pipe_dsv(data, all_keys)

        if isinstance(data, dict) and data:
            nested_dsv: dict[str, tuple[bool, list[str]]] = {}
            any_nested_eligible = False
            for k, v in data.items():
                ok, keys = _can_convert_to_pipe_dsv(v)
                nested_dsv[k] = (ok, keys)
                if ok:
                    any_nested_eligible = True

            if any_nested_eligible:
                if len(data) == 1:
                    only_key = next(iter(data.keys()))
                    _, keys = nested_dsv[only_key]
                    return f"#key:{only_key}\n{_list_to_pipe_dsv(data[only_key], keys)}"
                blocks: list[str] = []
                for k, v in data.items():
                    ok, keys = nested_dsv[k]
                    if ok:
                        blocks.append(f"#key:{k}\n{_list_to_pipe_dsv(v, keys)}")
                    else:
                        blocks.append(
                            f"#key:{k}\n{json.dumps(v, separators=(',', ':'), ensure_ascii=False)}"
                        )
                return "\n".join(blocks)

    return json.dumps(data, separators=(",", ":"), ensure_ascii=False)


def _compress_csv_or_tsv(raw_text: str, delimiter: str, dsv_for_flat_lists: bool) -> str:
    reader = csv.reader(io.StringIO(raw_text), delimiter=delimiter)
    rows = [row for row in reader if any(cell.strip() for cell in row)]
    if not rows:
        return ""
    if dsv_for_flat_lists and len(rows) >= 2:
        header = "#schema:" + "|".join(_format_dsv_scalar(c.strip()) for c in rows[0])
        out_lines = [header]
        for row in rows[1:]:
            out_lines.append("|".join(_format_dsv_scalar(c.strip()) for c in row))
        return "\n".join(out_lines)
    return "\n".join("|".join(_format_dsv_scalar(c.strip()) for c in row) for row in rows)


def _compress_yaml_or_toml(raw_text: str, section: str | None, file_path: str) -> str:
    lines = raw_text.splitlines()
    if section is not None and section.strip():
        req_sections = [s.strip() for s in section.split(",") if s.strip()]
        extracted_blocks: list[str] = []
        for req in req_sections:
            needle = req.casefold()
            block_lines: list[str] = []
            capturing = False
            mode = ""
            for line in lines:
                stripped = line.strip()
                if not stripped or stripped.startswith("#"):
                    if capturing:
                        block_lines.append(line.rstrip())
                    continue
                # TOML [section] or [[section]]
                if stripped.startswith("[") and stripped.endswith("]"):
                    hdr = stripped.strip("[]").strip().casefold()
                    if hdr == needle or hdr.startswith(needle + "."):
                        capturing = True
                        mode = "toml"
                        block_lines.append(line.rstrip())
                        continue
                    elif capturing and mode == "toml":
                        break
                # Top-level YAML/TOML key
                if not line[0].isspace() and ":" in line:
                    key_name = line.split(":", 1)[0].strip().casefold()
                    if key_name == needle:
                        capturing = True
                        mode = "yaml"
                        block_lines.append(line.rstrip())
                        continue
                    elif capturing and mode == "yaml":
                        break
                elif not line[0].isspace() and "=" in line and not stripped.startswith("["):
                    key_name = line.split("=", 1)[0].strip().casefold()
                    if key_name == needle and not capturing:
                        block_lines.append(line.rstrip())
                        break
                if capturing:
                    block_lines.append(line.rstrip())
            if block_lines:
                extracted_blocks.append("\n".join(block_lines).strip())
        if not extracted_blocks:
            return f"ERROR: Sectie '{section}' niet gevonden in '{file_path}'."
        lines = "\n\n".join(extracted_blocks).splitlines()

    out: list[str] = []
    blank_streak = 0
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("#"):
            continue
        if not stripped:
            blank_streak += 1
            if blank_streak == 1:
                out.append("")
            continue
        blank_streak = 0
        out.append(line.rstrip())

    while out and out[0] == "":
        out.pop(0)
    while out and out[-1] == "":
        out.pop()
    return "\n".join(out)


def _format_py_func_sig(node: ast.FunctionDef | ast.AsyncFunctionDef, indent: str = "", include_line_range: bool = True) -> list[str]:
    res: list[str] = []
    start_line = min([node.lineno] + [d.lineno for d in node.decorator_list])
    end_line = node.end_lineno or node.lineno
    for d in node.decorator_list:
        res.append(f"{indent}@{ast.unparse(d)}")
    if include_line_range:
        res.append(f"{indent}# L{start_line}-L{end_line}")
    prefix = "async def " if isinstance(node, ast.AsyncFunctionDef) else "def "
    args_str = ast.unparse(node.args)
    ret_str = f" -> {ast.unparse(node.returns)}" if node.returns else ""
    doc = ast.get_docstring(node)
    first_doc = doc.splitlines()[0].strip() if doc and doc.splitlines() else ""
    if include_line_range:
        comment = f"  # {first_doc}" if first_doc else ""
    else:
        comment = f"  # L{start_line}-L{end_line}" + (f": {first_doc}" if first_doc else "")
    res.append(f"{indent}{prefix}{node.name}({args_str}){ret_str}: ...{comment}")
    return res


def _extract_python_code(raw_text: str, section: str | None, file_path: str) -> str:
    lines = raw_text.splitlines()
    try:
        tree = ast.parse(raw_text)
    except SyntaxError:
        return _extract_js_ts_code(raw_text, section, file_path)

    if section is None or not section.strip():
        multiline_str_lines: set[int] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Constant) and isinstance(node.value, str):
                start = getattr(node, "lineno", None)
                end = getattr(node, "end_lineno", None)
                if start and end and end > start:
                    multiline_str_lines.update(range(start + 1, end + 1))

        out: list[str] = []
        blank_streak = 0
        for idx, line in enumerate(lines, start=1):
            if idx in multiline_str_lines:
                blank_streak = 0
                out.append(line)
                continue
            if not line.strip():
                blank_streak += 1
                if blank_streak == 1:
                    out.append("")
                continue
            blank_streak = 0
            out.append(line.rstrip())
        while out and out[0] == "":
            out.pop(0)
        while out and out[-1] == "":
            out.pop()
        return "\n".join(out)

    sec_clean = section.strip()
    if sec_clean in ("--signatures", "--outline"):
        out_sig: list[str] = []
        for node in tree.body:
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                seg = "\n".join(lines[node.lineno - 1 : (node.end_lineno or node.lineno)]).strip()
                out_sig.append(seg)
            elif isinstance(node, (ast.Assign, ast.AnnAssign)):
                seg = "\n".join(lines[node.lineno - 1 : (node.end_lineno or node.lineno)]).strip()
                if "\n" not in seg and len(seg) <= 100:
                    out_sig.append(seg)
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                out_sig.extend(_format_py_func_sig(node, indent="", include_line_range=True))
            elif isinstance(node, ast.ClassDef):
                start_line = min([node.lineno] + [d.lineno for d in node.decorator_list])
                end_line = node.end_lineno or node.lineno
                for d in node.decorator_list:
                    out_sig.append(f"@{ast.unparse(d)}")
                out_sig.append(f"# L{start_line}-L{end_line}")
                bases_list = [ast.unparse(b) for b in node.bases] + [
                    f"{kw.arg}={ast.unparse(kw.value)}" if kw.arg else f"**{ast.unparse(kw.value)}"
                    for kw in node.keywords
                ]
                bases_str = f"({', '.join(bases_list)})" if bases_list else ""
                out_sig.append(f"class {node.name}{bases_str}:")
                has_items = False
                doc = ast.get_docstring(node)
                if doc and doc.splitlines():
                    out_sig.append(f'    """{doc.splitlines()[0].strip()}"""')
                    has_items = True
                for item in node.body:
                    if isinstance(item, (ast.AnnAssign, ast.Assign)):
                        seg = "\n".join(lines[item.lineno - 1 : (item.end_lineno or item.lineno)]).strip()
                        if "\n" not in seg and len(seg) <= 100:
                            out_sig.append(f"    {seg}")
                            has_items = True
                    elif isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        out_sig.extend(_format_py_func_sig(item, indent="    ", include_line_range=False))
                        has_items = True
                if not has_items:
                    out_sig.append("    ...")
        return "\n".join(out_sig)

    # Symbol extraction: comma-separated symbol names
    targets = {s.strip() for s in sec_clean.split(",") if s.strip()}
    matched_ranges: list[tuple[int, int]] = []

    def _visit_nodes(nodes: list[ast.stmt], parent_class: str | None = None) -> None:
        for node in nodes:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                qual_name = f"{parent_class}.{node.name}" if parent_class else node.name
                if node.name in targets or qual_name in targets:
                    start_line = min([node.lineno] + [d.lineno for d in node.decorator_list])
                    end_line = node.end_lineno or node.lineno
                    matched_ranges.append((start_line, end_line))
                    continue
                if isinstance(node, ast.ClassDef):
                    _visit_nodes(node.body, parent_class=node.name)

    _visit_nodes(tree.body)
    if not matched_ranges:
        return f"ERROR: Symbool '{section}' niet gevonden in '{file_path}'."

    blocks = [
        f"# L{start}-L{end}\n" + "\n".join(lines[start - 1 : end])
        for start, end in matched_ranges
    ]
    return "\n\n".join(blocks)


def _extract_js_ts_code(raw_text: str, section: str | None, file_path: str) -> str:
    lines = raw_text.splitlines()
    if section is None or not section.strip():
        out: list[str] = []
        blank_streak = 0
        for line in lines:
            if not line.strip():
                blank_streak += 1
                if blank_streak == 1:
                    out.append("")
                continue
            blank_streak = 0
            out.append(line.rstrip())
        while out and out[0] == "":
            out.pop(0)
        while out and out[-1] == "":
            out.pop()
        return "\n".join(out)

    sec_clean = section.strip()
    if sec_clean in ("--signatures", "--outline"):
        sig_lines: list[str] = []
        for idx, line in enumerate(lines, start=1):
            stripped = line.strip()
            if not stripped or stripped.startswith("//") or stripped.startswith("/*") or stripped.startswith("*"):
                continue
            if _JS_TS_SIG_RE.match(line) or _JS_TS_METHOD_RE.match(line):
                clean_sig = line.rstrip()
                if clean_sig.endswith("{"):
                    clean_sig = clean_sig[:-1].rstrip() + " { ... }"
                sig_lines.append(f"{clean_sig}  # L{idx}")
        return "\n".join(sig_lines)

    targets = [s.strip() for s in sec_clean.split(",") if s.strip()]
    blocks: list[str] = []
    for sym in targets:
        esc = re.escape(sym)
        decl_re = re.compile(
            rf"^\s*(?:export\s+(?:default\s+)?)?(?:(?:public|private|protected|static|readonly|async|abstract)\s+)*(?:function\s+{esc}|class\s+{esc}|interface\s+{esc}|type\s+{esc}|enum\s+{esc}|(?:const|let|var)\s+{esc}|{esc}\s*(?:<[^>]*>)?\s*\()\b"
        )
        idx = 0
        while idx < len(lines):
            if decl_re.search(lines[idx]):
                start_idx = idx
                while start_idx > 0 and lines[start_idx - 1].strip().startswith("@"):
                    start_idx -= 1
                brace_depth = 0
                seen_open_brace = False
                end_idx = idx
                for scan_idx in range(idx, len(lines)):
                    scan_line = lines[scan_idx]
                    for ch in scan_line:
                        if ch == "{":
                            brace_depth += 1
                            seen_open_brace = True
                        elif ch == "}":
                            brace_depth -= 1
                    end_idx = scan_idx
                    if seen_open_brace and brace_depth <= 0:
                        break
                    if not seen_open_brace and scan_line.rstrip().endswith(";"):
                        break
                blocks.append(
                    f"# L{start_idx + 1}-L{end_idx + 1}\n"
                    + "\n".join(lines[start_idx : end_idx + 1])
                )
                idx = end_idx + 1
            else:
                idx += 1

    if not blocks:
        return f"ERROR: Symbool '{section}' niet gevonden in '{file_path}'."
    return "\n\n".join(blocks)


def _extract_frontmatter(text: str) -> str | None:
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return None
    for scan_idx in range(1, len(lines)):
        if lines[scan_idx].strip() in ("---", "..."):
            return "\n".join(lines[: scan_idx + 1])
    return None


def _extract_markdown_headings(text: str) -> str | None:
    lines = text.splitlines()
    in_fence = False
    fence_marker = ""
    headings: list[str] = []
    for idx, line in enumerate(lines, start=1):
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
        if _HEADING_RE.match(line):
            headings.append(f"L{idx}: {line.strip()}")
    return "\n".join(headings) if headings else None


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


def _split_md_table_cells(line: str) -> list[str]:
    stripped = line.strip()
    inner = stripped[1:-1]
    return [c.strip() for c in _UNESCAPED_PIPE_RE.split(inner)]


def _is_md_table_line(line: str) -> bool:
    stripped = line.strip()
    return stripped.startswith("|") and stripped.endswith("|") and len(stripped) >= 2


def _is_md_table_sep_row(cells: list[str]) -> bool:
    return bool(cells) and all(bool(_TABLE_SEP_CELL_RE.match(c)) for c in cells)


def _compact_table_line(line: str) -> str:
    if not _is_md_table_line(line):
        return line.rstrip()

    raw_cells = _split_md_table_cells(line)
    compacted_cells: list[str] = []
    for c in raw_cells:
        sep_match = _TABLE_SEP_CELL_RE.match(c)
        if sep_match:
            c = f"{sep_match.group(1)}-{sep_match.group(2)}"
        compacted_cells.append(c)
    return "|" + "|".join(compacted_cells) + "|"


def _format_table_block(table_lines: list[str], convert_to_dsv: bool) -> list[str]:
    if convert_to_dsv and len(table_lines) >= 4:
        header_cells = _split_md_table_cells(table_lines[0])
        sep_cells = _split_md_table_cells(table_lines[1])
        if _is_md_table_sep_row(sep_cells):
            dsv_lines = ["#schema:" + "|".join(header_cells)]
            for row_line in table_lines[2:]:
                dsv_lines.append("|".join(_split_md_table_cells(row_line)))
            return dsv_lines
    return [_compact_table_line(tl) for tl in table_lines]


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
    table_buffer: list[str] = []

    def _flush_table_buffer() -> None:
        nonlocal table_buffer
        if table_buffer:
            out.extend(_format_table_block(table_buffer, convert_to_dsv=compact_tables))
            table_buffer = []

    for line in lines[idx:]:
        fence_match = _FENCE_RE.match(line)
        if fence_match:
            _flush_table_buffer()
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
            _flush_table_buffer()
            blank_streak += 1
            if blank_streak == 1:
                out.append("")
            continue

        blank_streak = 0
        if _is_md_table_line(line):
            table_buffer.append(line)
        else:
            _flush_table_buffer()
            out.append(line.rstrip())

    _flush_table_buffer()

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
                "Relative or absolute path to a .md, .txt, .json, .py, .ts, .tsx, .js, .jsx, .yaml, .yml, .toml, .csv, or .tsv file inside the project workspace."
            )
        ),
    ],
    section: Annotated[
        str | None,
        Field(
            default=None,
            description=(
                "Optional selector: for .md/.txt use '--frontmatter', '--headings', or one/more comma-separated heading names ('Why,Scope'); "
                "for .py/.ts/.js use '--signatures' ('--outline') or comma-separated symbol names ('func1,ClassA'); "
                "for .json/.yaml/.toml use comma-separated top-level keys ('routes,version')."
            ),
        ),
    ] = None,
    dsv_for_flat_lists: Annotated[
        bool,
        Field(
            default=True,
            description=(
                "When True (default), converts flat, dense JSON lists (top-level or nested under dict keys), "
                "Markdown tables (>= 2 data rows), and .csv/.tsv files into Positional Pipe-DSV (#schema:col1|col2...)."
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
    """Losslessly compress a workspace .md, .txt, .json, .py, .ts, .js, .yaml, .toml, or .csv file for context packs.

    Supports Markdown section extraction (--frontmatter, --headings, or multi-section A,B,C),
    Python/TS/JS AST --signatures and symbol extraction, table/CSV/JSON Positional Pipe-DSV (#schema:col1|col2...)
    for flat lists with N >= 2, and RFC 8259 JSON/YAML/TOML compaction.
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

    suffix = target.suffix.lower()

    if suffix == ".json":
        return _compress_json_content(
            raw_text,
            dsv_for_flat_lists=validated.dsv_for_flat_lists,
            file_path=validated.file_path,
            section=validated.section,
        )

    if suffix in (".csv", ".tsv"):
        return _compress_csv_or_tsv(
            raw_text,
            delimiter="\t" if suffix == ".tsv" else ",",
            dsv_for_flat_lists=validated.dsv_for_flat_lists,
        )

    if suffix in (".yaml", ".yml", ".toml"):
        return _compress_yaml_or_toml(
            raw_text,
            section=validated.section,
            file_path=validated.file_path,
        )

    if suffix == ".py":
        return _extract_python_code(
            raw_text,
            section=validated.section,
            file_path=validated.file_path,
        )

    if suffix in _CODE_EXTENSIONS:
        return _extract_js_ts_code(
            raw_text,
            section=validated.section,
            file_path=validated.file_path,
        )

    content = raw_text
    if validated.section is not None and validated.section.strip():
        sec_clean = validated.section.strip()
        if sec_clean == "--frontmatter":
            fm = _extract_frontmatter(content)
            if fm is None:
                return f"ERROR: Geen frontmatter gevonden in '{validated.file_path}'."
            return fm
        if sec_clean == "--headings":
            hd = _extract_markdown_headings(content)
            if hd is None:
                return f"ERROR: Geen headings gevonden in '{validated.file_path}'."
            return hd

        queries = [q.strip() for q in sec_clean.split(",") if q.strip()]
        extracted_sections: list[str] = []
        for q in queries:
            sec_block = _extract_markdown_section(content, q)
            if sec_block is not None:
                extracted_sections.append(sec_block)

        if not extracted_sections and len(queries) > 1:
            single_block = _extract_markdown_section(content, sec_clean)
            if single_block is not None:
                extracted_sections.append(single_block)

        if not extracted_sections:
            return f"ERROR: Sectie '{validated.section}' niet gevonden in '{validated.file_path}'."
        content = "\n\n".join(extracted_sections)

    return _compact_markdown_or_text(
        content, compact_tables=validated.dsv_for_flat_lists
    )


if __name__ == "__main__":
    mcp.run()
