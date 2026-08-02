# Spec: Project Pilot

## Objective

Create a neutral, beginner-friendly Codex plugin inspired by Sol Advisor. A person
should be able to ask Project Pilot to build, fix, plan, or review work without knowing
model names, agent configuration, shell scripting, or orchestration terminology.

The default experience should be safe and useful in one session. When native
multi-agent tools are available, the skill may use them for focused implementation or
fresh review. When they are unavailable, it must continue honestly in the primary
session instead of blocking routine work.

### Assumptions

1. The target is the current Codex plugin format, not a Claude Code plugin.
2. "Custom" means new neutral branding and a simplified workflow, not a line-for-line fork.
3. Exact Sol, Terra, and Luna model access cannot be assumed for people receiving the plugin.
4. The repository will be shareable as a Codex marketplace after the user publishes it.
5. Publishing to a remote Git host is outside scope until the user chooses an account and repository.
6. The MIT-licensed Sol Advisor source may be adapted as long as its notice is preserved.

## Tech Stack

- Codex marketplace JSON and plugin manifest JSON
- Markdown-based Codex skill
- POSIX shell for local setup and verification helpers
- Python 3 standard-library tests
- No runtime packages, API keys, services, or build step

## Commands

- Test: `python3 -m unittest discover -s tests -v`
- Verify package: `sh plugins/project-pilot/scripts/verify.sh`
- Check setup helper: `sh scripts/setup.sh --dry-run`
- Official skill validation: `uv run --no-project --with pyyaml python "$HOME/.codex/skills/.system/skill-creator/scripts/quick_validate.py" plugins/project-pilot/skills/project-pilot`
- Official plugin validation: `uv run --no-project --with pyyaml python "$HOME/.codex/skills/.system/plugin-creator/scripts/validate_plugin.py" plugins/project-pilot`

## Project Structure

- `.agents/plugins/marketplace.json` — shareable Codex marketplace catalog
- `plugins/project-pilot/` — installable plugin package
- `plugins/project-pilot/skills/project-pilot/` — concise runtime workflow and references
- `plugins/project-pilot/scripts/verify.sh` — dependency-free package check
- `scripts/setup.sh` — one-command local install/update helper
- `tests/` — packaging and behavior-contract tests
- `docs/` — contributor-facing rationale and comparison
- `tasks/` — implementation plan and progress checklist

## Content Style

Prefer direct, observable language:

```text
Outcome: Add a working search box to the customer list.
Done when: A user can search by name, clear the search, and existing tests pass.
Safety: Do not change login, billing, or stored customer data.
Checks: Run the focused tests and inspect the final diff.
```

Avoid unexplained labels such as "lane pin," "rollout metadata," or "commitment boundary."

## Testing Strategy

- Use standard-library unit tests to validate manifest fields, file layout, documentation,
  mode names, safety gates, fallbacks, and attribution.
- Use the repository verifier for JSON, shell syntax, and cross-file consistency.
- Run the official Codex skill and plugin validators before handoff.
- Forward-test realistic invocations in a fresh agent context after the package validates.

## Boundaries

- Always: keep installation reversible, report actual verification, preserve attribution,
  and distinguish independent review from self-review.
- Ask first: publishing, pushing, installing into global Codex configuration, destructive
  actions, credentials, paid services, and consequential production changes.
- Never: claim a particular model ran without evidence, require private session-log access,
  silently skip a requested careful review, or overwrite unrelated user configuration.

## Success Criteria

1. One plugin install exposes one clearly named Project Pilot skill.
2. The plugin has no custom-agent, named-model, `jq`, API-key, or service dependency.
3. Quick, Guided, and Careful modes have clear routing and safety behavior.
4. A non-technical reader can install, invoke, update, share, and remove it from the README.
5. Optional delegation uses bounded ownership; absence of delegation has an honest fallback.
6. Meaningful code changes receive verification, and risky changes receive a fresh review
   when available or an explicit limitation when not.
7. Repository tests, package verification, and official validators all pass.
8. The original Sol Advisor copyright and MIT permission notice remain included.

## Open Questions

- The final GitHub owner and repository URL are intentionally unset until the user chooses them.
- The publisher display name can be personalized later without changing the workflow.
