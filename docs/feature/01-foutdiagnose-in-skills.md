---
id: feature/01
title: Foutdiagnose in alle skills
category: feature
status: done
summary: Alle skills herkennen de echte oorzaak van een fout (log, symptoom) en geven een geteste fix, in elk vakgebied.
tags: [skills, diagnose, forensic-audit, voorbeelden]
created: 2026-10-23
updated: 2026-10-23
related: [feature/02, feature/03, feature/04]
---

# Foutdiagnose in alle skills

## Why
De skills beoordelen output, maar herkennen niet wat er mis is als er al iets fout gegaan is (foutmelding, stacktrace, mislukte test, mislukt gerecht) en komen niet met een geteste oplossing. Visie: "Gaat er iets fout, dan herkennen ze de echte oorzaak in de foutmelding of het symptoom en komen ze met een concrete, geteste oplossing, zonder een bewuste beveiliging te verzwakken."

## Starting point (audit findings)
- Verified: geen skill heeft een foutdiagnose-regel (alle `SKILL.md` gelezen). Aanpak sluit aan op Google SRE "Effective Troubleshooting" (hypothese, test, behandel; 🔎). Config en secrets in de omgeving: 12factor Config (🔎). Traceback is context, foutmelding is de kern: Python docs (🔎).
- Corrected: n.v.t.
- Unverified: ECE R90 (🔍 alleen snippet); bakken, OBD-code P0301, hondentraining, huishoudapparaten niet bij primaire bron gecontroleerd (🚫). Voorbeelden zijn illustratief; veiligheid (remmen, pijn, agressie, elektra) verwijst naar een professional.

## Decisions (from the grill)
| Question | Decision | Reason |
| --- | --- | --- |
| Waar staat de tekst? | Per skill een eigen variant | Past bij het vak van elke skill |
| Drift | Geen sync-script; gelijke stapnamen en README-afspraak | Keuze gebruiker |
| Algemeenheid | Domeinneutrale kern, voorbeelden uit meerdere vakgebieden | Eis gebruiker |
| Verificatie | 5 vaste testgevallen door `forensic-audit` (uitgebreid van 4) | Meetbaar |
| Visie | Aangepast met de diagnose-zin | Keuze gebruiker |

## Scope
- In: Principle 6 en Diagnosis-blok in `forensic-audit` (plus triggerwoorden); varianten in `forensic-security-audit`, `forensic-site-audit`, `docs-first-planner` (incl. `plan-template`, `audit-brief`); richtlijn 6 in `CLAUDE.md`, `GEMINI.md`, Cursor-rule; `EXAMPLES.md` en README.
- Out (explicitly not doing): geen nieuwe skill; geen sync-script; geen automatische fixes buiten bestaande toestemmingsregels; geen bestaande comments of docstrings verwijderen; geen wijziging aan `docs_tool.py` of de MCP-server.

## Approach
Stapnamen in elke skill: Quote, Signal, Guard, Hypotheses, Fix, Confirm.
1. Schrijf de domeinneutrale kern en pas Principle 6 en het Diagnosis-blok toe in `forensic-audit`.
2. Voeg varianten toe aan security-audit, site-audit en planner (met `plan-template` en `audit-brief`).
3. Voeg richtlijn 6 toe aan `CLAUDE.md`, `GEMINI.md` en de Cursor-rule.
4. Voeg de 5 testgevallen en voorbeelden toe aan `EXAMPLES.md`, en een zin aan de README.
5. Draai de 5 testgevallen en leg het resultaat vast onder `## Verification`.

## Acceptance criteria
- [x] Elke skill bevat de zes stapnamen in dezelfde volgorde (`Select-String` op alle `SKILL.md`).
  Check: `(Select-String skills/*/SKILL.md -Pattern '\*\*Hypotheses' -List | Measure-Object).Count` -> `4`
- [x] Traceback-case: Diagnosis-blok `Symptom | Root cause | Fix | Confirm` met `config.py:110` als oorzaak, niet "startup failed".
- [x] Traceback-case: `validate_production_secrets` blijft staan, er wordt niet om een geheim gevraagd.
- [x] Brood-, remblok-, hond- en huishoudapparaat-case leveren hetzelfde blok; bij remmen, pijn, agressie of elektra staat een doorverwijzing naar een professional.
- [x] `docs_tool.py check` geeft `docs OK`.
  Check: `python skills/docs-first-planner/scripts/docs_tool.py check` -> `docs OK`
- [x] Geen IT-specifieke woorden in de kern, alleen in voorbeelden (opgelost en geverifieerd via `feature/03`).
  Check: `(Select-String skills/forensic-audit/SKILL.md -Pattern 'stack trace|first frame|config key' | Where-Object { $_.LineNumber -ge 71 -and $_.LineNumber -le 85 } | Measure-Object).Count` -> `0`

## Risks and open points
- Varianten kunnen uit elkaar lopen; mitigatie: gelijke stapnamen en README-afspraak.
- Voorbeelden buiten IT zijn niet bij primaire bronnen gecontroleerd.
- Het blok komt alleen in het rapport als de input een fout bevat, om rapporten kort te houden.
- Visie-antwoord "1" is gelezen als "ja".

## Relations
- Is basis voor: `feature/02` (docs-regressiecheck, zelfde skillbestanden).

## Verification
| Criterion | How checked | Result |
| --- | --- | --- |
| Zes stapnamen in elke skill | PowerShell: positie van Quote, Signal, Guard, Hypotheses, Fix, Confirm per `SKILL.md`, oplopend in alle vier | Voldaan |
| Traceback-case | Blinde subagent met alleen `forensic-audit/SKILL.md`, 5 ruwe prompts | Voldaan: oorzaak `config.py` r.110 (niet "startup failed"), guard blijft, geen geheim gevraagd |
| Brood, remblok, hond, wasmachine | Zelfde test | Voldaan: Diagnosis-blok aanwezig; doorverwijzing naar garage, dierenarts en monteur/elektricien; wasmachine: stekker eruit |
| `docs_tool.py check` | Uitgevoerd | `docs OK` |
| Varianten security-audit, site-audit, planner | Per skill een blinde subagent met alleen die `SKILL.md`: geplakte log met wachtwoord en voorstel de check uit te zetten; Playwright-run met 422, TypeError en voorstel de timeout te verhogen; planner-simulatie fase 0 tot 2 met dezelfde traceback (niets geschreven) | Voldaan: wachtwoord gemaskeerd en als gecompromitteerd gemarkeerd, check blijft aan; eerste falende event (422) en test- versus productfout benoemd, timeout niet verhoogd; bug (geen security-route), oorzaak als Impact-punt met status hypothese, acceptatiecriterium dat de guard nog weigert |
| Geen IT-woorden in de kern | Op verzoek van gebruiker volledig domeinneutraal gemaakt in `feature/03` (0 treffers op `stack trace`, `first frame`, `config key` in Principle 6) | Voldaan |

Beperkingen van deze test:
- Alle vier de varianten zijn getest, maar alleen met de traceback- of een IT-casus; de varianten buiten IT (bijvoorbeeld de planner met een brood-wens) zijn niet getest.
- Alle 10 auditpunten waren 🚫 NOT SEARCHED (zoeken bewust overgeslagen); de agent beoordeelt zichzelf.
- Het brood-antwoord noemt getallen (15-20% starter, 24-26 °C, zout 2%) uit eigen kennis (🧠), niet uit een bron.
- De secret-guard is nagebootst (`python`, 3 invoeren) en niet tegen de echte infradoc-code gedraaid.