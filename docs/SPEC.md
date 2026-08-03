# Spec: Astral Orchestrator v3.1

## Objective

Provide a beginner-friendly Codex plugin that delivers observable model-routed
orchestration. A Sol task leads, assigns bounded work to Luna or Terra based on the work,
integrates and verifies the result, then uses a fresh Sol reviewer. Each lane's reasoning
effort is configurable without editing profiles.

The user should not need to understand TOML files, runtime logs, or agent APIs. One setup
command installs the plugin and three namespaced profiles. When an exact route cannot be
proven, the workflow stops rather than claiming a generic fallback was the requested
orchestration.

Version 3.1 adds a local JSONL benchmark scorecard. It compares paired, repeated Astral
and single-Sol trials only after validating frozen task fingerprints, identical
acceptance checks, route evidence, and consistently available optional metrics. It
summarizes supplied data without calling models or claiming a result that was not
recorded.

## Identity and migration

Version 3.0.0 was the breaking identity migration from the former Project Pilot
identifiers. The current product version is 3.1.4. The normalized plugin, marketplace,
skill, and profile prefix is
astral-orchestrator; TOML agent names use astral_orchestrator. Route evidence begins
with ASTRAL_ORCHESTRATOR_ROUTE, and persistent effort settings live at
~/.codex/astral-orchestrator/effort-levels.toml.

Users install the v3 package as new. The former profile and settings names are not
modified automatically.

## Assumptions

1. The target is the current Codex plugin and custom-agent format.
2. The primary task starts with gpt-5.6-sol at the configured reasoning effort; High is
   the default.
3. Recipients have access to gpt-5.6-luna, gpt-5.6-terra, and gpt-5.6-sol.
4. Custom agents are installed to Codex's personal agents directory and are discovered
   in a newly started task.
5. When a host lacks native custom-agent selection, the bundled launcher may start an
   exact pinned Codex process for the same lane.
6. The project homepage is https://github.com/Demonbane18/astral-orchestrator.
7. The MIT-licensed Sol Advisor source may be adapted with preserved notice.

## Route contract

| Responsibility | Required route |
|---|---|
| Requirements, architecture, decomposition, cross-lane integration | Sol at configured effort (High default) |
| Narrow, repeatable, fully specified execution | Luna at configured effort (XHigh default) |
| Context-heavy implementation, debugging, component/external integration, refactoring | Terra at configured effort (XHigh default) |
| Fresh final review | Sol at configured reviewer effort (High default), with requested read-only sandbox |

The default efforts are Sol High, Luna XHigh, Terra XHigh, and reviewer Sol High.
Per-lane overrides are stored outside the plugin cache. A custom worker or reviewer
effort uses the exact-process launcher so a native profile cannot override it.

Quick mode is the explicit exception: tiny, reversible work stays in the verified Sol
primary at its configured effort. Guided and Careful use pinned lanes whenever bounded
execution exists.

## Tech stack

- Codex marketplace JSON and plugin manifest JSON
- Markdown Codex skill and one-level reference files
- Codex custom-agent TOML profiles
- POSIX shell for setup, exact-copy installation, and verification
- Python 3.11+ standard library for tests, exact-process launching, and allowlisted
  runtime evidence
- No added API key, external service beyond Codex, analytics, direct network client, or
  background process

## Commands

- Test: python3 -B -m unittest discover -s tests -v
- Verify package: sh plugins/astral-orchestrator/scripts/verify.sh
- Check setup: sh scripts/setup.sh --dry-run
- Score local trials: python3 plugins/astral-orchestrator/scripts/benchmark-scorecard.py benchmarks/trials.jsonl
- Validate skill: uv run --no-project --with pyyaml python "$HOME/.codex/skills/.system/skill-creator/scripts/quick_validate.py" plugins/astral-orchestrator/skills/astral-orchestrator
- Validate plugin: uv run --no-project --with pyyaml python "$HOME/.codex/skills/.system/plugin-creator/scripts/validate_plugin.py" plugins/astral-orchestrator

## Safety and failure behavior

- Agent installation never overwrites a different file.
- Agent removal deletes only exact, unmodified Astral Orchestrator profiles.
- Destructive, irreversible, credential, publishing, and production actions retain an
  explicit user-confirmation gate.
- Each worker receives exact ownership and must preserve concurrent edits.
- Agent reports are inspected and independently verified in the primary session.
- Missing or mismatched role, model, or effort evidence stops the route; no silent
  fallback is allowed.
- Unsupported effort settings fail before a delegated Codex process starts.
- Careful review cannot claim ship unless required read-only isolation is observed.

## Success criteria

1. One setup command installs one plugin and exactly three namespaced profiles.
2. Profiles pin Sol High, Luna XHigh, and Terra XHigh exactly as specified.
3. The skill routes by work characteristics and parallelizes only non-overlapping cards.
4. Runtime inspection emits only allowlisted route fields.
5. A non-technical reader can install, invoke, update, share, troubleshoot, and remove it.
6. Tests, package verification, and official validators pass.
7. The original Sol Advisor copyright and MIT permission notice remain included.
8. A non-technical user can show, change, and reset every lane's effort independently.
