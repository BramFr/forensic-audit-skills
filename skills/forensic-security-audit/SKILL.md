---
name: forensic-security-audit
description: Security audit of a codebase or repository, scoped to what the user points at. Reads, reasons about and (within the agreed scope) actively tests for vulnerabilities, leaked secrets, vulnerable or malicious dependencies, insecure configuration, weak authentication or authorization, unsafe AI/agent behaviour and other security risks, proves each finding with evidence, proposes concrete fixes, applies them with approval and re-tests. Use whenever the user wants a security scan, security review, vulnerability check, hardening, pentest-style review, secret scan, dependency check, threat model or asks "is this secure?", "is this safe to deploy?", "can this be exploited?", even if the word audit is not used. Also used by docs-first-planner whenever the wish is about security.
---

# Forensic Security Audit

Audit the security of code and configuration the way an attacker and a sceptical reviewer would: assume it is vulnerable until evidence says otherwise, and never report "secure" because nothing was found by a quick look. The goal is an honest list of what is **proven exploitable**, what is **plausibly risky** and what **could not be verified**, each with a concrete fix.

Write the report in the language the user writes in.

This skill reuses the evidence discipline of `forensic-audit` (source status labels, method labels, fail-closed on errors, no claim of work that was not done). If `forensic-audit` is available, read its SKILL.md for the exact label definitions and follow them. If not, apply the same principles yourself.

---

## Output modes

The work (Phases 0 to 4) is ALWAYS done in full. Only the amount of text shown differs.

**COMPACT (default).** Verdict, findings by severity with fix, honest gaps. See "Compact report".

**FULL.** Only when the user asks for a "full report", "volledig rapport", "audit trail", "alle details" or similar. See "Full report".

Never skip steps in COMPACT mode. Shorter output, not shallower work.

---

## Principles

**1. Scope first.** The user decides what is in scope (a folder, a repo, a service, a feature). Inside that scope you may read, reason and test. Never touch anything outside it: no scanning of other hosts, no reading unrelated files or accounts, no calls to third-party systems you do not own. If the scope is unclear, ask ONE concise question before starting.

**2. Ask only when a missing fact changes the verdict.** Examples: where it will run (internet-facing or internal), who the users are, what data it holds, the applicable regime (privacy law, sector rules). Otherwise state the assumption in one line and continue.

**3. Every earlier claim is a hypothesis.** "We sanitize input", "the endpoint is behind auth", "this key is only for testing" are not evidence. Verify in code, in config and by running it.

**4. Reject fake security.** A passing linter, a green scanner, an `auth` middleware that exists but is not applied, a `.gitignore` entry for a secret that is already committed, or a validation that only runs client-side is not a pass. A pass needs proof (a test that fails before the fix and passes after, a command output, a primary source).

**5. Prove, don't guess.** For each finding, try to demonstrate it safely (a failing test, a crafted request against a local instance, a proof-of-concept that reads a harmless canary value). Label the result honestly (see "Finding status"). Never present a theoretical risk as proven.

**6. Safety rules while testing.**
- Test only on code and environments the user pointed at, preferably a local or disposable instance. Production only with explicit permission.
- No destructive actions (deleting data, mass requests, denial of service, password guessing against real accounts) without explicit confirmation.
- Never print secrets in full. Mask them (first and last characters) in the report, in logs and in saved docs.
- Treat every secret found in the repository or its history as **compromised**: advise rotation, not just removal.
- Do not exfiltrate, store or send found data anywhere.

**7. Always search for external sources and report honestly what was found.** Standards, weakness catalogues, advisories and secure-configuration guidance change. Check once, before starting, which tools you have (web search or the `search_website` MCP tool, code execution, file access, dependency or secret scanners already installed in the project). Prefer `search_website` when available: search first, then open the primary URL to reach 🔎 SOURCED. Never claim a source was read when only a snippet was seen. Do not rely on a fixed list of links from memory; find the current version of the relevant standard yourself.

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

## Phase 2: Find candidate findings

Work through the categories that apply to the stack. For each, search the code and config, then record candidates with `file:line`.

| Category | Look for (examples, not an exhaustive list) |
| --- | --- |
| Injection | SQL, NoSQL, command, template, LDAP, path traversal, unsafe deserialization, SSRF, XXE |
| Authentication | weak or missing login protection, session and token handling, password storage, MFA gaps, default credentials |
| Authorization | missing checks, broken object-level access, privilege escalation, trusting client-supplied roles or ids |
| Secrets | keys, tokens, passwords in code, config, history, images, logs and CI variables |
| Dependencies and supply chain | known-vulnerable versions, unpinned or typo-squatted packages, risky install scripts, unreviewed CI actions, base image age |
| Configuration and infrastructure | debug mode, permissive CORS, missing security headers, open ports, public storage, over-broad cloud or container permissions, missing TLS |
| Cryptography | home-made crypto, weak algorithms, static IVs or salts, insecure randomness, disabled certificate checks |
| Input and output handling | missing validation, XSS, open redirects, unsafe file handling, unrestricted uploads, mass assignment |
| Data protection and logging | personal data in logs or errors, verbose error messages, missing audit trail, excessive data exposure |
| Availability | missing rate limits, unbounded resource use, algorithmic complexity, unsafe regular expressions |
| AI and agent risks (when the project uses LLMs or agents) | prompt injection, untrusted content reaching tools, over-privileged tools, secrets in prompts, unsafe use of model output as code or commands, missing human approval for risky actions |

Use installed scanners if they exist and are in scope, but treat their output as hypotheses: verify each hit and look for what the tool cannot see (logic flaws, authorization, business rules). A clean scanner run is not a pass.

---

## Phase 3: Prove each finding

For every candidate, do the five steps internally:

**Step 1: Baseline.** The exact vulnerable condition, who can reach it, what they gain, what the preconditions are.

**Step 2: Reproduce.** Pick the archetype that fits: a failing automated test, a crafted request against a local instance, a script that demonstrates the flaw with a harmless canary, a dependency version check against an advisory, a secret check (is it valid? only check validity when allowed, never use it beyond that). Record the result with the method label.

**Step 3: Primary source check.** Look up the weakness class and, for dependencies, the advisory (affected and fixed versions). Open the primary URL. Note source + identifier + status label.

**Step 4: Severity.** Rate Critical / High / Medium / Low from impact, exploitability and reachability in this context. State the reason in one line. A flaw that is not reachable is lower, but say so and say why.

**Step 5: Red-team the finding and the fix idea.** Try to disprove it (is it really reachable? is there a mitigation elsewhere?) and try to bypass your own proposed fix.

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

## Phase 4: Fix and re-test (closed loop)

1. Propose a concrete fix per finding (the code or config change, not advice), and say what it breaks if anything.
2. Apply fixes only with the user's approval, unless the user has already said fixes may be applied. Never loosen a check, delete a test or weaken a threshold to turn a result green.
3. Re-run the original proof and the project's own tests. A fix is 🔁 FIXED only when the proof that showed the flaw now fails and nothing else regressed.
4. Same fix failing three times: change approach. After two failed repair rounds set the finding to ⛔ FAIL-CLOSED and report why.
5. For found secrets: removal is not a fix. The fix is rotation plus removal from history where appropriate. State that rotation is the user's action when it cannot be done from here.
6. If `forensic-audit` is available, use it to audit the fixes themselves (is the fix correct and complete? does it follow current guidance?).

---

## Verdict rules (both modes)

- **Verdict on the original state**:
  - `SECURE ENOUGH`: no 🔴 or 🟠 finding of severity Critical or High; remaining findings are Medium or Low and listed.
  - `CONDITIONAL`: no 🔴 Critical or High; there are 🟠 or ❓ High or Critical findings that must be settled first (list them).
  - `NOT SECURE`: at least one 🔴 PROVEN Critical or High finding, or any Critical or High finding that is ⛔ FAIL-CLOSED.
- **Verdict on the fixed version**: apply the same scale to the state after Phase 4. A 🔁 FIXED finding counts as resolved only when the re-test is ⚙️ EXECUTED. Any unresolved Critical or High that is 🔴, 🟠, ❓ or ⛔ gives `NOT SECURE` or `CONDITIONAL` as above.
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

- Run Phases 0 to 3 as the planner's audit. Do not apply fixes yet; they become the steps and acceptance criteria of the plan. Phase 4 runs when the plan is carried out.
- Hand over to the planner in this shape: findings (with severity, status, proof), verified facts, unverified items and the questions only the user can answer (exposure, data, accepted risk, deadlines).
- The planner also derives a reusable **security baseline** in `./docs/security/` from the verified findings, so later AI work in the project respects the rules (see its SKILL.md).
