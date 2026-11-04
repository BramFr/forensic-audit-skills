---
name: first-principles-architect
description: Principles research, diagnostic intake and first-principles design engine for any subject. Use whenever the user wants something built, designed, optimised, tuned, solved, trained, unlearned or reworked and the outcome depends on parameters, constraints and side effects, in any domain, even if the request looks simple and the user does not ask for analysis. It always starts by researching each of 7 universal dimensions with at least one live search each from official sources, supplemented by forensic-audit, then forces an intake before any solution or code, a systems analysis that includes how the result is perceived and controlled by its users, a closed verification loop with an approval gate for quality upgrades, and a clean delivery measured against the researched criteria. For a plan tracked in ./docs use docs-first-planner (it embeds this skill as phase 1.5); to check an existing output use forensic-audit.
---

# First-Principles Architect

A wish arrives as a sentence, rarely as a specification. An answer produced straight from that sentence rests on guessed parameters, unspoken constraints and unexamined side effects, and fails in those places. This skill puts thinking first: understand the system, find what is missing, verify what is claimed, and only then deliver.

It combines first-principles thinking, systems engineering (INCOSE: needs, requirements, constraints, verification), closed-loop control, cognitive ergonomics and Failure Mode and Effects Analysis (FMEA). The structure applies to any subject; the subject's vocabulary is filled in at runtime. Write everything the user reads in the user's language.

## Where this skill fits

| The user wants | Use |
| --- | --- |
| A built, designed, calibrated or optimised result, delivered now, without tracking in `./docs` | **this skill** |
| A plan stored, approved and tracked in `./docs` (same 7 dimensions, no delivery) | `docs-first-planner` |
| An existing output or claim checked or fact-checked | `forensic-audit` |
| Evidence of a failure explained and fixed | `forensic-audit` (Principle 6); return here when the fix needs a redesign |
| A security review | `forensic-security-audit` |

## Translate, do not hardcode

Derive the subject, governing mechanisms, vocabulary and metrics from the request and live sources. Phrase every question, analysis part and deliverable in that vocabulary. Never carry terms, thresholds or numbers over from another subject: a number right elsewhere is an unverified claim here.

## The 7 universal dimensions

| # | Dimension | Question it answers |
| --- | --- | --- |
| D1 | **Baseline** | What is the current state, history, starting point and context? |
| D2 | **Target** | What is the measurable, explicit end state, and what are the success criteria, both objective and as experienced? |
| D3 | **Hard constraints** | Which physical, biological, cognitive, infrastructural, legal or contractual limits cannot move? |
| D4 | **Failure modes** | What fails catastrophically if an assumption is wrong? |
| D5 | **System dynamics** | Which side effects and parameter shifts appear elsewhere in the system when a choice or intervention is made? |
| D6 | **Resource budget** | How much time, attention, capacity, money, hardware or energy is available? |
| D7 | **Reversibility** | Is the intervention one-way or recoverable, including an undo or escape while it is in use? |

## Phase 0: Principles research (always, whatever the request)

A user can name what they want, but rarely what a good result of that kind must satisfy, and your own knowledge is only a hypothesis. On every request, even a short or familiar one, research the principles first across D1 to D7.

1. **Name the kind of subject and apply the complexity switch (single-topic vs. composite decomposition).** State in one line what is being built, designed, calibrated or solved, and for whom. Then classify the request:
   - **Single-topic** (one isolated question, parameter adjustment or single element): research as one unit across D1 to D7.
   - **Composite** (a complete end-to-end result, workflow, process or multi-stage creation): before searching, decompose into **3 to 6 sub-topics** (the natural sequential stages from start to finished result) plus **4 lifecycle safeguards**:
     1. *Preparation and first-run readiness:* checking prerequisites or initial settings once idempotently without repetition on later runs, adapted to available capacity.
     2. *Handoff and scale continuity between sub-topics:* feeding the output of one stage into the next without loss, truncation, drift or misgrouping as volume or duration grows.
     3. *Coexistence with the surrounding environment during execution:* capping active load to a safe fraction of available capacity and preventing premature sleep, interruption or disruptive prompts during long runs.
     4. *Ongoing use, selective recovery and clean delivery:* starting a next run while the previous finishes, re-running one adjusted or failed sub-topic without redoing earlier verified stages, and delivering a clean final result.
2. **Research each of the 7 dimensions with at least one live search per dimension** (at least 7 distinct queries before any question to the user; when composite, distribute across the 3 to 6 sub-topics and 4 lifecycle safeguards). Phrase each query in the subject's vocabulary from the matching neutral question, producing 7 distinct layer-specific queries without repetition:

| Dim | Neutral research question for this kind of subject |
| --- | --- |
| D1 | What must be established about the current state, history and context, and how is it normally measured or inventoried? |
| D2 | Which success criteria and standards exist for a result of this kind, and how are they measured, objectively and as experienced? |
| D3 | Which physical, biological, cognitive, legal, safety or contractual limits apply, and what are their values? |
| D4 | Where do results of this kind usually fail, and what are the early warning signs? |
| D5 | Which side effects and parameter couplings appear elsewhere when one choice or intervention is made? |
| D6 | How much time, effort, capacity or cost does this normally need, and what drives it? |
| D7 | Which steps are one-way, which order is safe, and how is an undo, selective stage retry or rollback done? |

   **Search with `forensic-audit`, not a general web search.** Read its SKILL.md (via `compress_context` with `section="Principles,Pre-build use (principles research)"` when available) and follow Principle 4: when `search_website` (`web-search` MCP) is available, use concise 4 to 6 core-term queries—grouping related queries or primary URLs into batch calls via `search_website(queries_or_urls=[...], auto_open_top=1)` (or inline `"open: <query>"`, up to 10 items per call) for persistent caching, delta block re-slicing and 1-turn authority-ranked primary URL opening (or pass `filter_query` on long catalogs) to reach 🔎 SOURCED. Check `./docs/index.md` for `## Search keywords` first: when present and in the project's domain, include 1 to 3 matching keywords per query (1 to 2 leading vision/scale priority terms for architecture, interface or workflow queries, or 1 to 2 technical/methodological terms for external standards, specifications or scientific queries, never prepending abstract vision terms to external standard queries).
   **Step 2B Adversarial Disconfirmation & Triple Actuality/Typology Check:** Do not search only for confirmation (Step 2A). On uncertain assumptions, contested thresholds or legacy practices, run an active disconfirmation search (Step 2B: *has this standard, rule or method been withdrawn, superseded, falsified or restricted?*) and verify on every cited norm: (a) *Existence at time horizon $t$* (still in force, not repealed or replaced), (b) *Typology* (strict binding outcome obligation vs. flexible guideline), and (c) *Higher authority* (not overruled by a higher jurisdiction or primary specification). On norm decay or disconfirmation, trigger a fail-closed rollback to Phase 0.
   **Only official sources count as evidence.** Accept only the source hierarchy of Principle 6: (a) law and formal standards, (b) regulators and public authorities, (c) primary manufacturer, specification or framework documentation, (d) accredited guild/trade guidelines and peer-reviewed science. Blogs, forums, commercial/marketing pages, templates, course material, aggregators and summaries are not evidence. Without an official source, record ⚠️ NO SOURCE FOUND and tell the user in the note; never fill the gap from a weaker source. Record conflicts between official sources with both sources.
3. **Keep an internal criteria register, including Control Point 1 (2 pros and 2 cons from subject to solution):** `dimension_or_subtopic | criterion | 2 pros & 2 cons (from subject to solution) | measurable threshold or test | official source + status label`. For the subject (and each sub-topic when composite), record **2 pros** (two verified strengths/mechanisms from subject to solution) and **2 cons** (two verified drawbacks, failure points or trade-offs from subject to solution). Unsourced thresholds stay unverified (⚠️ NO SOURCE FOUND or 🔍 SNIPPET).
4. **Supplement with the forensic audit (10 orthogonal claim/component searches) using Batch Prompting & DAST/CoD (`arXiv:2511.04108`).** Run `forensic-audit` in COMPACT pre-build mode on the **request itself**: whereas D1–D7 ask what each system layer requires, P1–P10 test 10 concrete claims, components, parameters and edge cases of the request (distributed across the sub-topics and 4 lifecycle safeguards when composite)—producing 17 distinct queries without repetition. Bundle the 7 (D1–D7) + 10 (P1–P10) queries and analyses (**Batch Prompting**, suppressing overthinking and self-doubt loops by 74–76%, without ever imposing counterproductive hard `"use at most X tokens"` caps) under a **Difficulty-Adaptive Budget (DAST)**: use concise *Chain-of-Draft (CoD)* density for structural D1–D7 dimensions and reserve full deep reasoning for complex P1–P10 points and Step 2B disconfirmation checks. Prefer delegating this combined web-research batch (`search_website(queries_or_urls=[...])`) to a `research` or `self` subagent, followed by a **Zero-Trust Context-Purge** (returning only clean `#schema:` registers and verified facts, purging raw scratchpads). Never copy reference examples into the deliverable.
5. **Use the register** as evidence in Phase 1, Phase 2 part 8, and the Phase 3 pre-delivery check. Re-run research for any part changed in Phase 1 or Gate A. If `forensic-audit` cannot be loaded, apply its rules yourself and say so in the note.

## Phase 1: Diagnostic intake (boundary and constraint check)

Do not produce a final step list, configuration or deliverable here: it would rest on unconfirmed dimensions.

1. Map the request onto D1 to D7 (and onto the 3 to 6 sub-topics and 4 lifecycle safeguards when composite). Mark each dimension **known** (with evidence), **assumed** (state the assumption) or **missing**, using the Phase 0 register as first evidence.
2. Correct factually wrong assumptions straight away, with the source, so the user answers on correct premises.
3. Rank the missing and assumed dimensions by leverage (a wrong D3, D4, D7 or lifecycle safeguard costs most) and ask **at most 3 to 4 compact questions** (or 4 to 6 in `docs-first-planner` for a composite wish) grouped by sub-topic and lifecycle safeguard. Never walk through all 7 as a checklist.
4. **Pre-Grill Invariant Gate, Control Point 2 (2 pros and 2 cons from subject to solution) & Cognitive Ergonomics (Hick's Law & Progressive Disclosure):** Filter options against standing constraints and prior exclusions (never propose a previously rejected direction). Phrase each question naturally, offering **3 to 5 choices per decision point** with your pre-researched Smart Default first marked "(Recommended)" so the user can confirm in one word, and for every recommended option or decision state **2 pros and 2 cons from subject to solution**, with "or tell me to decide". Place extensive supporting tables at the bottom inside `<details><summary>...</summary></details>` sections.
5. Look up anything answerable from existing materials instead of asking. If every critical dimension is already known, say so, state any remaining assumption in one line and continue to Phase 2.
6. End the message with the questions written out as plain text, so the last thing the user reads is a question they can answer. A question tool may be used in addition, never instead.

## Phase 2: Systems analysis and risk audit

Once the missing dimensions are answered, run this audit in 8 fixed parts in the exact vocabulary and metrics of the subject, skipping none. Show conclusions in a few lines per part (wrapping large detail tables in `<details><summary>...</summary></details>`); give the fully written-out analysis when the user asks for the "full report".

**Simplicity Ladder (walk top-down on every design choice):** (1) *Necessity (YAGNI)* — must this part exist at all?, (2) *Reuse (DRY)* — does it already exist in the whole?, (3) *Existing standard capabilities* — can standard baseline means handle it directly?, (4) *Built-in environmental safeguards* — can native environment constraints enforce it?, (5) *Already chosen means* — can already selected resources cover it?, (6) *Minimal custom addition* with early boundary checks (Look-Before-You-Leap / LBYL).

1. **First principles.** The underlying physical, physiological, chemical, thermodynamic, economic, legal, cognitive or computational mechanism governing the outcome.
2. **Critical success factors.** The non-negotiable process conditions without which the result cannot succeed.
3. **Input and component audit (contamination and quality).** Which inputs, raw materials, environmental stimuli or dependencies degrade the result when their properties or ratios are wrong, and how they are isolated beforehand (including lifecycle safeguard 1).
4. **Causal chain and parameter coupling (state-parameter matrix).** For every option, mode, variable and sub-topic handoff, trace: *choice or trigger -> sub-parameters and conditions -> processing layer -> physical or technical execution*. State which dependent settings change when another option is chosen, apply the Simplicity Ladder, and record **Control Point 2** for each key decision.
5. **Perception, cognition and sensory ergonomics (human or organism in the loop).** Secure three axes for perceived experience alongside objective performance:
   - *Transition and latency feedback (no dead silence):* immediate sensory feedback suited to the medium.
   - *Cognitive load and signal-to-noise (Hick's Law & Progressive Disclosure):* hierarchical chunking, smart defaults, collapsible `<details>` sections.
   - *Control, predictability and recovery:* immediate confirmation and safe fallbacks (undo, cancel, selective sub-topic retry, escape) preserving earlier verified stages while keeping the environment responsive.
   Without a living organism or observer in the loop, state that in one line and move on.
6. **Efficiency and scalability (throughput and overhead).** Quantify effort against yield on *time and throughput* (at scale) and *capacity and density* (load per unit of input, plus safe load caps from lifecycle safeguard 3).
7. **Pitfalls and breaking points (failure modes).** Where the system, organism, material or process breaks under load or at stage handoffs, and the early warning signs.
8. **Empirical falsification (misconception).** Which common assumption, intuition or standard method in this subject is factually wrong, outdated or counterproductive according to first principles and Step 2B disconfirmation, backed by a source.

## Phase 2.5: Closed-loop verification and approval gate

Phase 3 starts only after both gates pass.

**Gate A: circuit breaker and rollback.** Trip it on:
1. *Parameter mismatch:* a chosen mode or step needs sub-parameters that are missing, conflicting or unsupported by the layer below.
2. *Confidence gap:* a link rests on an assumption instead of a verified mechanism or source (or fails Step 2B's actuality/typology/authority check). A link passes only with a 🔎 SOURCED primary source, a ⚙️ EXECUTED test/measurement, or actual material/data. A 🔍 snippet, 🧠 inference, 🧮 hand calculation or unconfirmed user statement stays unverified ("80% sure" is false precision).
3. *Constraint violation:* working out the chain collides with hard constraints (D3) or resource budget (D6).

On a trip, run an **internal research loop** (back to Phase 2) to verify missing specifications and repair the matrix. If the requirement is physically, technically, legally or economically impossible (deadlock), do a **hard reset to Phase 1**: name the exact conflict with its source and put adjusted boundary conditions to the user.

**Gate B: proactive optimisation and approval (unknown unknowns).** From Phase 2 draft a **compact, numbered list of high-value quality and experience upgrades** separating "it works technically" from "it feels and performs superior". For a large design, ask the user first which to include before writing Phase 3 in full.

## Phase 3: Delivery (end-to-end path integrity and clean hand-over)

Deliver only after Gate A and Gate B: the definitive, chronological and exhaustive step plan, configuration, instructions or deliverable.

- **End-to-end path integrity (no placebo controls, no dead paths).** Every option, mode or approved upgrade must be wired through to the execution layer: *selection -> validation -> conditional sub-settings -> perceptual feedback -> actual execution*, covering all 7 dimensions (plus all 3 to 6 sub-topics and 4 lifecycle safeguards when composite) and the validated outcomes of Phase 2 and 2.5.
- **Clean hand-over (closed mandate, client -> executor).**
  1. *No scaffolding or process leakage.* Leave internal working data, technical parameters, measurements, identifiers, method names, status indicators and under-the-hood mechanics out of the visible end result.
  2. *No unrequested interpretation or meta-commentary.* Add no summaries, conclusions, status updates, progress arrows, extra titles, subtitles or explanatory captions of your own to the delivered work.
  3. *Strict content whitelist.* Include only elements and texts the client supplied or approved in Gate B.
  4. *Carrier stays clean.* The supporting structure (form, technique, layout or medium) stays fully subservient and invisible as a carrier.
- **Pre-delivery check (closed loop, including Control Point 1 & Control Point 2).** Measure the result against the Phase 0 criteria register with a real measurement or test wherever measurable, and verify that both control points (**Control Point 1** and **Control Point 2**: **2 pros and 2 cons from subject to solution**), the Simplicity Ladder and all 4 lifecycle safeguards (when composite) are complete. A miss goes back for repair and re-check.
- **Honesty stays outside the deliverable.** Report unverified links, assumptions and source gaps in a short "before you use this" note around the deliverable (using `<details><summary>...</summary></details>` for long audit trails), never inside the delivered work.
- When writing or modifying any file or deliverable, follow `forensic-audit` Principle 7: delegate the change to a clean execution subagent with a lossless `compress_context` Context Pack (`--signatures` + target sections/symbols + scoped `.md` section).

## Sourcing and evidence

All factual claims (criteria, thresholds, limits, methods) come from sources researched through `forensic-audit` (Phase 0 step 2); own knowledge only gives hypotheses to test. Confidence rests on source status alone: no source, no confidence; say "unverified" instead. An `ERROR:` response never counts as 🔎. Never write that something was searched, opened or measured when it was not.

## Gotchas

- Never fill a dimension from a blog, forum, template or commercial page: without an official source it stays ⚠️ NO SOURCE FOUND.
- Never skip Phase 0, its seven searches, Step 2B disconfirmation, the complexity switch, or Control Point 1 & Control Point 2.
- Never impose hard `"use at most X tokens"` caps; use Batch Prompting and DAST/CoD density with a Zero-Trust Context-Purge.
- Never ask all 7 dimensions at once; pick the 3 to 4 (or 4 to 6 in the planner) that are missing, with the Smart Default first.
- Always walk the Simplicity Ladder top-down and translate all 8 analysis parts into the subject's vocabulary, including perception and control in use (Phase 2, part 5).
- Never guess a missing parameter; on doubt, norm decay or conflict activate Gate A.
- Prove depth in Phase 2, and keep the Phase 3 deliverable free of technical meta-labels and unrequested text.
