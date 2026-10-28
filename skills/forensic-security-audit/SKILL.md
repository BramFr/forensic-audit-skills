---
name: forensic-security-audit
description: Security audit of a codebase or repository, scoped to what the user points at. Reads, reasons about and (within the agreed scope) actively tests for vulnerabilities, leaked secrets, vulnerable or malicious dependencies, insecure configuration, weak authentication or authorization, unsafe AI/agent behaviour and other security risks, proves each finding with evidence, proposes concrete fixes, applies them with approval and re-tests. Asks the user (grill-me style) for missing context before starting. Use whenever the user wants a security scan, security review, vulnerability check, hardening, pentest-style review, secret scan, dependency check, threat model or asks "is this secure?", "is this safe to deploy?", "can this be exploited?", even if the word audit is not used. Also used by docs-first-planner whenever the wish is about security.
---

# Forensic Security Audit

Audit the security of code and configuration the way an attacker and a sceptical reviewer would: assume it is vulnerable until evidence says otherwise, and never report "secure" because nothing was found by a quick look. The goal is an honest list of what is **proven exploitable**, what is **plausibly risky** and what **could not be verified**, each with a concrete fix.

Write the report in the language the user writes in.

This skill reuses the evidence discipline of `forensic-audit` (source status labels, method labels, fail-closed on errors, no claim of work that was not done). If `forensic-audit` is available, read its SKILL.md for the exact label definitions and follow them. If not, apply the same principles yourself.

---

## Output modes

The work (Phases 0 to 4) is ALWAYS done in full; Phase 5 is the report. Only the amount of text shown differs.

**COMPACT (default).** Verdict, findings by severity with fix, honest gaps. See "Compact report".

**FULL.** Only when the user asks for a "full report", "volledig rapport", "audit trail", "alle details" or similar. See "Full report".

Never skip steps in COMPACT mode. Shorter output, not shallower work.

---

## Principles

**1. Scope first.** The user decides what is in scope (a folder, a repo, a service, a feature). Inside that scope you may read, reason and test. Never touch anything outside it: no scanning of other hosts, no reading unrelated files or accounts, no calls to third-party systems you do not own. If the scope is unclear, ask in Phase 0 (see principle 2) before starting.

**2. Ask before you start, then run in one go.** Questions are welcome, but only in Phase 0 (and in Phase 4 for approval of fixes). Ask about every missing fact that changes the verdict: scope, where it will run (internet-facing or internal), who the users are, what data it holds, the applicable regime (privacy law, sector rules), accepted risks, whether active testing is allowed. Use a grill-me style interview: one question at a time, each with your recommended answer, using the question tool when available; skip anything the code or `./docs` already answers. The "never ask" rule only applies once the scope is given and Phase 0 is complete: from Phase 1 to 3 do not pause for permission to continue; state minor assumptions in one line and list them under the open points.

**3. Every earlier claim is a hypothesis.** "We sanitize input", "the endpoint is behind auth", "this key is only for testing" are not evidence. Verify in code, in config and by running it.

**4. Reject fake security.** A passing linter, a green scanner, an `auth` middleware that exists but is not applied, a `.gitignore` entry for a secret that is already committed, or a validation that only runs client-side is not a pass. A pass needs proof (a test that fails before the fix and passes after, a command output, a primary source).

**5. Prove, don't guess.** For each finding, try to demonstrate it safely (a failing test, a crafted request against a local instance, a proof-of-concept that reads a harmless canary value). Label the result honestly (see "Finding status"). Never present a theoretical risk as proven.

**6. Safety rules while testing.**
- Test only on code and environments the user pointed at, preferably a local or disposable instance. Production only with explicit permission.
- No destructive actions (deleting data, mass requests, denial of service, password guessing against real accounts) without explicit confirmation.
- Never print secrets in full. Mask them (first and last characters) in the report, in logs and in saved docs.
- Treat every secret found in the repository or its history as **compromised**: advise rotation, not just removal.
- Do not exfiltrate, store or send found data anywhere.

**7. Always search for external sources and report honestly what was found.** Standards, weakness catalogues, advisories and secure-configuration guidance change. Check once, before starting, which tools you have (web search or the `search_website` MCP tool, code execution, file access, dependency or secret scanners already installed in the project). Prefer `search_website` when available: search first, then open the primary URL to reach 🔎 SOURCED. **Always check before searching whether `./docs/index.md` exists and contains `## Search keywords`:** if present, it is mandatory for accurate project-specific information — read it in Phase 0 and select 1 to 3 relevant terms per search query (`{selected keywords} {query}`: 1–2 leading vision/scale priority terms from the start of `## Search keywords` for architecture/scale/tenant-isolation queries, or 1–2 technical domain terms for specific protocol/RFC/crypto/CVE queries, stripping search-operator punctuation like `+`) without dumping the full keyword list into one query and **never sending 0 keywords when `## Search keywords` is present** (0 project keywords counts as `🚫 NOT SEARCHED`); if `./docs/index.md` or `## Search keywords` is not present (e.g. a standalone question), continue with the normal search flow. Never claim a source was read when only a snippet was seen. Do not rely on a fixed list of links from memory; find the current version of the relevant standard yourself.

**8. When something goes wrong, diagnose before you fix.** If the user shares a failure (an error, log, refused start, blocked action, failed authentication or deployment failure), follow the seven steps of `forensic-audit` Principle 6, applied to security:
1. **Discover**: derive the stack, component, protocol and regime from the scope and project files, then search live (`search_website` preferred: search first, then open the primary URL for 🔎 SOURCED) for the exact error and the governing security standard (formal standards such as ISO/IEC 27001, NEN, IEC or IETF RFCs; public authorities and standards such as NIST SP 800-series, NCSC, OWASP ASVS, CWE/CVE advisories; and official vendor/framework security docs). For paywalled standards (ISO/NEN), always name the standard AND open its free **open primary counterpart** (NIST, NCSC, OWASP, RFC or vendor advisory) for 🔎 SOURCED.
2. **Quote** the failure verbatim, with secrets masked (never repeat a secret in full, even if it appears in the log).
3. **Signal**: the first failing check or origin of the refusal, not the outer wrapper message that followed.
4. **Guard**: check whether the refusal is a deliberate fail-closed control (startup secret validation, CSRF/auth check, certificate verification, rate limit, policy gate). If so, the fix is to satisfy the control, never to disable, loosen or bypass it.
5. **Hypotheses**: at most 3 candidate causes, each with a cheap, safe test (for example checking variable presence or length without printing its value, inspecting token claims, or verifying certificate chains).
6. **Fix**: the concrete change aligned with the security standard, plus who performs it. Secrets are generated and stored by the user in the environment or secret manager, never pasted into chat, code or docs; any secret that appeared in a log or repository counts as compromised and must be rotated.
7. **Confirm**: re-run the action; confirm that the original failure is gone AND that the control still rejects a missing, weak or invalid value.

---

## Source and method labels

Per finding and per check, use the same labels as `forensic-audit`:

- Source status: 🔎 SOURCED, 🔍 SNIPPET, ⚠️ NO SOURCE FOUND, 🚫 NOT SEARCHED (a process failure, always flagged).
- Method: ⚙️ EXECUTED, 🧮 HAND-CALCULATED, 🧠 REASONED.

Fail-closed on `ERROR:`: a fetch that returned an error never counts as 🔎. Open another primary URL or fall back to 🔍 / ⚠️ and record the failed URL.

**Authority types** (choose the one that fits, find the current version yourself): a web application or API security standard and its verification requirements, a weakness catalogue (CWE-style identifiers), vulnerability and advisory databases for dependencies (CVE, ecosystem advisories), national or international security guidance bodies, the official documentation and security notes of the framework, library, cloud provider or protocol in use, and RFCs for protocols. Marketing blogs, vendor sales pages and SEO content do not count.

---

## Phase 0: Scope and context

1. Confirm the scope from the user's request (paths, components, branches). If the user pointed at nothing, ask.
1b. Run the question round from principle 2 for all open facts. Do not start Phase 1 until the answers (or explicit "unknown, assume X") are recorded.
2. Detect the stack by reading manifests and config (languages, frameworks, package managers, container and infrastructure files, CI definitions).
3. Note the context that changes severity: exposure (internet, internal, local only), data sensitivity, users and roles, deployment target. State assumptions in one line.
4. Check `./docs` if it exists (for example a security baseline or earlier security items) and treat it as hypotheses to verify, not facts.
5. Check which tools are available (see principle 7) and list them for the report.

---

## Phase 1: Map the attack surface

Build a short map, internally, before hunting:

- **Entry points**: routes, endpoints, CLI arguments, message consumers, file uploads, webhooks, scheduled jobs.
- **Trust boundaries**: where untrusted data enters, where privileges change, where data leaves.
- **Assets**: credentials, tokens, personal data, money-moving actions, admin functions.
- **Dependencies and build chain**: direct and transitive packages, install scripts, CI/CD steps and their permissions, base images.

Discover all of this at runtime from the code. Do not assume route names, framework conventions or file locations.

---

## Phase 2: Dynamic Category Discovery & Topic Extraction

### Step 2.1: Live Internet Research for 15 Domain Categories
Do NOT rely on hardcoded categories. Perform live web searches based on the specific project, stack, or question to discover **15 Domain-Specific Risk & Quality Categories** relevant to this subject.

*Examples of dynamic category sets generated by search:*
- **Automotive/Tuning**: Aerodynamics, ECU Calibration, Brake Bias, Tire Compound, Thermal Management, Suspension Geometry, Transmission Ratios, Frame Rigidity, Emissions Compliance, Fuel Delivery, Turbo Boost Limits, Exhaust Backpressure, Weight Distribution, Active Safety, Structural Fatigue.
- **Software/IT**: Injection, Authentication, Authorization (BOLA), Secrets Leakage, Supply Chain Dependencies, Infra Configuration, Cryptography, Input/Output Sanitization, Data Privacy & Logging, Availability/Rate Limiting, LLM/Agent Tool Safety, Async Race Conditions, State Management, Memory Leaks, Network Isolation.

### Step 2.2: Extract 10 Critical Audit Topics
From the 15 dynamically discovered categories, select **EXACTLY 10 Project-Specific Audit Topics** ($\text{T}_1 \dots \text{T}_{10}$):
- **5 High-Impact Topics ($\text{T}_1 \dots \text{T}_5$)**: Topics where failure causes immediate system crash, severe safety hazards, legal non-compliance, or major financial loss.
- **5 High-Uncertainty / High-Risk Topics ($\text{T}_6 \dots \text{T}_{10}$)**: Topics relying on unverified assumptions, outdated methods, high complexity, or greatest risk of "Fake Green" illusions.


---

## Phase 3: Closed-Loop Execution & Rollback Loop (Per Topic)

Execute the following 5-step loop sequentially for each of the 10 topics ($\text{T}_1 \dots \text{T}_{10}$):

### STEP 1: ZERO-TRUST BASELINE ("BEFORE" STATE)
- **Forensic Self-Analysis**: Deconstruct implicit assumptions, record the exact baseline state (code/DOM state, chemical/physical parameters, structural constraints), and define the expected delta and potential failure modes.

### STEP 2: DYNAMIC ACTIVATION & SIMULATION ("AFTER" STATE)
- **Execution & Simulation**: Determine the appropriate activation archetype (Physical/Thermal calculation, Digital Runtime execution, Workflow/Logistics simulation, Quantitative/Normative formula test, or Adversarial Stress Test) and record the concrete "AFTER" outcome.

### STEP 3: LIVE PRIMARY SOURCE SEARCH
- **Web Search**: Perform targeted live web searches for the latest industry standards, regulations, manufacturer datasheets, RFCs, and peer-reviewed research.
- **Mandatory Filter**: Consult at least 10 distinct, independent, authoritative primary sources per audit in total, of which at least 5 per High-Impact topic (T1-T5) and at least 2 per High-Uncertainty topic (T6-T10). A source may support several topics but counts once in the total. Apply the source status labels honestly; never pad the count with unopened or irrelevant sources. Commercial blogs, marketing fluff, and unverified forum posts are strictly rejected.

### STEP 4: RED-TEAMING DISCONFIRMATION TEST & NORM MATCHING
- **Falsification Probe**: Execute explicit queries searching for known vulnerabilities, failure mechanisms, deprecated methods, or regulatory bans associated with the proposed solution.
- **Match Outcome**: Compare the "BEFORE" baseline and "AFTER" simulation directly against the verified standards from Step 3.

### STEP 5: FAIL-CLOSED FIX & FULL ROLLBACK TO STEP 1
- **IF MISMATCH / DEPRECATED / UNHEALTHY OUTCOME DETECTED**:
  1. Design the fix using one of the 5 Repair Archetypes (Refactoring, Boundary Tightening, Component Substitution, Recalibration, or Fail-Closed Fallback). Apply it to the project only after approval in Phase 4 (or, in docs-first-planner mode, record it as a plan step); until then verify it on a scratch copy or by reasoning and label the method honestly.
  2. **HARD ROLLBACK TO STEP 1**: Re-initialize the baseline and re-run the entire 5-step loop for this topic. Maximum 5 rollback iterations per topic; if it still does not pass, set it to FAIL-CLOSED instead of looping further.
- **IF 100% VERIFIED**: Assign `[VERIFIED_PASS]` (equivalent to NO FINDING, or FIXED with EXECUTED or SOURCED evidence; a topic resting only on REASONED, SNIPPET, NO SOURCE FOUND or NOT SEARCHED can never be `[VERIFIED_PASS]`) and automatically proceed to the next topic.

### Finding status

| Status | Use when |
| --- | --- |
| 🔴 PROVEN | Reproduced (⚙️ EXECUTED): exploit or failing test demonstrated |
| 🟠 LIKELY | Strong code-level reasoning or source support, not reproduced. Never counts as proven |
| ❓ UNVERIFIED | Could not be assessed or reproduced (missing environment, input, access or source). Never counts as confirmed and never as fixed |
| 🔁 FIXED | Fix applied and re-tested: the same proof now fails, other behaviour still works |
| ⛔ FAIL-CLOSED | Cannot be fixed safely within the scope (needs redesign or a decision); do not rely on it as is |
| ✅ NO FINDING | Checked, nothing found, with evidence of what was checked (not "nothing seen") |

---

## Phase 4: Fix & re-test (with approval)

1. Present the findings that have a fix, ordered by severity, and ask the user which fixes to apply (grill-me style: one question at a time, with your recommendation). Apply nothing without approval. In docs-first-planner mode skip this phase (see the last section).
2. Apply the approved fixes inside the agreed scope only. Prefer the smallest change that satisfies the control; never disable or loosen a guard. **Lossless Context Pack & Subagent Isolation:** use `compress_context` (`mcp/context-compressor`) in (1) **Phase 0/1 Progressive Reading** (`section="--frontmatter"`, `section="--headings"`, or multi-section `section="Scope,Rules"` on `.md` docs), (2) **Phase 1–3 Security Code/Config Audit** (`section="--signatures"` or `section="func1,func2"` on `.py`/`.ts`/`.js`, `section="key"` on `.json`/`.yaml`/`.toml`, and when scanning `>= 3` source files in depth, delegate a read-only `research` subagent with a compressed Context Pack returning `#schema:point|status|file_line|evidence`), and (3) **Phase 4 Code-Subagent Isolation**: whenever applying a fix writes or modifies any code (even 1 line), delegate the code edit to a clean code-subagent (`invoke_subagent` / `Agent` tool) with a lossless **Subagent Context Pack** built via `compress_context` (`--signatures` + target functions + scoped `.md` section, Pipe-DSV `#schema:` for `N >= 2` flat rows/tables, or `JSON_COMPACT`; never use lossy word-pruning or parallel edits to the same file).
3. Re-test with the same proof that demonstrated the finding (EXECUTED): it must now fail, and other behaviour must still work. Set status FIXED only on that evidence. Max. 5 rounds per finding, then FAIL-CLOSED.
4. Secrets that were found stay compromised: tell the user to rotate them; never paste new secrets into chat, code or docs.

---

## Phase 5: Forensic Attribution & Final Audit Report

Deliver the report in COMPACT mode by default or FULL mode on request (see "Compact report" and "Full report"). The FULL report is organised into the following 6 sections; the quotation limit is 15 words everywhere:

1. **Primary Evidence & Attribution Matrix**: Record all verified claims backed by primary source citations (Author/Organization, Standard Identifier/URL, and verbatim quotation of at most 15 words, only of what was actually read). No fabricated certainty percentages.
2. **Red-Team Audit Log**: Transparent register of all tested failure modes and how the final solution neutralizes them.
3. **Reconciliations of Conflicting Sources**: Explicit justification when authoritative sources conflict (e.g., newer EU directive vs. older national standard).
4. **Negative Declaration & Unverified Scope**: Clear disclosure of any parameters that could not be fully verified due to missing raw data or simulation limits.
5. **Actionable Implementation Protocol**: Step-by-step guidance equipped with strict Guard Clauses ("Do's & Don'ts").
6. **Forensic Audit Seal**:
   - **Overall Verdict**: the scale of the Verdict rules below (`SECURE ENOUGH` / `CONDITIONAL` / `NOT SECURE`), for the original and the fixed state
   - **Dynamic Categories Researched**: 15 categories listed
   - **Audited Topics**: 10 topics (5 High-Impact + 5 High-Uncertainty)
   - **Total Primary Sources Cited**: [Number of sources]
   - **Audit Date**: [Current Date]

---

## Verdict rules (both modes)

- **Verdict on the original state**:
  - `SECURE ENOUGH`: no 🔴 or 🟠 finding of severity Critical or High; remaining findings are Medium or Low and listed.
  - `CONDITIONAL`: no 🔴 Critical or High; there are 🟠 or ❓ High or Critical findings that must be settled first (list them).
  - `NOT SECURE`: at least one 🔴 PROVEN Critical or High finding, or any Critical or High finding that is ⛔ FAIL-CLOSED.
- **Verdict on the fixed version**: apply the same scale to the state after Phase 4 (Fix & re-test). A 🔁 FIXED finding counts as resolved only when the re-test is ⚙️ EXECUTED. Any unresolved Critical or High that is 🔴, 🟠, ❓ or ⛔ gives `NOT SECURE` or `CONDITIONAL` as above.
- **Never `SECURE ENOUGH` on thin evidence.** If a whole category that applies was not checked, or an Impact area is ❓ or 🚫, the verdict is at most `CONDITIONAL` and the gap is named.
- **Confidence**: High, Medium or Low, based on how much rests on ⚙️ and 🔎 versus 🧠, 🔍 and ❓. A 🚫 NOT SEARCHED on a Critical or High finding caps confidence at Low.
- **Source gaps**: number of ⚠️ and 🚫 items with their numbers, or "none". If not "none", start the line with ⚠️.
- **Coverage line**: which categories were checked and which were not (and why). "Not found" only means "not found in what was checked".

---

## Compact report (DEFAULT)

Show exactly this. Aim for roughly one screen. Use the user's language.

1. **Tools and scope line** (one line): scope audited, tools available. If no search tool: `⚠️ NO EXTERNAL SOURCES CONSULTED — this audit rests on reasoning only`.
2. **Verdict** (2 lines): original state → `SECURE ENOUGH` / `CONDITIONAL` / `NOT SECURE`; fixed state → same scale. Add Confidence.
3. **Findings by severity** (Critical first): per finding one block of at most 4 lines: `severity · status · title`, where (`file:line`), proof (what was run and what happened), fix (the concrete change) and, for fixed items, the re-test result. Mask secrets.
4. **Before you go live** (max. 5 bullets): rotations to perform, conditions, assumptions, and the honest gaps: every ❓, 🟠, ⚠️ and 🚫 item in one line, failed URLs, and which professional (security engineer, pentester, DPO or compliance officer) should confirm anything high-stakes that is not ⚙️-proven.
5. **Coverage and source gaps** line, and a counts line: `🔴 x · 🟠 x · ❓ x · 🔁 x · ⛔ x · ✅ x | 🔎 x · 🔍 x · ⚠️ x · 🚫 x | date`.
6. **Limitation note** (one line): this audit reduces risk but does not replace a professional penetration test, a compliance assessment or sign-off where law, money or sensitive data are involved. Absence of findings is not proof of security.
7. **Last line**: "Say 'full report' for the complete audit trail."

Do not show: the attack surface map, the per-category tables, the falsification log or the execution protocol. Offer them only through the last line.

---

## Full report (only on request)

Show: the attack surface map, the category checklist with the result per category, every finding with all five Phase 3 steps, then:

1. **Evidence and attribution**: organisation, identifier or URL, status (🔎/🔍) and at most one literal quote of at most 15 words, only of what you actually read.
2. **Falsification log**: mechanisms that produced a deviation, and how neutralised, plus the total checked.
3. **Conflicting sources**: only real conflicts, resolved in favour of the most recent and, on safety matters, the strictest.
4. **Negative Declaration**: everything not substantiated, not tested or out of scope: unchecked categories, every 🟠, ❓, 🔍, ⚠️, 🚫, 🧠 item, tools that were missing, environments that were not available. Never shorten this section.
5. **Execution protocol**: at most 10 steps plus at most 5 Do's and 5 Don'ts.
6. **Audit summary**: verdicts, confidence, coverage, counts and limitation note.

---

## Use from docs-first-planner

When `docs-first-planner` runs a wish that is about security, it uses this skill for its audit phase and persists the result as security items in `./docs/security/`. In that mode:

- Run Phases 0 to 3 as the planner's audit (merge the Phase 0 question round with the planner's own interview: never ask the same thing twice). Do not apply fixes yet; they become the steps and acceptance criteria of the plan. Phase 4 (Fix & re-test) runs when the plan is carried out; Phase 5 delivers the report.
- Hand over to the planner in this shape: findings (with severity, status, proof), verified facts, unverified items and the questions only the user can answer (exposure, data, accepted risk, deadlines).
- The planner also derives a reusable **security baseline** in `./docs/security/` from the verified findings, so later AI work in the project respects the rules (see its SKILL.md).
