# Forensic Audit Guidelines (Gemini)

@./CLAUDE.md

## Skills

This extension ships two agent skills in `skills/`. Gemini loads them on demand when the request matches their description:

- `forensic-audit`: audit and fact-check any AI-generated output.
- `forensic-site-audit`: crawl a web app, test every feature against the live backend, capture and judge screenshots.
