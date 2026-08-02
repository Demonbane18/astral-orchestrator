# Spec: Project Pilot v2

## Objective

Create a beginner-friendly Codex plugin that provides real, observable multi-agent
orchestration inspired by Sol Advisor. Sol High must lead the task, assign bounded work
to Luna XHigh or Terra XHigh according to the work, integrate and verify the result,
then use a fresh Sol High reviewer.

The user should not need to understand TOML files, runtime logs, or agent APIs. One setup
command installs the plugin and three namespaced agent profiles. The workflow must stop
when an exact required route cannot be proven; it must never pretend a fallback was the
requested orchestration.

### Assumptions

1. The target is the current Codex plugin and custom-agent format.
2. The primary task can be started with `gpt-5.6-sol` and High reasoning.
3. Recipients have access to `gpt-5.6-luna`, `gpt-5.6-terra`, and `gpt-5.6-sol`.
4. Custom agents are installed to Codex's personal `agents` directory and discovered in
   a newly started task.
5. Publishing is outside scope until the user chooses a GitHub destination.
6. The MIT-licensed Sol Advisor source may be adapted with preserved notice.

## Route Contract

| Responsibility | Required route |
|---|---|
| Requirements, architecture, decomposition, cross-lane integration | Sol High primary session |
| Narrow, repeatable, fully specified execution | Luna XHigh |
| Context-heavy implementation, debugging, component/external integration, refactoring | Terra XHigh |
| Fresh final review | Sol High reviewer with requested read-only sandbox |

Quick mode is the explicit exception: tiny, reversible work stays in the Sol High
primary session. Guided and Careful work use pinned lanes whenever bounded execution
exists.

## Tech Stack

- Codex marketplace JSON and plugin manifest JSON
- Markdown Codex skill and one-level reference files
- Codex custom-agent TOML profiles
- POSIX shell for setup, exact-copy installation, and verification
- Python 3 standard library for tests and allowlisted runtime evidence
- No API key, external service, analytics, network call, or background process

## Commands

- Test: `python3 -m unittest discover -s tests -v`
- Verify package: `sh plugins/project-pilot/scripts/verify.sh`
- Check setup: `sh scripts/setup.sh --dry-run`
- Validate skill: `uv run --no-project --with pyyaml python "$HOME/.codex/skills/.system/skill-creator/scripts/quick_validate.py" plugins/project-pilot/skills/project-pilot`
- Validate plugin: `uv run --no-project --with pyyaml python "$HOME/.codex/skills/.system/plugin-creator/scripts/validate_plugin.py" plugins/project-pilot`

## Safety and Failure Behavior

- Agent installation never overwrites a different file.
- Agent removal deletes only exact, unmodified Project Pilot profiles.
- Destructive, irreversible, credential, publishing, and production actions retain an
  explicit user confirmation gate.
- Each worker receives exact ownership and must preserve concurrent edits.
- Agent reports are inspected and independently verified in the primary session.
- Missing or mismatched role/model/effort evidence stops the route; no silent fallback.
- Careful review cannot claim `ship` unless required read-only isolation is observed.

## Success Criteria

1. One setup command installs one plugin and exactly three namespaced profiles.
2. Profiles pin Sol High, Luna XHigh, and Terra XHigh exactly as specified.
3. The skill routes by work characteristics and parallelizes only non-overlapping cards.
4. Runtime inspection emits only allowlisted route fields.
5. A non-technical reader can install, invoke, update, share, troubleshoot, and remove it.
6. Tests, package verification, and official validators pass.
7. The original Sol Advisor copyright and MIT permission notice remain included.

## Open Questions

- The final GitHub owner and repository URL remain unset until the user chooses them.
- A PowerShell installer may be added after demand from Windows recipients is confirmed.
