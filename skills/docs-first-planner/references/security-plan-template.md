# Security plan template

Used on the security route of `docs-first-planner`. Save to `./docs/security/NN-slug.md`. Write in the user's language. Keep the frontmatter keys exactly as in `plan-template.md` (category is `security`), because `scripts/docs_tool.py` builds the index from them. Never put full secrets in this file.

## Security plan

```markdown
---
id: security/02
title: Short, specific title
category: security
status: planned
summary: One line (max ~120 chars): what is secured or checked and why.
tags: [security, area, component]
created: 2026-01-31
updated: 2026-01-31
related: [security/01]
---

# Short, specific title

## Why
The risk or goal in 2-4 sentences, and which part of the product vision it protects.

## Scope
- In: what may be read and tested (paths, components, environments).
- Out (explicitly not doing): what is not touched, including systems not owned.
- Context: exposure, data sensitivity, users and roles, assumptions made.

## Findings (audit)
| # | Severity | Status | Title | Where | Proof (what was run, result) | Source + status |
| --- | --- | --- | --- | --- | --- | --- |

Status values: 🔴 PROVEN, 🟠 LIKELY, ❓ UNVERIFIED, ✅ NO FINDING. Coverage: categories checked and not checked, with reasons.

## Decisions (from the grill)
| Question | Decision | Reason |
| --- | --- | --- |

Include accepted risks (who accepted, until when) and deadlines.

## Approach
One numbered step per finding, highest severity first. Each step: the concrete fix, what it may break, and the re-test that proves it.
1. ...

## Acceptance criteria
- [ ] For every fixed finding: the original proof now fails and the project tests pass (command named).
- [ ] Secrets found: rotated (confirmed by the user) and removed from the code, and from history where agreed.
- [ ] Open findings (❓ / 🟠) are either settled or listed as accepted risk.

## Risks and open points
- Unverified items, source gaps, and which professional (security engineer, pentester, compliance officer) should confirm high-stakes points.

## Relations
- Depends on / overlaps / supersedes: `security/01`, ...
```

## Security baseline

One file per project: `./docs/security/NN-security-baseline.md` (usually `01`). It is the standing set of rules AI must follow in later work. Status stays `in-progress` while it is the living baseline.

```markdown
---
id: security/01
title: Security baseline
category: security
status: in-progress
summary: Standing security rules and known risks that every change in this project must respect.
tags: [security, baseline]
created: 2026-01-31
updated: 2026-01-31
related: []
---

# Security baseline

## Context
Exposure, data sensitivity, users and roles, deployment target (as verified or assumed).

## Rules for every change
Short, checkable statements derived from verified findings and decisions, for example:
- Where untrusted input is validated and how (name the mechanism found in the code).
- How authentication and authorization are enforced and where a new endpoint must hook in.
- How secrets are provided (never in code or logs) and which are known to be rotated.
- Dependency policy: how versions are pinned and checked.
- What AI agents and tools in this project may and may not do without human approval.

## Known risks and accepted risks
| Risk | Severity | Status | Owner / deadline |
| --- | --- | --- | --- |

## Verification
How to re-check these rules (commands, tests, scanners) and the date of the last check.
```

Only rules that were verified, or explicitly decided by the user, go in as rules. Unverified claims go under known risks as unverified.
