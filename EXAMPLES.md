# Examples

Concrete before/after illustrations of the principles and skills in this repo.

---

## 1. No Fake Green

**Request:** "Verify that saving the API token works."

❌ **Fake green**
```
POST /settings/token -> 200 OK
Screenshot file exists: settings.png
Result: PASS
```

✅ **Verified**
```
BEFORE  token column: NULL
AFTER   token column: ciphertext (not equal to input), decrypts to input
UI      success message visible, shown after reload
LOG     no plaintext token in app log, console or HAR
Result: PASS
```

---

## 2. Zero-Hardcode Discovery

**Request:** "Test the settings page."

❌ **Hardcoded**
```python
page.goto("/settings")
page.click("#save-btn")
expect(page.locator(".toast")).to_have_text("Saved!")
```
Breaks on a renamed route, id or copy change.

✅ **Discovered at runtime**
```python
for url in crawl(base_url):                       # routes from nav, sitemap, router, OpenAPI
    page.goto(url)
    for control in accessibility_tree(page):      # role + accessible name
        classify(control)                         # input | submit | tab | destructive ...
        interact(control, data=from_schema(control))
```

---

## 3. Closed-Loop Repair (visual)

**Finding:** primary button measured at 32×36 px, below the 44×44 px target.

❌ **Loosen the check**
```python
assert box.height >= 32
```

✅ **Fix the component, re-run, re-capture**
```
Deviation  button 32×36 px           (threshold ≥ 44×44)
Changed    button min-height/width -> 44px via shared design token
Retest     44×44 px ✅   new screenshot captured: settings-interactive
Status     🔁 ROLLBACK→✅
```

---

## 4. Compact Report

```
| # | Type        | BEFORE              | AFTER                 | Source          | Red-team | Screenshots | Status |
|---|-------------|---------------------|-----------------------|-----------------|----------|-------------|--------|
| 1 | Impact      | no session          | JWT stored, 401 on bad| RFC 7519        | token reuse blocked | login-initial, login-interactive | ✅ PASS |
| 2 | Impact      | secret col NULL     | ciphertext in DB      | OWASP ASVS V6   | no plaintext in logs | settings-interactive | ✅ PASS |
| 3 | Uncertainty | target 32×36 px     | 44×44 px              | WCAG 2.5.8      | mobile viewport ok | settings-mobile | 🔁 ROLLBACK→✅ |
```

---

## 5. Project Context Block (site audit)

```
PROJECT: InfraDoc
GOAL: Implement missing Login and Settings pages and verify them visually.
BACKEND: Pydantic V2 + PostgreSQL (SSOT), POST /api/v1/auth/login, JWT + tenant context in a reactive state store.
UX REQUIREMENTS: Hick's Law with smart defaults from INFRADOC_ADMIN_USER / INFRADOC_ADMIN_PASS (local only);
                 Fitts' Law ≥ 44×44 px; inline error messages; progressive disclosure on Settings
                 (1. VCS/GitHub auth: PAT primary, SSH key, username/password;
                  2. tenant & roles: Tenant Admin, Engineer, Viewer, RLS isolation;
                  3. system & database status: PostgreSQL SSOT, encryption).
SECURITY: LBYL; secrets encrypted at rest; never logged in plain text.
ACCEPTANCE: No mocks; SQL proves persistence and encryption; initial + interactive screenshots per page
            stored in test-artifacts, reviewed and approved; 100% coverage of discovered pages.
```

The skill reads this block as **parameters**. Page routes, field names and button labels are still discovered at runtime.

---

## 6. Diagnose Before You Fix (domain-neutral discovery + live standards)

> **Illustrations of the method only.** Never copy numbers or meanings from this table as facts; on every run the agent must execute step 1 (**Discover**) and search live (`search_website`) for the specific make, model, species, stack or jurisdiction and open the primary source (`🔎 SOURCED`). Compact report block: `Symptom | Root cause | Fix | Confirm | Source`.

| # | Topic | 1. Discover & live source hierarchy (`search_website`) | 2–4. Quote, Signal & Guard | 5–7. Hypotheses (cheap test), Fix & Confirm |
|---|-------|-------------------------------------------------------|----------------------------|---------------------------------------------|
| 1 | Software / IT | Derive framework and config from project files; open framework docs + OWASP ASVS / NIST SP 800-63B (free open primary counterpart to ISO/IEC 27001) | Quote the raised exception at its origin frame (`config.py:110`); "startup failed" is only the wrapper. Guard: deliberate fail-closed secret check | Test variable presence/length without printing the secret. Fix: user generates and stores a high-entropy secret in the environment/secret manager. Confirm: startup succeeds AND empty/short values are still rejected |
| 2 | Food / Baking | Derive dough type and process; search food-safety and guild authorities (NVWA / Bakery Hygiene Code / Codex Alimentarius as open counterpart to ISO 22000) | Quote user observation; decisive signal is the first deviation (dough never rose during bulk fermentation), not the flat baked loaf. Guard: food-safety temperature/hygiene limits | Test fermentation activity (levain float/rise test, dough thermometer, salt ratio check). Fix per guild standard; Confirm: measurable volume increase in a marked vessel before baking |
| 3 | Automotive / Mechanical | Ask or derive make/model/VIN; open UNECE Regulation R90 (free full PDF on `unece.org`) and RDW APK handbook (`apk-handboek.rdw.nl`) | Quote symptom (part does not fit / squeals, or diagnostic trouble code). Guard: type approval (ECE R90) and braking safety — never modify a friction part to make it fit | Check OEM/VIN part number and ECE R90 marking; for a trouble code, run the manufacturer's diagnostic swap test. High consequence: stop and have a qualified mechanic fit and test |
| 4 | Animal / Veterinary | Derive species, age and behaviour cue; search veterinary and behaviour guidelines (KNMvD / LICG / peer-reviewed veterinary literature) | Quote behaviour; decisive signal is the pain indicator (whining when touched on the back), not ignoring the cue. Guard: animal welfare and pain exclusion before training | Rule out physical pain first. High consequence (animal in pain): stop training and refer to a veterinarian; only test training variables (distraction, reward timing) after medical clearance |
| 5 | Electrical / Appliance | Derive appliance brand/model and error code; open official manufacturer service/error documentation and electrical safety rules (`wetten.overheid.nl` Bbl / Arbobesluit as open counterpart to NEN 1010 / NEN 3140) | Quote displayed code and symptom; decisive signal is the drain failure + live mains hazard. Guard: de-energise (pull the plug) before touching internal components | After unplugging, inspect filter and hose per manufacturer manual; if the fault is in wiring or internal pump assembly, refer to a certified technician. Confirm: test drain cycle with zero error code |
