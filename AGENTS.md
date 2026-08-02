# Project Pilot repository guide

## Purpose

This repository packages Project Pilot as a shareable Codex marketplace plugin.
Keep the installed experience simple for people who do not write code.

## Commands

- Test: `python3 -m unittest discover -s tests -v`
- Verify package: `sh plugins/project-pilot/scripts/verify.sh`
- Validate skill: `python3 "$HOME/.codex/skills/.system/skill-creator/scripts/quick_validate.py" plugins/project-pilot/skills/project-pilot`
- Validate plugin: `python3 "$HOME/.codex/skills/.system/plugin-creator/scripts/validate_plugin.py" plugins/project-pilot`

## Conventions

- Use plain language and explain unavoidable technical terms on first use.
- Keep the core `SKILL.md` concise; put detailed templates in `references/`.
- Do not require a named model, custom agent, external service, or extra package.
- Treat multi-agent work as an optional enhancement with a same-session fallback.
- Preserve the original Sol Advisor MIT notice and attribution.
- Use Opera GX for browser testing. Do not use Google Chrome unless the user asks.

## Boundaries

- Always run the test and verification commands after behavior or packaging changes.
- Ask before publishing, pushing, or changing a user's global Codex configuration.
- Never add secrets, analytics, network calls, or destructive setup steps.
