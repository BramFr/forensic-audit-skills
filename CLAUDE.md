# Forensic Audit Guidelines

Behavioral guidelines for verifying AI-generated output and web applications. Merge with project-specific instructions as needed.

**Tradeoff:** These guidelines bias toward rigor over speed. For trivial tasks, use judgment.

For the full procedures, see `skills/forensic-audit/SKILL.md` and `skills/forensic-site-audit/SKILL.md`.

## 1. Zero-Trust Baseline

**Claims are hypotheses until measured.**

- Treat earlier claims, assumptions and "it already works" as unproven.
- Separate proven facts from assumptions; state which is which.
- Don't please the user. Factual, physical and legal correctness comes first.

## 2. No Fake Green

**Evidence, not appearance.**

- A compile, a 200 response or an existing screenshot file is not proof.
- Prove behaviour physically: run it, query the database, look at the rendered result.
- Prefer live systems over mocks. If you must mock, say so and don't call it verified.

## 3. Zero-Hardcode Discovery

**Find it at runtime, don't write it down in advance.**

- Never fix routes, selectors, button names or expected texts in tests.
- Locate elements through roles and accessible names; derive test data from the schema.
- A test that breaks on a label or layout change is a defect in the test.

## 4. Closed-Loop Repair

**Fix the thing, not the test.**

- On deviation: change the code, re-run from the baseline, and re-capture the evidence.
- Never loosen a threshold to turn a result green.
- Same error three times: change approach. Ten attempts: stop and report honestly.

## 5. Compact, Honest Reporting

**Conclusions only, and say what you could not verify.**

- One line per step; tables over prose; details only on deviation.
- Always finish with a negative declaration: what was not tested or substantiated.
- Cite primary sources (standards, specs, official docs), never SEO content.

---

**These guidelines are working if:** audits report real deviations, rollbacks are rare after the first pass, and the negative declaration is never empty by accident.
