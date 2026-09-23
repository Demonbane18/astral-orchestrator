# Astral Orchestrator repository guide

## Purpose

This repository packages Astral Orchestrator as a shareable Codex marketplace plugin.
Keep the installed experience simple for people who do not write code.

TypeSafe session: on

## Commands

- Test: `python3 -m unittest discover -s tests -v`
- Verify package: `sh plugins/astral-orchestrator/scripts/verify.sh`
- Validate skill: `uv run --no-project --with pyyaml python "$HOME/.codex/skills/.system/skill-creator/scripts/quick_validate.py" plugins/astral-orchestrator/skills/astral-orchestrator`
- Validate release tracker: `uv run --no-project --with pyyaml python "$HOME/.codex/skills/.system/skill-creator/scripts/quick_validate.py" skills/track-astral-releases`
- Validate plugin: `uv run --no-project --with pyyaml python "$HOME/.codex/skills/.system/plugin-creator/scripts/validate_plugin.py" plugins/astral-orchestrator`

## Conventions

- Use plain language and explain unavoidable technical terms on first use.
- Keep the core `SKILL.md` concise; put detailed templates in `references/`.
- Require the observed supported primary at its current session effort and selected
  child routes at their configured effort in every mode. Primary effort never caps
  worker effort; never silently substitute a route.
- Keep Comet mode as the explicit single-session option for tiny work.
- Use built-in local tools by default. The user-authorized TypeSafe companion may
  make a bounded external judgment only when this session is on and a project key
  is configured; keep credentials out of the plugin and website.
- Preserve the original Sol Advisor MIT notice and attribution.
- Use Opera GX for browser testing. Do not use Google Chrome unless the user asks.
- Use `skills/track-astral-releases/SKILL.md` for every version bump, release,
  deployment, marketplace update, or OpenAI public-version check. Append evidence to
  `release/astral-release-ledger.json`; never infer one publication surface from another.

## Boundaries

- Always run the test and verification commands after behavior or packaging changes.
- Ask before publishing, pushing, or changing a user's global Codex configuration unless
  that target and effect were already explicitly authorized in this task. Carry that
  authorization across turns; ask again only when the target or effect changes.
- Complete authorized local preparation and verification while a consequential action
  awaits approval. Block dependent work, continue independent work, and respect explicit
  preview-only or user-review pauses.
- Never add secrets, analytics, or destructive setup steps. TypeSafe calls are
  limited to the user-authorized opt-in routing integration.
