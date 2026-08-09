# Spec: Astral Orchestrator v3.3

## Objective

Provide a beginner-friendly Codex plugin with an additive portable skill package that delivers observable model-routed
orchestration. A Sol task leads, assigns bounded work to Luna or Terra based on the work,
integrates and verifies the result, then uses a fresh Sol reviewer. Explicit opt-in Morph
can route only a bounded worker to a user-selected model, and explicit opt-in Constellation
can fan out independent cards within verified capacity. Each fixed lane's reasoning effort
is configurable without editing profiles.

The user should not need to understand TOML files, runtime logs, or agent APIs. Two
GitHub marketplace commands install the plugin and its bundled exact-process launcher.
The optional setup command installs three namespaced native profiles for faster,
more-ergonomic named-agent selection. When an exact route cannot be proven, the workflow
stops rather than claiming a generic fallback was the requested orchestration.

Version 3.1 adds a local JSONL benchmark scorecard. It compares paired, repeated Astral
and single-Sol trials only after validating frozen task fingerprints, identical
acceptance checks, route evidence, and consistently available optional metrics. It
summarizes supplied data without calling models or claiming a result that was not
recorded.

Version 3.2 adds explicit opt-in Measured mode: one canonical frozen work card, an
owner-only non-secret local ledger, deterministic pinned-lane routing, and fresh review.
The v3.2 package also documents explicit opt-in Morph and Constellation routes without a
version bump: Sol remains the verified primary and final reviewer in every mode.

Version 3.3.0 adds a root portable manifest alongside the existing Codex manifest. The
portable package standardizes skill discovery only. On capable non-Codex hosts, an
explicit Morph or Constellation route requires observable model, worker-context, and
fresh-reviewer capabilities; it does not generalize fixed Codex lanes.

## Identity and migration

Version 3.0.0 was the breaking identity migration from the former Project Pilot
identifiers. The current product version is 3.3.0. The normalized plugin, marketplace,
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
4. Optional native custom agents, when installed, live in Codex's personal agents
   directory and are discovered in a newly started task.
5. When native profiles are missing or customized, or a host lacks exact native
   custom-agent selection, the bundled launcher starts an exact pinned Codex process for
   the same lane.
6. The project homepage is https://github.com/Demonbane18/astral-orchestrator.
7. The MIT-licensed Sol Advisor source may be adapted with preserved notice.
8. Where `CODEX_THREAD_ID` and local rollout evidence are available, the bundled primary
   checker can automatically inspect the current primary without reading rollout contents
   itself or exposing prompts.
9. OpenCodex, if a user chooses it for Morph, is installed and configured independently;
   Astral neither modifies its configuration nor handles provider credentials.
10. Non-Codex hosts may discover the portable skill but must expose each required Morph or
    Constellation capability before the corresponding portable route can run.

## Route contract

| Responsibility | Required route |
|---|---|
| Requirements, architecture, decomposition, cross-lane integration | Sol at configured effort (High default) |
| Narrow, repeatable, fully specified execution | Luna at configured effort (XHigh default) |
| Context-heavy implementation, debugging, component/external integration, refactoring | Terra at configured effort (XHigh default) |
| Fresh final review | Sol at configured reviewer effort (High default), with requested read-only sandbox |
| Explicit Morph worker | User-selected native or `provider/model` worker at requested effort; Sol remains primary and reviewer |
| Explicit Constellation first wave | Cost-aware non-Sol workers by default, only for independent ready cards within advertised capacity |

The default efforts are Sol High, Luna XHigh, Terra XHigh, and reviewer Sol High.
Per-lane overrides are stored outside the plugin cache. A custom worker or reviewer
effort uses the exact-process launcher so a native profile cannot override it.

Quick mode is the explicit exception: tiny, reversible work stays in the verified Sol
primary at its configured effort. Guided and Careful use pinned lanes whenever bounded
execution exists.
Measured is never auto-selected. Sol freezes exactly one canonical card and chooses Luna
only for fully specified narrow mechanical work with exact checks and no flags; any
debugging, integration, cross-component, context-heavy, or moderate-ambiguity flag uses
Terra. Ambiguous routing receives exactly one Luna and one Terra behaviorally read-only
probe with the identical card; material disagreement defaults to Terra.
Morph and Constellation are never auto-selected. Morph stores the exact worker model id
and requested effort in each card, but does not claim that a provider accepted native
effort semantics. Constellation starts only the independent first wave that fits the
configured roster and host-advertised available slots after the primary uses one. It falls
back to serial Guided-style routing when capacity or independence cannot be proven.

## Tech stack

- Codex marketplace JSON and plugin manifest JSON, plus a root portable manifest JSON
- Markdown Codex skill and one-level reference files
- Codex custom-agent TOML profiles
- POSIX shell for setup, exact-copy installation, and verification
- Python 3.11+ standard library for tests, exact-process launching, and allowlisted
  runtime evidence
- No added API key, external service beyond Codex, analytics, direct network client, or
  background process; OpenCodex remains an optional user-owned route, not a dependency

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
- The primary checker returns allowlisted `match`, `mismatch`, or `unavailable` JSON and
  exits zero only for the exact configured Sol route; only unavailable evidence may use
  the one-time user-confirmation fallback.
- Unsupported effort settings fail before a delegated Codex process starts.
- Morph never changes the primary or final reviewer, and its requested effort is not a
  claim of verified upstream-native effort semantics.
- Constellation uses no extra Sol implementers by default and falls back to serial routing
  unless it can prove independent ownership and available capacity.
- Portable routes never claim fixed lane names, actual model/effort, concurrency, or fresh
  review without observable host evidence.
- Careful review cannot claim ship unless required read-only isolation is observed.
- Measured uses an unpersisted Prepare step, one persisted freeze/preflight/route base,
  one or more numbered implementation/verification/review attempts, and Complete only
  after a ship verdict. Its owner-only local state rejects symlinks and records
  prospective/finished events without secrets.

## Success criteria

1. Two GitHub marketplace commands install the plugin; optional setup installs exactly
   three namespaced native profiles.
2. Profiles pin Sol High, Luna XHigh, and Terra XHigh exactly as specified.
3. The skill routes by work characteristics and parallelizes only non-overlapping cards.
4. Runtime inspection emits only allowlisted route fields.
5. A non-technical reader can install, invoke, update, share, troubleshoot, and remove it.
6. Tests, package verification, and official validators pass.
7. The original Sol Advisor copyright and MIT permission notice remain included.
8. A non-technical user can show, change, and reset every lane's effort independently.
9. A Measured run keeps one canonical card, reproducible safe state, exact routing
   evidence, fresh verification after fixes, and a new fresh reviewer.
10. Morph and Constellation remain explicit opt-ins with the fixed Sol primary and reviewer
    guarantees preserved.
11. The root portable manifest and fixed `skills/` discovery are verified without changing
    the existing Codex/OpenAI manifest or route contract.
