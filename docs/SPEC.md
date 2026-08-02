# Spec: Project Pilot v2.1

## Objective

Create a beginner-friendly Codex plugin that provides real, observable multi-agent
orchestration inspired by Sol Advisor. A Sol task must lead, assign bounded work to Luna
or Terra according to the work, integrate and verify the result, then use a fresh Sol
reviewer. The user can tune each lane's effort without editing agent profiles.

The user should not need to understand TOML files, runtime logs, or agent APIs. One setup
command installs the plugin and three namespaced agent profiles. The workflow must stop
when an exact required route cannot be proven; it must never pretend a fallback was the
requested orchestration.

### Assumptions

1. The target is the current Codex plugin and custom-agent format.
2. The primary task can be started with `gpt-5.6-sol` and the configured reasoning
   effort; High is the default.
3. Recipients have access to `gpt-5.6-luna`, `gpt-5.6-terra`, and `gpt-5.6-sol`.
4. Custom agents are installed to Codex's personal `agents` directory and discovered in
   a newly started task.
5. When a host lacks native custom-agent selection, a bundled launcher may start an
   exact pinned Codex process for the same lane.
6. Publishing is outside scope until the user chooses a GitHub destination.
7. The MIT-licensed Sol Advisor source may be adapted with preserved notice.

## Route Contract

| Responsibility | Required route |
|---|---|
| Requirements, architecture, decomposition, cross-lane integration | Sol at configured effort (High default) |
| Narrow, repeatable, fully specified execution | Luna at configured effort (XHigh default) |
| Context-heavy implementation, debugging, component/external integration, refactoring | Terra at configured effort (XHigh default) |
| Fresh final review | Sol at configured reviewer effort (High default), with requested read-only sandbox |

The default efforts are Sol High, Luna XHigh, Terra XHigh, and reviewer Sol High.
Per-lane overrides are stored outside the plugin cache. A custom worker or reviewer
effort uses the exact-process launcher so a native profile cannot override it.

Quick mode is the explicit exception: tiny, reversible work stays in the Sol primary at
its configured effort. Guided and Careful work use pinned lanes whenever bounded
execution exists.

## Tech Stack

- Codex marketplace JSON and plugin manifest JSON
- Markdown Codex skill and one-level reference files
- Codex custom-agent TOML profiles
- POSIX shell for setup, exact-copy installation, and verification
- Python 3.11+ standard library for tests, exact-process launching, and allowlisted
  runtime evidence
- No additional API key, external service beyond Codex, analytics, direct network client,
  or background process

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
- Unsupported effort settings fail before a delegated Codex process starts.
- Careful review cannot claim `ship` unless required read-only isolation is observed.

## Success Criteria

1. One setup command installs one plugin and exactly three namespaced profiles.
2. Profiles pin Sol High, Luna XHigh, and Terra XHigh exactly as specified.
3. The skill routes by work characteristics and parallelizes only non-overlapping cards.
4. Runtime inspection emits only allowlisted route fields.
5. A non-technical reader can install, invoke, update, share, troubleshoot, and remove it.
6. Tests, package verification, and official validators pass.
7. The original Sol Advisor copyright and MIT permission notice remain included.
8. A non-technical user can show, change, and reset every lane's effort independently.

## Open Questions

- The final GitHub owner and repository URL remain unset until the user chooses them.
- A PowerShell installer may be added after demand from Windows recipients is confirmed.
