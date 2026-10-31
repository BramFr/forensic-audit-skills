# First-principles analysis (phases 2.5, 3, 3.5 and the plan check)

A diagnostic intake and analysis engine built on first-principles thinking, systems engineering (INCOSE: stakeholder needs, requirements, constraints, verification), cybernetic control (closed feedback loops) and Failure Mode and Effects Analysis (FMEA). It works for any subject: software, a physical or mechanical system (vehicle, engine, network, heating), training or unlearning behaviour or physical performance (human or animal), a construction, recipe or renovation, or any optimisation where parameters and boundary conditions decide the outcome. Always translate the structure below into the exact vocabulary and metrics of the subject at hand, without skipping any part of it.

## The 7 universal dimensions

Every non-trivial wish is broken down along these seven axes:

| # | Dimension | Question it answers |
| --- | --- | --- |
| D1 | **Baseline** | What is the current state, history, starting point and context? |
| D2 | **Target** | What is the measurable, explicit end state, and what are the success criteria? |
| D3 | **Hard constraints** | Which physical, biological, infrastructural, legal or contractual limits cannot move? |
| D4 | **Failure modes** | What fails catastrophically if an assumption is wrong (data loss, out of memory, damage, injury, fear, leakage, a failed batch)? |
| D5 | **System dynamics** | Which side effects and parameter shifts appear elsewhere in the system when a choice or intervention is made? |
| D6 | **Resource budget** | How much time, capacity, money, hardware, energy or attention is available? |
| D7 | **Reversibility** | Is the intervention one-way, or can it be undone, and at what cost? |

## Phase 2.5: dimension check (after the audit, before the grill)

Never produce a final plan, step list or configuration here. Instead:

1. Map the wish and the audit findings onto D1 to D7. Mark each dimension **known** (with its evidence: 🔎 source, test, code or docs), **assumed** (state the assumption) or **missing**.
2. Correct factually wrong assumptions in the wish straight away, with the source, so the user answers the grill on correct premises.
3. Draft the **system analysis** below as far as the evidence allows; every gap becomes a candidate grill question or a research item.
4. Rank the missing and assumed dimensions by how much they change the outcome (a wrong D3, D4 or D7 usually costs most). The top ones become the grill questions.

Show the user only the compact dimension overview (D1–D7, one line per dimension: known / assumed / missing) together with the audit summary, then continue straight into the grill in the same turn. Keep the 7-part system analysis internal to drive the grill questions and the plan, and only print it in full when the user asks for the "full report".

## System analysis (7 fixed parts)

Run it in the vocabulary of the subject. Parts that cannot be filled yet are marked missing, never guessed.

1. **First principles.** The underlying physical, physiological, chemical, thermodynamic, economic, legal or computational mechanism that governs the outcome.
2. **Critical success factors.** The non-negotiable process conditions without which the result cannot succeed.
3. **Input and component audit (contamination and quality).** Which inputs, raw materials, environmental stimuli or dependencies degrade the result when their properties or ratios are wrong, and how they are eliminated or isolated beforehand.
4. **Causal chain and parameter coupling (state-parameter matrix).** For every option, mode or variable, trace the full chain: *choice or trigger -> dependent sub-parameters and conditions -> processing layer -> physical or technical execution*. State exactly which dependent settings change or become invalid when another option is chosen.
5. **Efficiency and scalability (throughput and overhead).** Quantify effort against yield on two axes: *time and throughput* (execution time, latency, preparation or lead time at scale) and *capacity and density* (memory, energy, volume, load or recovery per unit of input).
6. **Failure modes and breaking points.** Where the system, organism, material or process breaks under load, and what the early warning signs are.
7. **Empirical falsification (misconception).** Which common assumption, intuition or standard method in this subject is factually wrong or counterproductive according to the first principles, backed by a source.

## Grill rules added by this reference (phase 3)

- **At least 3, at most 10 questions per plan**, counted over all rounds. Ask in **rounds of 3 to 5 questions** in one message, numbered, each in plain language with options, the recommended answer first marked "(Recommended)", a one-line reason, and "or tell me to decide".
- Target the missing or assumed dimensions with the most leverage. Never walk through all 7 dimensions as a rigid checklist (interrogation fatigue).
- If fewer than 3 real gaps remain, use the remaining questions to confirm the riskiest assumption (usually D4 failure modes or D7 reversibility) or the misconception from part 7; never ask a question whose answer cannot change the plan.
- If a question can be answered by reading the code, docs or a primary source, look it up instead of asking.
- After 10 questions, stop asking. Every gap still open goes into the plan as **unverified** (Starting point and Risks) with the assumption you used. Ask more only when the user explicitly says so (for example "ask more" / "vraag verder"); extra questions then follow the same rules.

## Phase 3.5: verification loop (after every round of answers)

The answers are new claims, so they are checked like any other claim:

1. **Search again.** For every answer that sets a parameter, limit, target or method, run a new `search_website` query (same search rules as phase 2, including the `## Search keywords` rule) and open the primary source to confirm it is correct, current and compatible with the rest of the chain. Also search for what is still **missing**: a sub-parameter, dependency or constraint the answer implies but nobody has named yet.
2. **Confidence gate.** A link in the causal chain (part 4) passes only when it rests on a 🔎 SOURCED primary source, a reproduced test or the actual code or measurement. A snippet (🔍), a plausible inference or an unconfirmed user statement does not pass; it stays **unverified**.
3. **Circuit breaker.** Trip it when any of these holds:
   - *Parameter mismatch:* a chosen option needs sub-parameters that are missing, conflicting or not supported by the layer below.
   - *Confidence gap:* a link does not pass the confidence gate.
   - *Constraint violation:* working out the chain still collides with D3 hard constraints or D6 resource budget.
4. **Recovery.**
   - *Research loop:* stop building towards the plan, research the right parameter, correct the state-parameter matrix and re-run the chain from the point of deviation. If the gap can only be closed by the user, ask a follow-up question (a new round, within the limit of 10).
   - *Hard reset (deadlock):* if the requested combination is physically, biologically, technically, legally or economically impossible (irreconcilable requirements), stop. Name the exact blockage with its source and put adjusted boundary conditions to the user as the next grill question, before any plan is written.
5. Leave the loop only when every link passes the gate or is explicitly marked unverified in the plan, and no circuit breaker condition is open.

## Plan check additions (phase 4)

- Are all 7 dimensions covered in the plan (Starting point, Decisions, Scope, Risks or Acceptance criteria), with any assumption stated as unverified?
- **No placebo controls or dead paths.** Is every option, mode or setting the plan offers wired through to its actual execution? Trace each choice path *selection -> validation -> conditional sub-settings -> execution* and make sure no step is skipped.
- Is the misconception from part 7 handled (corrected in a step, a decision or a risk)?
- Does every link of the causal chain pass the confidence gate, or is it listed as unverified with the professional or primary source that must confirm it?
- Was no missing parameter guessed to make the chain look complete?
