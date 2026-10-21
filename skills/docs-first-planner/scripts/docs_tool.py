#!/usr/bin/env python3
"""Helper for the docs-first-planner skill. Standard library only.

Usage (run from the project root, or pass --docs PATH):
  docs_tool.py next <category>   print the next two-digit number for a category
  docs_tool.py index             rebuild the item table in docs/index.md from frontmatter
  docs_tool.py check             report problems (missing frontmatter, duplicate IDs, bad links, stale index)
  docs_tool.py index --strict    like index, but refuse to write when check finds problems
"""
import argparse
import re
import sys
from pathlib import Path

START, END = "<!-- INDEX:START -->", "<!-- INDEX:END -->"
STATUSES = {"planned", "in-progress", "done", "dropped", "superseded"}
FILE_RE = re.compile(r"^(\d{2,})-.+\.md$")
SKELETON = f"""# Docs index

## Product vision
_Not written down yet. Describe in 3-5 lines what the product is for, who it is for and what it is not._

## Items
{START}
{END}
"""


def parse_frontmatter(path):
    text = path.read_text(encoding="utf-8-sig")  # utf-8-sig: tolerate a BOM (PowerShell 5.1 / some editors add one)
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n", text, re.S)
    if not m:
        return None
    data = {}
    for line in m.group(1).splitlines():
        if ":" not in line or line.startswith((" ", "\t", "#")):
            continue
        key, _, val = line.partition(":")
        val = val.strip()
        if val.startswith("[") and val.endswith("]"):
            val = [v.strip() for v in val[1:-1].split(",") if v.strip()]
        data[key.strip()] = val
    return data


def items(docs):
    """Yield (path, frontmatter-or-None) for every NN-*.md in a category folder."""
    for cat in sorted(p for p in docs.iterdir() if p.is_dir()):
        for f in sorted(cat.glob("*.md")):
            if FILE_RE.match(f.name):
                yield f, parse_frontmatter(f)


def cell(value):
    if isinstance(value, list):
        value = ", ".join(value)
    return str(value or "").replace("|", "\\|").replace("\n", " ").strip()


def cmd_next(docs, category):
    folder = docs / category
    nums = [int(FILE_RE.match(f.name).group(1)) for f in folder.glob("*.md") if FILE_RE.match(f.name)] if folder.is_dir() else []
    print(f"{(max(nums) + 1) if nums else 1:02d}")


def build_table(docs):
    rows = ["| ID | Status | Title | Summary | Tags |", "| --- | --- | --- | --- | --- |"]
    warnings = []
    for f, fm in items(docs):
        rel = f.relative_to(docs).as_posix()
        if not fm:
            warnings.append(f"{rel}: no frontmatter, skipped")
            continue
        item_id = fm.get("id") or rel.rsplit("-", 1)[0]
        rows.append(
            f"| [{cell(item_id)}]({rel}) | {cell(fm.get('status'))} | {cell(fm.get('title'))} "
            f"| {cell(fm.get('summary'))} | {cell(fm.get('tags'))} |"
        )
    return "\n".join(rows), warnings


def cmd_index(docs, strict=False):
    docs.mkdir(parents=True, exist_ok=True)
    if strict and docs.is_dir():
        # the index itself may be missing or stale (that is what we are fixing), so ignore those messages
        problems = [p for p in collect_problems(docs) if "out of sync" not in p and "index.md does not exist" not in p]
        if problems:
            print("index NOT written (--strict), fix first:")
            print("\n".join(f"- {p}" for p in problems))
            sys.exit(1)
    index = docs / "index.md"
    if not index.exists():
        index.write_text(SKELETON, encoding="utf-8")
    text = index.read_text(encoding="utf-8")
    if START not in text or END not in text:
        text = text.rstrip() + f"\n\n## Items\n{START}\n{END}\n"
    table, warnings = build_table(docs)
    new = re.sub(re.escape(START) + r".*?" + re.escape(END), lambda _: f"{START}\n{table}\n{END}", text, flags=re.S)
    index.write_text(new, encoding="utf-8")
    print(f"index updated: {len(table.splitlines()) - 2} item(s)")
    for w in warnings:
        print("WARNING:", w)


def collect_problems(docs):
    problems = []
    index = docs / "index.md"
    if not index.exists():
        problems.append("docs/index.md does not exist")
    seen = {}
    all_ids = {fm2.get("id") for _, fm2 in items(docs) if fm2}
    for f, fm in items(docs):
        rel = f.relative_to(docs).as_posix()
        if not fm:
            problems.append(f"{rel}: missing frontmatter")
            continue
        for key in ("id", "title", "category", "status", "summary"):
            if not fm.get(key):
                problems.append(f"{rel}: frontmatter field '{key}' is empty")
        if fm.get("status") and fm["status"] not in STATUSES:
            problems.append(f"{rel}: unknown status '{fm['status']}'")
        if fm.get("category") and fm["category"] != f.parent.name:
            problems.append(f"{rel}: category '{fm['category']}' does not match folder '{f.parent.name}'")
        expected_id = f"{f.parent.name}/{FILE_RE.match(f.name).group(1)}"
        if fm.get("id") and fm["id"] != expected_id:
            problems.append(f"{rel}: id '{fm['id']}' does not match file name (expected {expected_id})")
        if str(fm.get("summary", "")).strip() in {">", "|", ">-", "|-"}:
            problems.append(f"{rel}: summary must be a single line (multi-line YAML is not parsed)")
        if fm.get("id"):
            if fm["id"] in seen:
                problems.append(f"{rel}: duplicate id {fm['id']} (also {seen[fm['id']]})")
            seen[fm["id"]] = rel
        rel_list = fm.get("related") or []
        for r in rel_list if isinstance(rel_list, list) else [rel_list]:
            if r and r not in all_ids:
                problems.append(f"{rel}: related item '{r}' not found")
    if index.exists():
        table, _ = build_table(docs)
        m = re.search(re.escape(START) + r"\n?(.*?)\n?" + re.escape(END), index.read_text(encoding="utf-8"), re.S)
        if not m or m.group(1).strip() != table.strip():
            problems.append("docs/index.md is out of sync with the item files (run: docs_tool.py index)")
    return problems


def cmd_check(docs):
    problems = collect_problems(docs)
    if problems:
        print("\n".join(f"- {p}" for p in problems))
        sys.exit(1)
    print("docs OK")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--docs", default="docs", help="path to the docs folder (default: ./docs)")
    sub = ap.add_subparsers(dest="cmd", required=True)
    n = sub.add_parser("next")
    n.add_argument("category")
    sub.add_parser("index").add_argument("--strict", action="store_true", help="refuse to write when check finds problems")
    sub.add_parser("check")
    args = ap.parse_args()
    docs = Path(args.docs)
    if args.cmd != "index" and not docs.is_dir():
        print(f"{docs} does not exist" + (" (next number would be 01)" if args.cmd == "next" else ""))
        if args.cmd == "next":
            print("01")
        sys.exit(0 if args.cmd == "next" else 1)
    {"next": lambda: cmd_next(docs, args.category), "index": lambda: cmd_index(docs, args.strict), "check": lambda: cmd_check(docs)}[args.cmd]()


if __name__ == "__main__":
    main()
