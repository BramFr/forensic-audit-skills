---
id: bugs/06
title: Standing Constraints in index.md, Slim-Plan-Read Commitment-Behoud (Decisions + Out), Pre-Grill Invariant Gate, Stille Fase 2.5 & Opschoning presentatie_ai Docs
category: bugs
status: done
summary: Voorkomt herhaling van afgewezen patronen (zoals muis-3D-tilt) via Standing constraints, Decisions/Out-behoud in slim-plan-read, Pre-Grill Gate en stille Fase 2.5.
tags: [planner, context-compressor, standing-constraints, slim-plan-read, pre-grill-gate, silent-phase-2-5, docs-consistency, bugfix]
created: 2026-11-04
updated: 2026-11-04
related: [feature/02, feature/11, feature/19, feature/20]
---

# Standing Constraints in index.md, Slim-Plan-Read Commitment-Behoud (Decisions + Out), Pre-Grill Invariant Gate, Stille Fase 2.5 & Opschoning presentatie_ai Docs

## Symptom, expected behaviour, how to reproduce
- **Symptom**: Wanneer een gebruiker in eerdere bugs of features (zoals `presentatie_ai/docs/bug/01` en `bug/04`) al expliciet heeft aangegeven dat de muis en gekantelde 3D-tekstvlakken (`mousemove` 3D-tilt, `wheel`-scroll en `-16deg` rotatie) **niet** mogen, stelt de planner dit bij een volgend plan (`bug/03`) opnieuw voor onder `(Recommended)` en blijven er in `bug/03`, `bug/01` en `engine/MODULE.md` tegenstrijdige zinnen achter. Daarnaast print de planner in Fase 2.5 elke keer een D1–D7 dimensie-overzicht in de chat, wat onnodige tokens kost.
- **Expected behaviour**:
  1. **Centrale `## Standing constraints` in `docs/index.md` (`docs_tool.py`)**: Harde projectbrede verboden en afspraken staan op de *primacy*-positie bovenaan in `docs/index.md` en worden automatisch gevalideerd door `docs_tool.py check`.
  2. **Lossless Commitment-Behoud in `mcp/context-compressor` Slim Plan-Read**: Een standaard slimme plan-read (`section=None`) laat de zware secties (`Starting point`, `Scope (In)`, `Approach`, `Acceptance criteria`, `Verification`) weg, maar **behoudt altijd** een gecomprimeerde `## Decisions` tabel (de eerste 2 kolommen `Question | Decision` zonder de lange `Reason/Pros/Cons` kolom) én het `- **Out...**:` blok uit `## Scope` (binnen de `<= 4.500 B` en `>= 80%` reductie-eisen van `benchmark_1request.py`).
  3. **Harde *Pre-Grill Invariant Gate*, Synchrone Proza-Update & Stille Fase 2.5**:
     - *Pre-Grill Gate*: De planner filtert elke kandidaat-optie in Fase 2.5/3 tegen `## Standing constraints`, `MODULE.md` (`Does NOT do`) en eerdere `## Decisions` / `Out:`. Verboden patronen mogen nooit als grill-optie of `(Recommended)` worden aangeboden.
     - *Stille Fase 2.5*: Het D1–D7 dimensie-overzicht en de 8-delige systeemanalyse blijven in COMPACT modus 100% intern om de grill-vragen te sturen en worden **niet** in de chat uitgeprint (tenzij de gebruiker om het `"full report"` vraagt).
     - *Synchrone Proza-Correctie (Fase 5)*: Wanneer een nieuw plan een eerdere keuze uit een `done` plan aanscherpt of herziet, werkt Fase 5 naast de `Check:` ook de tegenstrijdige proza in `summary`, `Expected behaviour`, `Decisions` en `Scope` van dat oude plan bij en voegt het nieuwe verbod toe aan `## Standing constraints` in `docs/index.md`.
  4. **Volledige opschoning van `D:\Github Projects\presentatie_ai/docs/`**: Toevoegen van `## Standing constraints` (`INV-01` t/m `INV-06`) aan `presentatie_ai/docs/index.md`, verwijderen van alle 11 achtergebleven positieve verwijzingen naar muis-tilt, auto-orbit, muiswiel-tik en `rotateX(12deg) rotateY(-16deg)` uit `bug/01`, `bug/03`, `bug/05`, `index.md` en `engine/MODULE.md`, en borgen met een automatische `Check:`.
- **How to reproduce**:
  1. Roep `compress_context(file_path="D:/Github Projects/presentatie_ai/docs/bug/04-keyboard-only-slide-flow-no-mouse-tilt.md", workspace_root="D:/Github Projects/presentatie_ai")` aan zonder `section`: `## Decisions` en `## Scope (Out)` ontbreken volledig in de output.
  2. Scan `D:\Github Projects\presentatie_ai\docs\bug\03-herstel-echte-3d-dioramas-en-preserve3d-keten.md` en `engine/MODULE.md`: deze bevatten nog 11 zinnen die beweren dat het 3D-diorama op muisbeweging reageert (`muis-tilt`), automatisch roteert (`auto-orbit`) en op `rotateX(12deg) rotateY(-16deg)` staat.
- **Root cause (VERIFIED — `⚙️ EXECUTED` + `🔎 SOURCED`)**:
  1. `_strip_heavy_plan_sections()` in `mcp/context-compressor/server.py:42-49` stripte heel `## Decisions` en heel `## Scope`, waardoor negatieve beslissingen (`Decisions` en `Out:`) onzichtbaar werden tijdens Fase 1 oriëntatie (`🔎 SOURCED` — *Context Codec*, `arXiv:2605.17304v1`).
  2. `docs/index.md` miste een centrale `## Standing constraints` sectie op de *primacy*-positie (`🔎 SOURCED` — NASA SWE-052 & Liu et al. `arXiv:2307.03172`).
  3. `skills/docs-first-planner/SKILL.md` miste een *Pre-Grill Invariant Gate* in Fase 2.5/3 en instrueerde de agent nog om in Fase 2.5 het D1–D7 overzicht in de chat te printen (`🔎 SOURCED` — INCOSE ISO/IEC 15288 Trade Study screening & `CogErgLLM` `arXiv:2407.02885v1`).
  4. Bij het bijwerken van `bug/03` door `bug/04` en `bug/05` in `presentatie_ai` werd alleen `AC3` bijgewerkt en bleef de oude proza in `bug/03`, `bug/01` en `engine/MODULE.md` staan (`🔎 SOURCED` — IEEE Std 830 Clause 4.3.2 *Internal Consistency*).

## Observed error
- **Failure signal (verbatim)**: *"Als je 'D:\Github Projects\presentatie_ai\docs\bug\03-herstel-echte-3d-dioramas-en-preserve3d-keten.md' en 'D:\Github Projects\presentatie_ai\docs\bug\05-5m-room-ergonomics-full-stage-layout.md' geef ik eigenlijk 2x aan dat de muis 3d weergave niet mag en toch doet hij dat. Hoe kunnen we dit zodanig inregelen dat dit niet meer voor komt? Want dit kost alleen maar extra tokens ... Fase 2.5 — Compact Dimensie-Overzicht (D1–D7) hoef je ook niet te promptem bij een compact output"*
- **Discover**: Domein: Requirements Traceability, Context Compression Commitment Preservation & LLM Choice Architecture. Geopende primaire bronnen (`🔎 SOURCED`): ISO/IEC/IEEE 29148:2018 (`https://sebokwiki.org/wiki/ISO/IEC/IEEE_29148`), IEEE Std 830-1998 (`http://www.math.uaa.alaska.edu/~afkjm/cs401/IEEE830.pdf`), NASA SWE-052 Bidirectional Traceability (`https://swehb.nasa.gov/spaces/SWEHBVD/pages/102695427/SWE-052+-+Bidirectional+Traceability`), INCOSE Tradeoff Study Framework (`https://www.academia.edu/7817478/INCOSE_Tradeoff_Study_Framework`), *Compress the Context, Keep the Commitments* (`https://arxiv.org/html/2605.17304v1`), *Lost in the Middle* (`https://arxiv.org/abs/2307.03172`), *The Instruction Gap* (`https://arxiv.org/html/2601.03269`), en *CogErgLLM* (`https://arxiv.org/html/2407.02885v1`).
- **Quote**: *"geef ik eigenlijk 2x aan dat de muis 3d weergave niet mag en toch doet hij dat. Hoe kunnen we dit zodanig inregelen dat dit niet meer voor komt? Want dit kost alleen maar extra tokens"*
- **Signal**: De fout ontstaat in de overdracht tussen (a) `_strip_heavy_plan_sections()` in `mcp/context-compressor/server.py`, (b) het ontbreken van `## Standing constraints` in `docs/index.md` en `docs_tool.py`, (c) de Fase 2.5/3 grill-instructies in `skills/docs-first-planner/SKILL.md`, en (d) achtergebleven tegenstrijdige zinnen in `presentatie_ai/docs/bug/03`, `bug/01` en `engine/MODULE.md`.
- **Guard**: Alle bestaande guards — `SKILL.md <= 26.500 B`, `first-principles-architect/SKILL.md <= 21.000 B`, `0` vakspecifieke termen in de domeinneutrale architect-bestanden, en `benchmark_1request.py --check` (`<= 4.500 B` en `>= 80%` reductie op Slim Plan-Read) — zijn bewuste guards en blijven **100% intact**.
- **Hypotheses**:
  1. *H1 (`context-compressor` stript `Decisions` en `Scope (Out)` in slim-mode)* -> **BEWEZEN (`⚙️` + `🔎`)**.
  2. *H2 (Geen centrale `## Standing constraints` + geen Pre-Grill Invariant Gate in `SKILL.md`)* -> **BEWEZEN (`⚙️` + `🔎`)**.
  3. *H3 (Tegenstrijdige proza in `presentatie_ai/docs/bug/03`, `bug/01` en `engine/MODULE.md`)* -> **BEWEZEN (`⚙️` + `🔎`)**.
- **Fix**: (1) Voeg `## Standing constraints` toe aan `docs/index.md` en `docs_tool.py`, (2) behoud in `mcp/context-compressor` Slim Plan-Read de 2-koloms `## Decisions` (`Question | Decision`) én `- **Out**:` uit `## Scope`, (3) voeg de Pre-Grill Invariant Gate, Synchrone Proza-Update en Stille Fase 2.5 toe aan `docs-first-planner` en `first-principles-architect`, en (4) schoon `presentatie_ai/docs/` volledig op.
- **Confirm**: Verifieer met `pytest`, `benchmark_1request.py --check`, `docs_tool.py check` op beide repo's en de nieuwe anti-contradictie `Check:` op `presentatie_ai`.

## Starting point (audit findings)
- **Verified (`🔎 SOURCED` + `⚙️ EXECUTED`)**:
  - `mcp/context-compressor/server.py:42-49` laat `Decisions` en `Scope` volledig weg bij `section=None`. Door in slim-mode van `## Decisions` alleen kolom 1 en 2 (`Question | Decision`) te bewaren en van `## Scope` alleen het `Out`-gedeelte, groeit de slim-read van `docs/feature/18` met slechts ~380 B (van `3.302 B` naar `~3.680 B`, ruim onder de `4.500 B` limiet en met `> 85%` reductie t.o.v. `27.310 B`).
  - `skills/docs-first-planner/SKILL.md` is nu `26.382 B` (limiet `26.500 B`) en `skills/first-principles-architect/SKILL.md` is `20.918 B` (limiet `21.000 B`).
  - **Control Point 1 (2 pros & 2 cons van onderwerp naar oplossing per deelonderwerp)**:
    - *ST1 (`## Standing constraints` in `index.md` & `docs_tool.py`)*: **+Pro 1**: Primacy-positie bovenaan `index.md` maakt harde verboden direct zichtbaar in Fase 1. **+Pro 2**: `docs_tool.py check` valideert dat bron-verwijzingen in de tabel kloppen. **-Con 1**: Maximaal 15 actieve kerngrenzen om *instruction dilution* te voorkomen. **-Con 2**: Voegt ~10 regels toe aan `index.md`.
    - *ST2 (`Decisions` + `Scope Out` in Slim Plan-Read)*: **+Pro 1**: 100% behoud van eerdere beslissingen en uitsluitingen bij standaard lezen. **+Pro 2**: Blijft `> 85%` kleiner dan `--all` door de lange `Reason/Pros/Cons` kolom en `Scope (In)` in slim-mode weg te laten. **-Con 1**: ~150–380 B extra per slim-plan-read. **-Con 2**: Vereist een compacte tabel/sectie-projector in `_strip_heavy_plan_sections`.
    - *ST3 (Pre-Grill Invariant Gate, Synchrone Proza-Update & Stille Fase 2.5)*: **+Pro 1**: De AI stelt nooit meer een verboden patroon voor als grill-optie of `(Recommended)` en print geen overbodige D1–D7 tabellen meer vóór de grill. **+Pro 2**: Voorkomt dat oude zinnen in `done` plannen blijven staan na een herziening. **-Con 1**: Bij een bewuste koerswijziging door de gebruiker vraagt de AI expliciet om superseding. **-Con 2**: Moet passen binnen de 26.5 KB / 21 KB skill-budgetten.
    - *ST4 (Opschoning `presentatie_ai/docs/`)*: **+Pro 1**: Elimineert alle 11 tegenstrijdige verwijzingen naar muis-tilt, auto-orbit en `-16deg` in `bug/01`, `bug/03`, `bug/05`, `index.md` en `engine/MODULE.md`. **+Pro 2**: Borgt de 6 staande invarianten direct in `presentatie_ai/docs/index.md`. **-Con 1**: Raakt documentatie in twee workspaces. **-Con 2**: Geen.
- **Corrected**:
  - In `presentatie_ai/docs/bug/03`, `bug/01` en `engine/MODULE.md` stonden nog oude formuleringen over muis-tilt, auto-orbit, muiswiel-stepper en `rotateX(12deg) rotateY(-16deg)` die in strijd waren met `bug/04` en `bug/05`.
- **Unverified**:
  - Geen (`0` open bronnen of aannames).

## Decisions (from the grill — Control Point 2: include 2 pros and 2 cons from subject to solution)
| Question | Decision | Reason (incl. 2 pros & 2 cons from subject to solution) |
| --- | --- | --- |
| 1. Centrale vastlegging van harde verboden in `docs/index.md` | **Optie 1A — Vaste sectie `## Standing constraints` bovenaan in `docs/index.md` + validatie in `docs_tool.py check`** | **+Pro 1**: Staat op de *primacy*-positie bovenaan `index.md` zodat de AI bij elke run direct alle actieve verboden ziet. **+Pro 2**: `docs_tool.py check` bewaakt dat elke genoemde bron-ID in `## Standing constraints` bestaat. **-Con 1**: Maximaal 15 kerngrenzen om *instruction dilution* te voorkomen. **-Con 2**: Voegt een compacte tabel toe aan `index.md`. |
| 2. Slim Plan-Read in `mcp/context-compressor` | **Optie 2A — Behoud gecomprimeerde `## Decisions` (`Question \| Decision`, zonder lange `Reason`-kolom) én `- **Out**:` uit `## Scope` in Slim Plan-Read** | **+Pro 1**: Eerdere beslissingen en uitsluitingen (`Out:`) gaan nooit meer verloren tijdens Fase 1 oriëntatie. **+Pro 2**: Blijft ruim onder de `4.500 B` benchmark-limiet (`> 85%` reductie). **-Con 1**: ~150–380 B extra per slim-plan-read. **-Con 2**: De volledige `Reason` en `Scope (In)` worden geladen via `section="Decisions,Scope"` of `--all`. |
| 3. Pre-Grill Gate, Proza-Sync & Fase 2.5 Output | **Optie 3A + Stille Fase 2.5 — Pre-Grill Invariant Gate in Fase 2.5/3, Synchrone Proza-Correctie in Fase 5 én géén D1–D7 overzicht meer printen bij compacte output** | **+Pro 1**: Verboden opties worden nooit meer als keuze of `(Recommended)` voorgesteld en elke run bespaart ~500–900 chat-tokens doordat Fase 2.5 intern blijft. **+Pro 2**: Oude plannen houden geen tegenstrijdige zinnen meer over na een latere bugfix. **-Con 1**: Vereist expliciete supersede-bevestiging als de gebruiker zelf een eerdere constraint wil omdraaien. **-Con 2**: Moet strak binnen de byte-limieten van `SKILL.md` blijven. |
| 4. Opschoning `presentatie_ai/docs/` | **Optie 4A — Direct `presentatie_ai/docs/` (`index.md`, `bug/01`, `bug/03`, `bug/05`, `engine/MODULE.md`) opschonen en voorzien van `## Standing constraints`** | **+Pro 1**: `presentatie_ai` is direct 100% vrij van de tegenstrijdigheden tussen `bug/03`, `bug/04` en `bug/05`. **+Pro 2**: Nieuwe `Check:` faalt direct als `muis-tilt`, `auto-orbit` of `rotateY(-16deg)` ooit terugkeert als eis. **-Con 1**: Wijzigt docs in twee repo's. **-Con 2**: Geen. |

## Scope
- **In**:
  1. **`skills/docs-first-planner/scripts/docs_tool.py` & `docs/index.md` (ST1)**:
     - Voeg `## Standing constraints` toe aan `SKELETON` in `docs_tool.py` en aan `docs/index.md` van `forensic-audit-skills`.
     - Laat `collect_problems(docs)` in `docs_tool.py` controleren dat als `## Standing constraints` aanwezig is in `docs/index.md`, elke gerefereerde plan-ID (zoals `bugs/01`, `feature/19`, `bug/04`) daadwerkelijk bestaat in `all_ids`.
  2. **`mcp/context-compressor/server.py`, `MODULE.md` & `tests/test_server.py` (ST2)**:
     - Pas `_strip_heavy_plan_sections()` in `mcp/context-compressor/server.py` aan zodat bij `section=None` op een planbestand:
       - `## Decisions` behouden blijft in compacte vorm: bij een Markdown-tabel worden alleen de eerste 2 kolommen (`Question | Decision`) behouden; bij bullet-lijsten blijft elke top-level bullet op 1 compacte regel behouden;
       - uit `## Scope` alleen het `- **Out...` / `- Out...` blok (met zijn sub-bullets) behouden blijft, terwijl `- **In...` / `- In...` weggelaten wordt en `'Scope (In)'` in de `<!-- Omitted plan sections ... -->` notice wordt vermeld.
     - Werk `mcp/context-compressor/MODULE.md` en `mcp/context-compressor/tests/test_server.py` bij met unit-tests en opposite-tests.
  3. **`skills/docs-first-planner/SKILL.md`, `references/first-principles.md`, `references/persist-and-regression.md`, `references/plan-template.md`, `skills/first-principles-architect/SKILL.md`, `CLAUDE.md`, `GEMINI.md` & `.cursor/rules/forensic-audit.mdc` (ST3)**:
     - Voeg `Standing constraints` toe aan de Fase 1 `compress_context(file_path="docs/index.md", section="Product vision,Standing constraints,Search keywords,Items,Modules", ...)` aanroep.
     - Voeg de **Pre-Grill Invariant Gate** toe aan Fase 2.5 en Fase 3: geen enkele grill-optie of `(Recommended)` default mag in strijd zijn met `## Standing constraints`, `MODULE.md` (`Does NOT do`) of eerdere `## Decisions` / `Out:`.
     - Maak **Fase 2.5 stil in COMPACT modus**: houd het D1–D7 dimensie-overzicht en de 8-delige systeemanalyse 100% intern (print ze niet uit in de chat vóór de grill, tenzij de gebruiker om het `"full report"` vraagt).
     - Voeg in `references/persist-and-regression.md` (Fase 5 stap 2) de **Synchrone Proza- & Standing-Constraints-Update** toe: bij het vastleggen van een harde afwijzing of het herzien van een eerder `done` plan moet Fase 5 zowel `## Standing constraints` in `index.md` aanvullen als tegenstrijdige zinnen in het gerelateerde plan (`summary`, `Expected behaviour`, `Decisions`, `Scope`) bijwerken.
  4. **Opschoning `D:\Github Projects\presentatie_ai` & Synchronisatie van alle Mirrors (ST4)**:
     - Voeg `## Standing constraints` (`INV-01` t/m `INV-06`) toe aan `D:\Github Projects\presentatie_ai\docs\index.md`.
     - Schoon alle achtergebleven positieve verwijzingen naar muis-tilt, auto-orbit, muiswiel-stepper en `rotateX(12deg) rotateY(-16deg)` op in `presentatie_ai/docs/bug/01`, `bug/03`, `bug/05`, `presentatie_ai/docs/index.md` en `presentatie_ai/engine/MODULE.md`.
     - Synchroniseer alle gewijzigde bestanden in `skills/` en `mcp/context-compressor/server.py` byte-identiek naar `C:\Users\BramFransen\.gemini\config\skills` en `C:\Users\BramFransen\.gemini\antigravity-cli\mcp\`.
- **Out (explicitly not doing)**:
  - Geen wijzigingen aan de presentatie-code in `D:\Github Projects\presentatie_ai\index.html` of `slides/*.md`.
  - Geen verhoging van de `SKILL.md` (`<= 26.500 B`), `first-principles-architect/SKILL.md` (`<= 21.000 B`) of `Slim Plan-Read` (`<= 4.500 B`) byte-limieten.
  - Geen vakspecifieke termen in `skills/first-principles-architect/SKILL.md` of `skills/docs-first-planner/references/first-principles.md`.

## Approach
1. **Stap 1 (`mcp/context-compressor` & `docs_tool.py`)**: Delegeer aan een schone uitvoerings-subagent het bijwerken van `_strip_heavy_plan_sections()` in `mcp/context-compressor/server.py`, `mcp/context-compressor/MODULE.md`, `mcp/context-compressor/tests/test_server.py` en `skills/docs-first-planner/scripts/docs_tool.py`.
2. **Stap 2 (`skills/docs-first-planner`, `skills/first-principles-architect`, `docs/index.md` & Mirrors)**: Delegeer aan een schone uitvoerings-subagent het domeinneutraal bijwerken van de skill-bestanden, `docs/index.md`, `CLAUDE.md`, `GEMINI.md`, `.cursor/rules/forensic-audit.mdc`, `scripts/benchmark_1request.py` en het synchroniseren naar `C:\Users\BramFransen\.gemini\config\skills`.
3. **Stap 3 (Opschoning `presentatie_ai/docs/` & `engine/MODULE.md`)**: Delegeer aan een schone uitvoerings-subagent het toevoegen van `## Standing constraints` aan `presentatie_ai/docs/index.md`, het opschonen van de tegenstrijdige zinnen in `bug/01`, `bug/03`, `bug/05` en `engine/MODULE.md`, en het draaien van `docs_tool.py index` en `check` op `presentatie_ai/docs`.
4. **Stap 4 (Regressie- & Eindverificatie)**: Draai alle unit-tests, `benchmark_1request.py --check`, `docs_tool.py check` op beide repo's en de acceptatiecriteria van `bugs/06`.

## Acceptance criteria
- [x] **AC1 — `mcp/context-compressor` Slim Plan-Read (`section=None`) behoudt gecomprimeerde `## Decisions` (`Question | Decision`) én `- **Out**:` uit `## Scope` terwijl `Starting point`, `Scope (In)`, `Approach`, `Acceptance criteria` en `Verification` weggelaten blijven (`<= 4.500 B` en `>= 80%` reductie op `docs/feature/18`)**
  Check: `uv run --python 3.12 --directory mcp/context-compressor pytest tests/test_server.py -q` -> `passed`
- [x] **AC2 — `docs/index.md` (in beide repo's) en `docs_tool.py` bevatten en valideren `## Standing constraints`, en `docs_tool.py check` geeft `docs OK` op zowel `forensic-audit-skills` als `presentatie_ai`**
  Check: `python -c "import subprocess, sys; r1=subprocess.run([sys.executable,'skills/docs-first-planner/scripts/docs_tool.py','check'],capture_output=True,text=True); r2=subprocess.run([sys.executable,'skills/docs-first-planner/scripts/docs_tool.py','--docs',r'D:\Github Projects\presentatie_ai\docs','check'],capture_output=True,text=True); print(r1.stdout.strip()=='docs OK' and r2.stdout.strip()=='docs OK' and '## Standing constraints' in open('docs/index.md',encoding='utf-8').read() and '## Standing constraints' in open(r'D:\Github Projects\presentatie_ai\docs\index.md',encoding='utf-8').read())"` -> `True`
- [x] **AC3 — `skills/docs-first-planner/SKILL.md` (`<= 26.500 B`), `references/first-principles.md`, `skills/first-principles-architect/SKILL.md` (`<= 21.000 B`) en `## Standing constraints` in `docs/index.md` bevatten de Pre-Grill Invariant Gate en Stille Fase 2.5 (geen D1–D7 chat-dump in compact mode), met `0` vakspecifieke of code-gebiaste termen (`code`, `code-edit`, `code-subagent`, etc.) in de domeinneutrale secties**
  Check: `python -c "import pathlib,re; p_dfp=pathlib.Path('skills/docs-first-planner/SKILL.md'); p_fpa=pathlib.Path('skills/first-principles-architect/SKILL.md'); p_fp=pathlib.Path('skills/docs-first-planner/references/first-principles.md'); t_dfp=p_dfp.read_text(encoding='utf-8'); t_fp=p_fp.read_text(encoding='utf-8'); sc=re.search(r'## Standing constraints(.*?)## Search keywords',pathlib.Path('docs/index.md').read_text(encoding='utf-8'),re.S).group(1); pat=re.compile(r'\\b(code(?:-edit|-subagent|-wijziging)?|vehicle|car|tuning|dough|oven|bake|baking|kitchen|recipe|meal|dog|puppy|horse|pet|house|building|renovat\\w*|database|sql|postgres|sqlite|server|software|coding|compile\\w*|compiler|binary|exe|thread\\w*|gpu|npu|cpu|ram|cyber\\w*|pentest\\w*|encrypt\\w*|firewall|malware|skeleton|texture|presentation|font|screen|canvas)\\b',re.I); b1=p_fpa.read_text(encoding='utf-8').split('---',2)[2]; print(p_dfp.stat().st_size<=26500 and p_fpa.stat().st_size<=21000 and 'Standing constraints' in t_dfp and 'Pre-Grill' in t_dfp and 'do not print the D1' in t_fp and len(pat.findall(b1))+len(pat.findall(t_fp))+len(pat.findall(sc))==0)"` -> `True`
- [x] **AC4 — `D:\Github Projects\presentatie_ai\docs\bug\03`, `bug/01` en `engine/MODULE.md` bevatten `0` tegenstrijdige zinnen die muis-tilt, auto-orbit of `rotateX(12deg) rotateY(-16deg)` nog als gewenst gedrag beschrijven**
  Check: `python -c "import pathlib,re; root=pathlib.Path(r'D:\Github Projects\presentatie_ai'); b3=(root/'docs/bug/03-herstel-echte-3d-dioramas-en-preserve3d-keten.md').read_text(encoding='utf-8'); mod=(root/'engine/MODULE.md').read_text(encoding='utf-8'); bad=re.findall(r'met auto-orbit|op muisbeweging reageert|\+\s*Muis-Tilt|sinusoïdale 3D-orbit|beweegt vanzelf subtiel|rotateX\(12deg\)\s*rotateY\(-16deg\)', b3+'\n'+mod, re.I); print('0 contradictions' if not bad else f'FAIL: {bad}')"` -> `0 contradictions`
- [x] **AC5 — `scripts/benchmark_1request.py --check` slaagt (`BENCHMARK OK`) en alle mirrors in `C:\Users\BramFransen\.gemini\config\skills` zijn byte-identiek**
  Check: `python -c "import pathlib,subprocess,sys; loc=pathlib.Path(r'C:\Users\BramFransen\.gemini\config\skills'); rep=pathlib.Path(r'D:\Github Projects\forensic-audit-skills\skills'); diff=sum((loc/p.relative_to(rep)).read_bytes()!=p.read_bytes() for p in rep.rglob('*') if p.is_file() and '__pycache__' not in p.parts); r=subprocess.run([sys.executable,'scripts/benchmark_1request.py','--check'],capture_output=True,text=True); print(diff==0 and 'BENCHMARK OK' in r.stdout)"` -> `True`

## Verification
| Criterion | How checked | Result |
| --- | --- | --- |
| AC1 | `uv run --python 3.12 --directory mcp/context-compressor pytest tests/test_server.py -q` | `22 passed` (inclusief `test_bugs06_slim_plan_keeps_2col_decisions_and_scope_out`; `docs/feature/18` slim plan-read = `4.225 B <= 4.500 B`, `-84.6%` reductie) |
| AC2 | `docs_tool.py check` op `forensic-audit-skills` en `presentatie_ai/docs` + aanwezigheid en ID-validatie van `## Standing constraints` | `True` (`docs OK` op beide repo's) |
| AC3 | Byte-limieten (`docs-first-planner/SKILL.md` = `26.485 B <= 26.500 B`, `first-principles-architect/SKILL.md` = `20.981 B <= 21.000 B`), Pre-Grill Gate, Stille Fase 2.5 en `0` hits op de uitgebreide domeinneutrale regex (incl. `code`, `code-edit`, `code-subagent`) over `first-principles-architect/SKILL.md`, `references/first-principles.md` en `## Standing constraints` in `docs/index.md` | `True` (`0` regex hits) |
| AC4 | Anti-contradictie scan op `presentatie_ai/docs/bug/03`, `bug/01` en `engine/MODULE.md` | `0 contradictions` |
| AC5 | Mirror-pariteit (`diff == 0`) en `python scripts/benchmark_1request.py --check` | `True` (`BENCHMARK OK`, `-87.0%` cumulatieve token-reductie in Finetuned v2) |

## Risks and open points
- Byte-budget van `skills/docs-first-planner/SKILL.md` (`26.382 B` / `26.500 B`): bij het toevoegen van de Pre-Grill Invariant Gate en Stille Fase 2.5 wordt de weggevallen D1–D7 chat-instructie ingekort zodat het bestand ruim onder `26.500 B` blijft.

## Relations
- Depends on / extends: `feature/02`, `feature/11`, `feature/19`, `feature/20`.
