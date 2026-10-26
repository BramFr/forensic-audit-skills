# Docs index

## Product vision
Deze skills laten een AI-agent controleren in plaats van instemmen. Ze gaan uit van nul vertrouwen en eisen bewijs in plaats van schijn. Gaat er iets fout, dan herkennen ze de echte oorzaak in de foutmelding of het symptoom en komen ze met een concrete, geteste oplossing, zonder een bewuste beveiliging te verzwakken. Ze werken in elk vakgebied: code, websites, beveiliging, planning, bakken, auto's, het trainen van een hond. De rapportage is compact en eerlijk over wat niet is geverifieerd.

## Search keywords
[zero-trust, forensic-audit, primary-source-verification, fail-closed, no-fake-green, zero-hardcode-discovery, closed-loop-repair, negative-declaration, domain-neutral-diagnosis, source-hierarchy, open-primary-counterpart, ISO-NEN-IEC, IETF-RFC, NIST-SP-800, OWASP-ASVS, W3C-WCAG-2.2, WAI-ARIA, Fitts-Law-44x44px, accessibility-tree, Playwright-E2E, HAR-recording, SQL-persistence-verification, docs-first-planner, single-source-of-truth, docs-regression-check, YAML-frontmatter, query-expansion, controlled-vocabulary, ISO-25964, SKOS, selective-keyword-scoping, priority-keywords, lost-in-the-middle, blast-radius-analysis, root-cause-analysis, security-baseline, secret-masking, CWE-CVE-advisories, LLM-excessive-agency, OWASP-LLM06, MCP-server, MCP-tool-schema, DuckDuckGo-search, PDF-to-Markdown, JSON-LD-ItemList, SSR-hydration-extraction, TLS-fingerprint-rotation, anti-bot-detection, Python-stdlib, pytest, Claude-Code-plugin, Gemini-CLI-extension, Cursor-rules, Antigravity-skills]

## Items
<!-- INDEX:START -->
| ID | Status | Title | Summary | Tags |
| --- | --- | --- | --- | --- |
| [bugs/01](bugs/01-search-keywords-afdwingen-in-tool-schema-en-skills.md) | done | Search keywords worden overgeslagen na lange context of door ontbrekende tool-schema instructie | Dwing ## Search keywords (incl. visie/schaal prio-termen) af in search_website.json, server.py docstring en SKILL.md en sync mappen. | planner, forensic-audit, search-keywords, web-search, mcp, tool-schema, sync, bugfix |
| [feature/01](feature/01-foutdiagnose-in-skills.md) | done | Foutdiagnose in alle skills | Alle skills herkennen de echte oorzaak van een fout (log, symptoom) en geven een geteste fix, in elk vakgebied. | skills, diagnose, forensic-audit, voorbeelden |
| [feature/02](feature/02-docs-regressiecheck.md) | done | Docs-controle vooraf en regressiecheck achteraf | De planner voert Check-regels van gerelateerde done-items uit, vooraf en achteraf, en markeert regressies. | planner, docs, regressie, verificatie |
| [feature/03](feature/03-domeinneutrale-diagnose-en-bronhierarchie.md) | done | Domeinneutrale diagnose met bronhierarchie en live zoeken | Diagnose in alle skills start met Discover en bronhierarchie (incl. open tegenhanger voor ISO/NEN) zonder vaste lijsten. | skills, diagnose, domeinneutraal, bronnen, normen |
| [feature/04](feature/04-zoekwoorden-in-index-en-skill-sync.md) | done | Dynamische Search keywords in index.md en synchronisatie van lokale skills | Voeg ## Search keywords (~50 termen) toe aan index.md zodat audits per zoekopdracht 1-3 projecttermen meesturen en sync skills. | planner, forensic-audit, search-keywords, index, sync, domeinneutraal |
| [feature/05](feature/05-universele-website-scraper-en-zoekfilter.md) | done | Universele 3-laags website-scraper, anti-bot sessierotatie en URL+zoekfilter in web-search | Voeg 3-laags extractie (JSON-LD, SSR hydration, DOM-cards), anti-bot sessierotatie en URL+zoekfilter toe aan server.py. | web-search, mcp, scraper, json-ld, hydration, anti-bot, filter-query, forensic-audit |
<!-- INDEX:END -->
