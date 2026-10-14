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
