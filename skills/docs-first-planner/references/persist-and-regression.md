# Phase 5: Persist, Status Updates & Regression Check Rules

Load this reference via `compress_context(file_path="skills/docs-first-planner/references/persist-and-regression.md")` only after the user approves the plan in Phase 4 (`"akkoord"`, `"approved"`, `"go"`), when updating an existing item's status, or when executing regression checks in Phase 1 step 5 / Phase 5 step 4.

## Phase 5: Persist (only after approval)

Never write to `./docs` before the user has approved the plan in Phase 4 (except for the automatic outcome of a failed regression check). Once approved, execute these four steps in order:

1. **Category folder & number**:
   - Reuse `feature`, `bugs`, or an existing lowercase category folder under `./docs` (or `security` on the security route).
   - Run `python <skill-path>/scripts/docs_tool.py next <category>` from the project root (`py` or `python` on Windows) to get the next sequential two-digit number `NN`.
   - Save the approved plan in full to `./docs/<category>/NN-short-slug.md` using `references/plan-template.md` (plus `references/scaffold-template.md` when creating/reshaping modules, or `references/security-plan-template.md` on the security route), keeping frontmatter keys exact (`id`, `title`, `category`, `status`, `summary` <= ~120 chars, `tags`, `created`, `updated`, `related`).
   - Even though Phase 4 showed only the concise plain-language summary in chat, the file saved to `./docs/<category>/NN-short-slug.md` MUST contain all complete sections from `references/plan-template.md` (`## Why`, `## Starting point`, `## Decisions`, `## Scope`, `## Approach`, `## Acceptance criteria`, `## Risks and open points`, `## Relations`).

2. **Update related docs & scaffold**:
   - Add bidirectional `related` links in the frontmatter of both the new item and every linked existing item.
   - If the new plan replaces an earlier item, set the old item's `status` to `superseded` and update its `updated` date. When the new plan refines or overrides a specific decision or `Check:` from a related `done` item without superseding the whole item, perform a **Synchronous Prose Update**: update not only the `Check:` line, but also any contradicting prose in `summary`, `Expected behaviour`, `Decisions`, `Scope` and `MODULE.md` of that related item so zero internal contradictions remain.
   - Fix any stale statuses or `docs_tool.py check` issues found in Phase 1.
   - Update `./docs/index.md` if the product vision was added/refined, if a new project-wide hard exclusion/invariant was agreed (add a concise row to `## Standing constraints`, keeping at most ~15 active core constraints and referencing the source item IDs), or if new domain/technical terms were introduced (keep `## Search keywords` as a bracketed list of ~30–80 curated terms starting with ~5–8 leading vision/scale priority terms followed by technical/methodological domain terms).
   - If the plan includes a scaffold, create the module folders and write or merge each `MODULE.md` contract using `references/scaffold-template.md` (contracts and boundaries only, no implementation code), then run `python <skill-path>/scripts/docs_tool.py modules`.

3. **Regenerate index & verify**:
   - Run `python <skill-path>/scripts/docs_tool.py index` to regenerate the `<!-- INDEX:START -->` table in `./docs/index.md` (never edit the generated table rows by hand).
   - Run `python <skill-path>/scripts/docs_tool.py check` and verify it outputs `docs OK`.
   - **Security route:** Create or update `./docs/security/NN-security-baseline.md`, link it via `related`, and ensure "Security rules for AI" is present under the product vision in `./docs/index.md` (never writing raw secrets anywhere).

4. **Regression check (after) & Report**:
   - Re-run the `Check:` lines of related `done` items and touched `MODULE.md` files following `## Regression check rules` below (and when accessing `## Acceptance criteria` of a plan file via `compress_context`, pass `section="Acceptance criteria"` explicitly because unfiltered plan reads omit heavy sections by default).
   - Report to the user: the saved plan path, the updated index row, touched files, regression check result, and the recommended first step (suggesting the plan ID in commits/branches). Do not implement code unless the user asks.

## Later invocations: status updates

When an existing item is started, completed, dropped or replaced on a later invocation:
- Update `status` (`planned`, `in-progress`, `done`, `dropped`, `superseded`) and `updated` (`YYYY-MM-DD`) in its YAML frontmatter, then run `python <skill-path>/scripts/docs_tool.py index` and `python <skill-path>/scripts/docs_tool.py check`.
- **Before marking an item `done`:**
  1. Read its acceptance criteria via `compress_context(file_path="docs/<cat>/NN-slug.md", section="Acceptance criteria,Verification")`.
  2. Execute the tests/commands for every acceptance criterion and every touched `MODULE.md` `Check:` line.
  3. Record the verification evidence under a `## Verification` section at the bottom of the item (`| Criterion | How checked | Result |`), confirming 0 blast-radius hits and guard failure on reintroduction for bug fixes.
  4. Run the regression check on related `done` items (`## Regression check rules`).

## Regression check rules

Used in Phase 1 step 5, Phase 5 step 4, and when marking an item `done` so completed work does not silently break:

- **Scope & lines:**
  - Check only related `done` or `in-progress` items plus `./docs/security/` if present (never scan the entire `./docs` tree blindly).
  - When reading an item's `Check:` lines with `compress_context`, pass `section="Acceptance criteria"` (since a default `section=None` slim plan-read omits `## Acceptance criteria`).
  - Only criteria with an explicit `Check: <command> -> <expected result>` line are executed automatically; criteria without `Check:` are **manual** and stay open until a person confirms them.
- **Execution safety:**
  - Purely read-only, side-effect-free local commands (`docs_tool.py check`, `grep`/`Select-String`, `git status`/`git diff`, read-only test suites and benchmark `--check` scripts) run automatically from the project root.
  - Any command that writes, deletes, installs, calls external networks, touches production or uses secrets is marked `needs approval` and is never run without explicit user permission.
- **On a failed check** (the single exception to "never write to `./docs` before approval"):
  1. Set the failing item's `status` to `in-progress` and update `updated` in its frontmatter.
  2. Log the exact failure output under `## Verification` in that item (with secrets masked).
  3. Create a planned bug item `./docs/bugs/NN-regressie-<slug>.md` with bidirectional `related` links to the regressed item.
  4. Regenerate the index (`docs_tool.py index`) and run `docs_tool.py check`. Do not fix code during the planning phase.
