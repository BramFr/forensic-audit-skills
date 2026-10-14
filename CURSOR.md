# Using this repo with Cursor

This project includes a **Cursor project rule** so the forensic audit guidelines apply automatically when you work here.

## In this repository

1. Open the folder in Cursor.
2. The rule [`.cursor/rules/forensic-audit.mdc`](.cursor/rules/forensic-audit.mdc) is committed with `alwaysApply: true`, so no extra installation is needed.
3. In Cursor, confirm it under **Settings → Rules**, where `forensic-audit` should appear.

## Use the same guidelines in another project

**Cursor (recommended):** Copy `.cursor/rules/forensic-audit.mdc` into that project's `.cursor/rules/` directory (create the folders if needed).

**Other tools:** If a stack only supports a root instruction file, copy [`CLAUDE.md`](CLAUDE.md) into that project instead.

## Full skills

The rule contains only the condensed principles. For the complete procedures, copy the skill folders from [`skills/`](skills/) or paste the `SKILL.md` content into your tool's instruction mechanism.
