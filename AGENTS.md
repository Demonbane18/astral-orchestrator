# Astral Orchestrator repository guide

## Purpose

This repository packages Astral Orchestrator as a shareable Codex marketplace plugin.
Keep the installed experience simple for people who do not write code.

## Commands

- Test: `python3 -m unittest discover -s tests -v`
- Verify package: `sh plugins/astral-orchestrator/scripts/verify.sh`
- Validate skill: `uv run --no-project --with pyyaml python "$HOME/.codex/skills/.system/skill-creator/scripts/quick_validate.py" plugins/astral-orchestrator/skills/astral-orchestrator`
- Validate release tracker: `uv run --no-project --with pyyaml python "$HOME/.codex/skills/.system/skill-creator/scripts/quick_validate.py" skills/track-astral-releases`
- Validate plugin: `uv run --no-project --with pyyaml python "$HOME/.codex/skills/.system/plugin-creator/scripts/validate_plugin.py" plugins/astral-orchestrator`

## Conventions

- Use plain language and explain unavoidable technical terms on first use.
- Keep the core `SKILL.md` concise; put detailed templates in `references/`.
- Require the exact Sol, Luna, and Terra models at each lane's configured effort for
  Orbit and Event Horizon execution; never silently substitute a different route.
- Keep Comet mode as the explicit single-session option for tiny work.
- Use only built-in local tools at runtime; do not add an API key or external service.
- Preserve the original Sol Advisor MIT notice and attribution.
- Use Opera GX for browser testing. Do not use Google Chrome unless the user asks.
- Use `skills/track-astral-releases/SKILL.md` for every version bump, release,
  deployment, marketplace update, or OpenAI public-version check. Append evidence to
  `release/astral-release-ledger.json`; never infer one publication surface from another.

## Boundaries

- Always run the test and verification commands after behavior or packaging changes.
- Ask before publishing, pushing, or changing a user's global Codex configuration.
- Never add secrets, analytics, network calls, or destructive setup steps.
