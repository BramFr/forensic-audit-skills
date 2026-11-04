---
id: feature/21
title: Uitgebreid 3-profielen rapport (benchmark-1request.md) en README-sync
category: feature
status: done
summary: Verrijk benchmark-1request.md met feature/20 context (<=6.5KB) en sync alle 3 README.md bestanden.
tags: [docs-first-planner, forensic-audit, web-search, mcp, benchmark, token-efficiency, feature-20, readme, diataxis, iso-25010-23]
created: 2026-11-03
updated: 2026-11-03
related: [feature/10, feature/18, feature/19, feature/20]
---

# Uitgebreid 3-profielen benchmark-rapport (`docs/benchmarks/benchmark-1request.md`) met `feature/20`-verantwoording en README-synchronisatie

## Why
Na `feature/20` bevat `docs/benchmarks/benchmark-1request.md` de 3 live gemeten `#schema:` tabellen (`3.004 B`), maar mist het bestand nog een expliciete inhoudelijke en klikbare referentie naar `docs/feature/20-reproduceerbare-3-profielen-benchmark-en-regressiefix.md` (en `feature/10`, `feature/18`, `feature/19`), legt het de 3 architectuur-fixes uit `feature/20` (live 3-profielen ketenmodel `-87.2%`, exact-match sectie-deduplicatie `16.060 B -> 10.223 B <= 10.240 B`, en `search_website.json = 2.565 B <= 3.100 B`) en de actieve token-estimator (`tiktoken o200k_base` vs. `ceil(utf8_bytes / 3.8)` fallback) niet uit, en verwijzen `README.md`, `mcp/context-compressor/README.md` en `mcp/web-search/README.md` nog nergens naar het nieuwe benchmark-rapport of `feature/20`.

Dit plan verrijkt `scripts/benchmark_1request.py` en `docs/benchmarks/benchmark-1request.md` tot een volledig zelfstandig, reproduceerbaar audit- en benchmark-artefact (`<= 6.500 B`, ruim binnen het `<= 10.240 B` inline budget), trekt de 3 `README.md`-bestanden gelijk conform het Diátaxis Reference-principe, en houdt alles lokaal ongecommit klaar voor eigen tests met de Conventional Commit-referentie `feat(benchmark): live 3-profile benchmark report, section deduplication and <=3.1KB schema (feature/20)`. Zoals de productvisie in `docs/index.md` stelt: *"Deze skills laten een AI-agent controleren in plaats van instemmen. Ze gaan uit van nul vertrouwen en eisen bewijs in plaats van schijn... De rapportage is compact en eerlijk over wat niet is geverifieerd."*

## Starting point (audit findings)
- **Verified (🔎 SOURCED + ⚙️ EXECUTED):**
  - `scripts/benchmark_1request.py` (`generate_benchmark_data` L275–L583, `run_benchmark` L586–L618) berekent alle 3 `#schema:` tabellen live en slaagt met `BENCHMARK OK` (`v1 = 292.313 tok / -70.5%`, `v2 = 126.831 tok / -87.2%`).
  - `docs/benchmarks/benchmark-1request.md` is nu `3.004 B` en bevat alleen een 1-regelige header boven 3 fenced codeblokken zonder klikbare link naar `../feature/20-reproduceerbare-3-profielen-benchmark-en-regressiefix.md`, zonder methodologie/normenkader en zonder estimator-vermelding.
  - `README.md` (`#### Lossless Token Savings` L167–L178 en `## Repository Layout` L206–L239), `mcp/context-compressor/README.md` en `mcp/web-search/README.md` tonen nog enkel de pre-`feature/18` deelmetingen en noemen `docs/benchmarks/benchmark-1request.md` en `feature/20` niet.
  - **Step 2B Disconfirmation & Norm-actualiteit (🔎 SOURCED):**
    1. **ISO/IEC 25023:2016 + ISO/IEC 25010:2023:** ISO/IEC 25010:2011 is vervangen door **ISO/IEC 25010:2023**, terwijl **ISO/IEC 25023:2016** vigerend blijft voor kwantitatieve performance-efficiency metingen; beide normen horen samen vermeld te worden.
    2. **IETF RFC 9111 (STD 98):** RFC 7234 is ingetrokken door **RFC 9111**; verwijzingen voor HTTP caching (`ETag` / `If-None-Match` / `304 Not Modified`) blijven strikt op RFC 9111 (naast RFC 3986, RFC 7763, RFC 8259 en NIST SP 800-53 Rev. 5.2.0 SI-7).
  - **Control Point 1 (2 pros en 2 cons van onderwerp naar oplossing per deelonderwerp):**
    1. *Deelonderwerp 1 (Verrijking `docs/benchmarks/benchmark-1request.md` in `scripts/benchmark_1request.py`):* **PRO 1:** Zelfstandig leesbaar bewijsstuk met directe klikbare link naar `feature/20`, `feature/19`, `feature/18` en `feature/10`; **PRO 2:** Transparante weergave van zowel de 3 profielen, de 2 regressiefixes (`<= 10.240 B` sectie-dedup en `<= 3.100 B` schema) als de actieve token-estimator; **CON 1:** Bestandsgrootte stijgt van `3.004 B` naar `~5.200 B`; **CON 2:** Moet strikt `<= 6.500 B` blijven voor 1-turn inline reads.
    2. *Deelonderwerp 2 (Synchronisatie van de 3 `README.md`-bestanden):* **PRO 1:** Eén consistente waarheid (Single Source of Truth) tussen publieke README's en het benchmark-rapport conform Diátaxis; **PRO 2:** Bezoekers zien direct de `-70.5%` (v1) en `-87.2%` (v2) ketenreductie en het pad naar `scripts/benchmark_1request.py`; **CON 1:** Raakt 3 README-bestanden; **CON 2:** Vereist een automatische check-regel op aanwezigheid van de kruisverwijzingen.
    3. *Deelonderwerp 3 (Deterministische `--check` pariteit):* **PRO 1:** Garandeert via `persisted == markdown_doc` dat het rapport op schijf nooit afwijkt van de live code-meting; **PRO 2:** Voorkomt dat handmatige edits de `feature/20` referentie breken; **CON 1:** Elke rapport-wijziging moet via `scripts/benchmark_1request.py --save` lopen; **CON 2:** Vereist deterministische rapportregels zonder flappende wall-clock milliseconden in het opgeslagen `.md` bestand.
    4. *Deelonderwerp 4 (Traceerbaarheid in `./docs` en lokale commit-voorbereiding):* **PRO 1:** Sluit de keten van `feature/20` -> `feature/21` -> `docs/benchmarks/benchmark-1request.md` met een kant-en-klare Conventional Commit 1.0.0 boodschap; **PRO 2:** Laat de git-werkboom ongecommit zodat de gebruiker alles eerst lokaal kan testen vóór push; **CON 1:** Voegt één item (`feature/21`) toe aan `docs/index.md`; **CON 2:** De daadwerkelijke `git commit` en `git push` blijven een bewuste handmatige vervolgstap van de gebruiker na lokale test.
- **Corrected:**
  - `docs/benchmarks/benchmark-1request.md` vermeldde niet welke token-estimator (`tiktoken o200k_base` vs. `math.ceil(utf8_bytes / 3.8)`) actief was en miste klikbare links naar `docs/feature/20-reproduceerbare-3-profielen-benchmark-en-regressiefix.md`.
  - `README.md`, `mcp/context-compressor/README.md` en `mcp/web-search/README.md` liepen nog achter op `feature/10` t/m `feature/20`.
- **Unverified:**
  - Geen (`0` `⚠️ NO SOURCE FOUND`, `0` `🚫 NOT SEARCHED`).

## Decisions (from the grill — Control Point 2: include 2 pros and 2 cons from subject to solution)
| Question | Decision | Reason (incl. 2 pros & 2 cons from subject to solution) |
| --- | --- | --- |
| 1. Opbouw van `docs/benchmarks/benchmark-1request.md` | **Optie 1A:** Volledig zelfstandig rapport (`<= 6.500 B`) met `feature/20` architectuur-samenvatting, methodologie/estimator-transparantie, reproductie-instructies + de 3 live `#schema:` tabellen | **PRO 1:** Volledige herleidbaarheid naar `feature/20` en de onderliggende RFC/ISO-normen in één zelfstandig bestand; **PRO 2:** 100% deterministisch gegenereerd en bewaakt via `benchmark_1request.py --check`; **CON 1:** Het bestand groeit van `3.004 B` naar `~5.200 B` (nog steeds ruim `<= 10.240 B`); **CON 2:** Vereist uitbreiding van `generate_benchmark_data()` en `--check`. |
| 2. Synchronisatie van `README.md`-bestanden | **Optie 2A:** Synchroniseer alle 3 de `README.md`-bestanden (`README.md`, `mcp/context-compressor/README.md`, `mcp/web-search/README.md`) met `docs/benchmarks/benchmark-1request.md` en `feature/20` | **PRO 1:** Single Source of Truth tussen hoofd-README, MCP-README's en `docs/benchmarks/benchmark-1request.md` conform Diátaxis; **PRO 2:** Gebruikers vinden direct het reproduceerbare benchmark-script en rapport; **CON 1:** Raakt 3 extra Markdown-bestanden; **CON 2:** Vereist een check-regel op de kruisverwijzingen. |
| 3. Registratie in `./docs` t.o.v. `feature/20` | **Optie 3A:** Nieuw plan-item `feature/21` met bidirectionele `related`-koppeling naar `feature/20` (en `feature/10`, `feature/18`, `feature/19`) | **PRO 1:** Zuivere chronologische traceerbaarheid in `docs/index.md` zonder de afgeronde scope van `feature/20` te overschrijven; **PRO 2:** Bidirectionele koppeling maakt direct zichtbaar hoe `feature/21` voortbouwt op `feature/20`; **CON 1:** Voegt één rij toe aan `docs/index.md`; **CON 2:** Vereist index-regeneratie via `docs_tool.py index`. |
| 4. Git commit & push uitvoering | **Optie 4B:** Geen `git commit` of `git push` uitvoeren; alles lokaal op schijf genereren en testen, met de kant-en-klare Conventional Commit (`feat(benchmark): live 3-profile benchmark report, section deduplication and <=3.1KB schema (feature/20)`) gedocumenteerd | **PRO 1:** Gebruiker kan alles eerst rustig lokaal testen en inspecteren vóór een commit of push naar GitHub; **PRO 2:** Geen risico op het ongewenst mee-committen van andere open bestanden in de werkboom; **CON 1:** De git-werkboom blijft lokaal op `modified`/`untracked` staan totdat de gebruiker zelf committ; **CON 2:** Vereist een duidelijke commit-instructie in het rapport en de oplevering. |

## Scope
- **In:**
  - **Deelonderwerp 1 (`scripts/benchmark_1request.py` & `docs/benchmarks/benchmark-1request.md`):**
    - Breid `generate_benchmark_data()` in `scripts/benchmark_1request.py` uit zodat `docs/benchmarks/benchmark-1request.md` (`<= 6.500 B`) naast de 3 live `#schema:` tabellen ook bevat:
      1. Een kopsectie met klikbare links naar `../feature/20-reproduceerbare-3-profielen-benchmark-en-regressiefix.md` (`feature/20`), `feature/19`, `feature/18` en `feature/10`, plus de referentie-commit `feat(benchmark): live 3-profile benchmark report, section deduplication and <=3.1KB schema (feature/20)`.
      2. Een sectie **Executive Summary & `feature/20` Regressie- en Architectuurfixes** die de 3 pijlers van `feature/20` kwantificeert: (a) Live 3-profielen ketenberekening (`989.768 -> 292.313 [-70.5%] -> 126.831 [-87.2%]` tokens over `24 -> 10 -> 7` turns), (b) Exact-match sectie-deduplicatie in `mcp/context-compressor/server.py` (`skills/forensic-audit/SKILL.md` multi-sectie `16.060 B -> 10.223 B <= 10.240 B`, `0` duplicaten), en (c) Gecomprimeerd MCP tool-schema `search_website.json` (`3.374 B -> 2.565 B <= 3.100 B`).
      3. Een sectie **Methodologie, Normenkader & Reproductie** met de actieve token-estimator (`tiktoken o200k_base` vs. `math.ceil(utf8_bytes / 3.8)` fallback), de geverifieerde standaarden (`ISO/IEC 25010:2023`, `ISO/IEC 25023:2016`, `IETF RFC 9111`, `RFC 3986`, `RFC 7763`, `RFC 8259`, `NIST SP 800-53 SI-7`) en de exacte CLI-commando's (`python scripts/benchmark_1request.py --save` en `python scripts/benchmark_1request.py --check`).
  - **Deelonderwerp 2 (`README.md`, `mcp/context-compressor/README.md`, `mcp/web-search/README.md`):**
    - Werk `README.md` (`#### Lossless Token Savings` en `## Repository Layout`) bij met de 3-profielen ketenresultaten (`-70.5%` v1, `-87.2%` v2), de `feature/18–20` optimalisaties, `docs/benchmarks/benchmark-1request.md` en `scripts/benchmark_1request.py`.
    - Werk `mcp/context-compressor/README.md` bij met `filter_query` getrapte tabelprojectie, automatische Slim Plan-Read op `./docs/<cat>/NN-*.md`, exact-match sectie-deduplicatie (`<= 10.240 B`), `@mcp.tool(output_schema=None)`, omkeerbare link-compactie en nooit-groter-guard + verwijzing naar `docs/benchmarks/benchmark-1request.md` (`feature/20`).
    - Werk `mcp/web-search/README.md` bij met `auto_open_top` / `open:`, het `<= 9.500 B` slack-herverdeelde batch-budget, de persistente SQLite WAL + RFC 3986 + RFC 9111 `ETag`/`304 Not Modified` cache, sessie-delta block re-slicing en het `<= 3.100 B` `search_website.json` schema + verwijzing naar `docs/benchmarks/benchmark-1request.md` (`feature/20`).
  - **Deelonderwerp 3 (`--check` validatie):**
    - Laat `run_benchmark(check_only=True)` in `scripts/benchmark_1request.py` tevens controleren dat `docs/benchmarks/benchmark-1request.md` strikt `<= 6.500 B` is en de klikbare referentie naar `20-reproduceerbare-3-profielen-benchmark-en-regressiefix.md` én de commit-string `feat(benchmark): live 3-profile benchmark report, section deduplication and <=3.1KB schema (feature/20)` bevat.
  - **Deelonderwerp 4 (`./docs` traceerbaarheid):**
    - Update `related` in `docs/feature/20-reproduceerbare-3-profielen-benchmark-en-regressiefix.md` en regenereer `docs/index.md` via `docs_tool.py index` en `docs_tool.py check`.
- **Out (explicitly not doing):**
  - Geen `git commit`, `git tag` of `git push` uitvoeren (alles blijft lokaal op schijf staan zodat de gebruiker eerst lokaal kan testen).
  - Geen wijzigingen aan de functionele runtime-logica van `mcp/web-search/server.py` of `mcp/context-compressor/server.py`.

## Approach
Alle code- en documentatie-aanpassingen in Stap 1 en Stap 2 worden conform Shared Execution Rule 6 gedelegeerd aan een schone code-subagent met een lossless `compress_context` Context Pack:
1. **Stap 1 — Uitbreiding `scripts/benchmark_1request.py` & atomaire regeneratie van `docs/benchmarks/benchmark-1request.md`:**
   - Voeg een helper `_active_token_estimator_label() -> str` toe aan `scripts/benchmark_1request.py` en breid `generate_benchmark_data()` uit met de `feature/20` traceerbaarheidskop, de Executive Summary van de 3 `feature/20`-pijlers, en de Methodologie & Reproductie-sectie boven de 3 live `#schema:` tabellen.
   - Voeg `REPORT_LIMIT_BYTES = 6_500` toe aan `run_benchmark(check_only=True)` en controleer dat het opgeslagen rapport `<= 6.500 B` is, byte-identiek is aan `markdown_doc`, en zowel de `feature/20` link als de Conventional Commit-string bevat.
   - Draai `python scripts/benchmark_1request.py --save` en `python scripts/benchmark_1request.py --check`.
2. **Stap 2 — Synchronisatie van `README.md`, `mcp/context-compressor/README.md` en `mcp/web-search/README.md`:**
   - Werk `README.md`, `mcp/context-compressor/README.md` en `mcp/web-search/README.md` bij zodat zij allemaal de actuele `feature/18–20` features en 3-profielen resultaten tonen en linken naar `docs/benchmarks/benchmark-1request.md` en `docs/feature/20-reproduceerbare-3-profielen-benchmark-en-regressiefix.md`.
3. **Stap 3 — Synchronisatie van `./docs` en regressie- & acceptatietests:**
   - Controleer alle acceptatiecriteria van `feature/21` én de regressiechecks van `feature/10`, `feature/18`, `feature/19` en `feature/20`, leg het bewijs vast onder `## Verification`, zet `feature/21` op `done`, en draai `docs_tool.py index` en `docs_tool.py check`.

## Acceptance criteria
- [x] `scripts/benchmark_1request.py --save` genereert `docs/benchmarks/benchmark-1request.md` (`<= 6.500` bytes) met een klikbare link naar `../feature/20-reproduceerbare-3-profielen-benchmark-en-regressiefix.md`, de Conventional Commit-referentie `feat(benchmark): live 3-profile benchmark report, section deduplication and <=3.1KB schema (feature/20)`, de `feature/20` architectuur- en methodologie-sectie (inclusief actieve token-estimator en ISO/IEC 25010:2023 + ISO/IEC 25023:2016 + RFC 9111), en alle 3 live `#schema:` tabellen, en `python scripts/benchmark_1request.py --check` slaagt met `BENCHMARK OK`.
  Check: `python -c "import pathlib, subprocess; p=pathlib.Path('docs/benchmarks/benchmark-1request.md'); txt=p.read_text(encoding='utf-8') if p.is_file() else ''; r=subprocess.run(['python','scripts/benchmark_1request.py','--check'],capture_output=True,text=True); print(p.is_file() and p.stat().st_size<=6500 and '20-reproduceerbare-3-profielen-benchmark-en-regressiefix.md' in txt and 'feat(benchmark): live 3-profile benchmark report, section deduplication and <=3.1KB schema (feature/20)' in txt and 'BENCHMARK OK' in r.stdout, p.stat().st_size)"` -> `True`
- [x] `README.md`, `mcp/context-compressor/README.md` en `mcp/web-search/README.md` verwijzen allemaal naar `docs/benchmarks/benchmark-1request.md` en `feature/20`, en `README.md` vermeldt zowel de 3-profielen ketenreductie (`-70.5%` / `-87.2%`) als `docs/benchmarks/benchmark-1request.md` en `scripts/benchmark_1request.py` in de repository-layout.
  Check: `python -c "import pathlib; r1=pathlib.Path('README.md').read_text(encoding='utf-8'); r2=pathlib.Path('mcp/context-compressor/README.md').read_text(encoding='utf-8'); r3=pathlib.Path('mcp/web-search/README.md').read_text(encoding='utf-8'); print(all('benchmark-1request.md' in t and 'feature/20' in t for t in (r1,r2,r3)) and '-87.2%' in r1 and 'benchmark_1request.py' in r1)"` -> `True`
- [x] Alle unit-tests van `mcp/context-compressor` (`21 passed`) en `mcp/web-search` (`35 passed`) en `docs_tool.py check` (`docs OK`) slagen zonder dat er een `git commit` of `git push` is uitgevoerd (`git log -1 --format=%H` blijft `935401f...`).
  Check: `python -c "import subprocess; c1=subprocess.run(['python','skills/docs-first-planner/scripts/docs_tool.py','check'],capture_output=True,text=True); c2=subprocess.run(['git','rev-parse','--short','HEAD'],capture_output=True,text=True); print(c1.stdout.strip()=='docs OK' and c2.stdout.strip()=='935401f')"` -> `True`

## Risks and open points
- **Strikte pariteit tussen `--save` en `--check`:** Omdat `python scripts/benchmark_1request.py --check` controleert dat `docs/benchmarks/benchmark-1request.md` exact overeenkomt met `generate_benchmark_data()`, moet elke tekstwijziging aan het rapport via `scripts/benchmark_1request.py --save` lopen.
- **Lokale git-status:** Op verzoek van de gebruiker (Keuze 4B) blijven alle wijzigingen lokaal ongecommit in de werkboom tot na de eigen lokale test.

## Relations
- Extends & documents: `feature/20` (and `feature/10`, `feature/18`, `feature/19`).

## Verification
| Criterion | How checked | Result |
| --- | --- | --- |
| AC1: `docs/benchmarks/benchmark-1request.md <= 6.500 B` met `feature/20` context & `--check` | `python scripts/benchmark_1request.py --save` & `--check` | `True 5230` (`BENCHMARK OK`, `-70.5%` v1 = `292,313` tok, `-87.2%` v2 = `126,831` tok) |
| AC2: Synchronisatie `README.md`, `mcp/context-compressor/README.md` & `mcp/web-search/README.md` | Python check op `benchmark-1request.md`, `feature/20`, `-87.2%` en `benchmark_1request.py` | `True` |
| AC3: Unit-tests (`21 passed` + `35 passed`), `docs_tool.py check` & geen `git commit` (`HEAD == 935401f`) | `pytest` in beide MCP-servers + `docs_tool.py check` + `git rev-parse --short HEAD` | `True` (`21 passed`, `35 passed`, `docs OK`, `935401f`) |
