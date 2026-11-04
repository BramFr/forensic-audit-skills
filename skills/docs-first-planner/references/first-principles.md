# First-principles analysis (phases 2.5, 3, 3.5 and the plan check)

Planner-specific rules for the first-principles method. The method itself lives in `../../first-principles-architect/SKILL.md` (`skills/first-principles-architect/SKILL.md`), which is the single canonical source for it: the 7 universal dimensions with their questions (D1 baseline, D2 target, D3 hard constraints, D4 failure modes, D5 system dynamics, D6 resource budget, D7 reversibility), the complexity switch (single-topic vs. composite decomposition into 3 to 6 sub-topics plus 4 lifecycle safeguards: preparation/first-run readiness, handoff/scale continuity, environment coexistence/load cap, and selective sub-topic recovery/clean delivery), the research of each dimension with **Control Point 1 (2 pros and 2 cons from subject to solution)** and **Step 2B Adversarial Disconfirmation & Triple Actuality/Typology Check** (phase 1.5, executed via Batch Prompting `arXiv:2511.04108` with DAST/CoD density and Zero-Trust Context-Purge), the **Simplicity Ladder** (YAGNI -> DRY -> existing standard capabilities -> built-in environmental safeguards -> already chosen means -> minimal custom addition with LBYL), the 8-part system analysis (its Phase 2, including part 5, perception, cognition and sensory ergonomics, which applies whenever a living organism or an observer is in the loop), **Control Point 2 (2 pros and 2 cons from subject to solution in intake options, decisions and pre-delivery check)**, the verification gates and the delivery rules. It is written in neutral language: translate every question, part and check into the vocabulary of the wish, without skipping any part. Those definitions are not repeated here; when this file and `skills/first-principles-architect/SKILL.md` differ, the latter wins.

This file only says how the method plugs into this skill: phases 2.5, 3 and 3.5 and the plan check.

## Phase 2.5: dimension check (after the audit, before the grill)

Never produce a final plan, step list or configuration here. Instead:

1. Map the wish and the audit findings onto D1 to D7 (and onto the 3 to 6 sub-topics and 4 lifecycle safeguards when composite). Mark each dimension **known** (with its evidence: 🔎 source, test, material or docs), **assumed** (state the assumption) or **missing**, and verify that **Control Point 1 (2 pros and 2 cons from subject to solution)** is recorded per topic/sub-topic.
2. Correct factually wrong or superseded assumptions (found via Step 2B disconfirmation) in the wish straight away, with the source, so the user answers the grill on correct premises.
3. Walk the **Simplicity Ladder** top-down and draft the **system analysis** (the 8 parts of `skills/first-principles-architect/SKILL.md`, Phase 2) as far as the evidence allows. Parts that cannot be filled yet are marked missing, never guessed; every gap becomes a candidate grill question or a research item.
4. **Pre-Grill Invariant Gate:** Filter candidate choices against active `## Standing constraints`, boundary contracts (`Does NOT do`) and earlier `## Decisions` / `Out:` exclusions so no previously rejected pattern is re-introduced, then rank the missing and assumed dimensions (and any open sub-topic handoffs or lifecycle safeguards) by how much they change the outcome (a wrong D3, D4 or D7 usually costs most). The top ones become the grill questions.

Keep both the D1–D7 dimension overview and the 8-part system analysis internal to drive the grill questions and the plan; do not print the D1–D7 overview in chat during compact runs, and print the full analysis only when the user asks for the "full report". Continue straight from the brief audit summary into the grill in the same turn.

## Grill rules added by this reference (phase 3)

- **At least 3, at most 10 questions per plan**, counted over all rounds. Ask in **rounds of 3 to 5 questions** (or 1 round of 4 to 6 questions for composite wishes covering the 3 to 6 sub-topics and 4 lifecycle safeguards) in one message, numbered, each in plain language with **3 to 5 options (Hick's Law)**, the pre-researched Smart Default first marked "(Recommended)" so the user can confirm in one word, a one-line reason, and "or tell me to decide". Never propose an option or "(Recommended)" default that violates `## Standing constraints`, boundary exclusions or prior `## Decisions` / `Out:` commitments unless the user explicitly asks to supersede that earlier commitment.
- **Control Point 2 (2 pros and 2 cons from subject to solution):** For every recommended choice or option in the grill, and for every key decision recorded in the plan, state **2 pros** (two verified strengths/mechanisms from subject to solution) and **2 cons** (two verified trade-offs/risks from subject to solution).
- Target the missing or assumed dimensions with the most leverage. Never walk through all 7 dimensions as a rigid checklist (interrogation fatigue).
- If fewer than 3 real gaps remain, use the remaining questions to confirm the riskiest assumption (usually D4 failure modes, D7 reversibility, or one of the 4 lifecycle safeguards) or the misconception from part 8; never ask a question whose answer cannot change the plan.
- If a question can be answered by reading existing files, docs or a primary source, look it up instead of asking.
- After 10 questions, stop asking. Every gap still open goes into the plan as **unverified** (Starting point and Risks) with the assumption you used. Ask more only when the user explicitly says so (for example "ask more" / "vraag verder"); extra questions then follow the same rules.

## Phase 3.5: verification loop (after every round of answers)

The answers are new claims, so they are checked like any other claim:

1. **Search again (including Step 2B Adversarial Disconfirmation).** For every answer that sets a parameter, limit, target or method, run a new `search_website` query (or batch via `queries_or_urls=[...], auto_open_top=1` / inline `"open: <query>"`, following the same search rules as phase 2, including the `## Search keywords` rule) and open the primary source to confirm it is correct, current at time horizon $t$ (not repealed, superseded or overruled by a higher authority), classified by typology (strict binding obligation vs. flexible guideline), and compatible with the rest of the chain. Only official sources count (the source hierarchy of Phase 0 in `skills/first-principles-architect/SKILL.md`); a blog, forum or template page is not a source. Also search for what is still **missing**: a sub-parameter, dependency or constraint the answer implies but nobody has named yet.
2. **Confidence gate.** A link in the causal chain (part 4) passes only when it rests on a 🔎 SOURCED primary source, a reproduced test or the actual material or measurement. A snippet (🔍), a plausible inference or an unconfirmed user statement does not pass; it stays **unverified**.
3. **Circuit breaker.** Trip it when any of these holds:
   - *Parameter mismatch:* a chosen option needs sub-parameters that are missing, conflicting or not supported by the layer below.
   - *Confidence gap or norm decay:* a link does not pass the confidence gate or fails the Step 2B actuality/typology/authority check.
   - *Constraint violation:* working out the chain still collides with D3 hard constraints or D6 resource budget.
4. **Recovery.**
   - *Research loop:* stop working towards the plan, research the right parameter, correct the state-parameter matrix and re-run the chain from the point of deviation. If the gap can only be closed by the user, ask a follow-up question (a new round, within the limit of 10).
   - *Hard reset (deadlock):* if the requested combination is physically, biologically, technically, legally or economically impossible (irreconcilable requirements), stop. Name the exact blockage with its source and put adjusted boundary conditions to the user as the next grill question, before any plan is written.
5. Leave the loop only when every link passes the gate or is explicitly marked unverified in the plan, and no circuit breaker condition is open.

## Plan check additions (phase 4)

- Are all 7 dimensions covered in the plan (Starting point, Decisions, Scope, Risks or Acceptance criteria), with any assumption stated as unverified?
- **Composite sub-topics and 4 lifecycle safeguards:** When the wish is composite, does the plan cover all 3 to 6 sub-topics, their handoffs, and all 4 lifecycle safeguards (1: preparation and idempotent first-run readiness, 2: handoff and scale continuity without truncation, 3: coexistence with the surrounding environment via safe load caps, 4: selective sub-topic recovery without restarting earlier verified stages)?
- **Both control points (2 pros and 2 cons from subject to solution):** Are **Control Point 1** (2 pros and 2 cons from subject to solution per topic/sub-topic in the research/audit findings) and **Control Point 2** (2 pros and 2 cons from subject to solution for the recommended options and key decisions in the plan) explicitly documented?
- **Simplicity Ladder & Step 2B Actuality:** Did every proposed component pass the Simplicity Ladder (YAGNI -> DRY -> existing standard capabilities -> built-in environmental safeguards -> already chosen means -> minimal addition with LBYL) and the Step 2B disconfirmation/actuality check?
- **No placebo controls or dead paths.** Is every option, mode or setting the plan offers wired through to its actual execution? Trace each choice path *selection -> validation -> conditional sub-settings -> execution* and make sure no step is skipped.
- Is the misconception from part 8 handled (corrected in a step, a decision or a risk)?
- Does every link of the causal chain pass the confidence gate, or is it listed as unverified with the professional or primary source that must confirm it?
- Was no missing parameter guessed to make the chain look complete?
