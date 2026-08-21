# Spec: Astral Orchestrator v3.6

## Objective

Provide a beginner-friendly Codex plugin with an additive portable skill package that delivers observable model-routed
orchestration. A Sol task leads, assigns bounded work to Luna or Terra based on the work,
integrates and verifies the result, then uses a fresh Sol reviewer. Explicit opt-in Morph
can route only a bounded worker to a user-selected model, and explicit opt-in Constellation
can fan out independent cards within verified capacity. Each fixed lane's reasoning effort
is configurable without editing profiles.

Explicit opt-in Singularity is the token-disciplined single-session route for meaningful
low- or medium-risk work: one verified Sol primary at the configured orchestrator effort,
one compact work card, no subagents, and one Sol self-review. It is distinct from Comet,
never automatic, and Event Horizon overrides Singularity for high-risk work.

The user should not need to understand TOML files, runtime logs, or agent APIs. Two
GitHub marketplace commands install the plugin. On current Codex MultiAgentsV2 hosts,
native explicit spawning is the standard route and the optional setup command is only a
faster, more-ergonomic named-agent enhancement. When an exact route cannot be proven,
the workflow stops rather than claiming a generic fallback was the requested
orchestration.

## Current MultiAgentsV2 native route

On a current Codex **MultiAgentsV2** host, native explicit spawning is the standard route
for Orbit, Event Horizon, and Pulsar implementation and review lanes. Before spawning,
inspect `collaboration.spawn_agent` and require these fields: `agent_type`, `task_name`,
`model`, `reasoning_effort`, and `fork_turns`. Every child receives a complete standalone
work packet. A Luna or Terra implementation uses the built-in native worker with the
exact model and configured effort:

```text
collaboration.spawn_agent({
  agent_type: "worker",
  task_name: "<unique_lowercase_task_name>",
  model: "gpt-5.6-luna" or "gpt-5.6-terra",
  reasoning_effort: "<configured lane effort>",
  fork_turns: "none",
  message: "<complete standalone work packet>"
})
```

When a matching custom reviewer profile is unavailable, a reviewer uses the built-in
native default with `model: "gpt-5.6-sol"`, the configured reviewer effort, its own
distinct unique reviewer `task_name`, `fork_turns: "none"`, and a complete standalone
review packet. Custom agent file values take precedence over explicit spawn values, so
use an Astral custom profile only when its fixed model and effort match the effective
settings and its fixed capability is needed. A missing, customized, or mismatched
optional profile does not force a nested CLI process on a v2 host; use the appropriate
built-in native agent with explicit values.

The reviewer spawn is explicit as well:

```text
collaboration.spawn_agent({
  agent_type: "default",
  task_name: "<unique_lowercase_reviewer_task_name>",
  model: "gpt-5.6-sol",
  reasoning_effort: "<configured reviewer effort>",
  fork_turns: "none",
  message: "<complete standalone review packet>"
})
```

The bundled exact-process launcher is a **legacy exact-process fallback** only for a host
whose collaboration tool lacks one or more required v2 controls—`agent_type`, `task_name`,
`model`, `reasoning_effort`, or `fork_turns`. It is not the current route and is not
selected merely because an optional profile is missing or customized. If the native v2
route or this compatibility fallback cannot be proven, stop before implementation.

Version 3.1 adds a local JSONL benchmark scorecard. It compares paired, repeated Astral
and single-Sol trials only after validating frozen task fingerprints, identical
acceptance checks, route evidence, and consistently available optional metrics. It
summarizes supplied data without calling models or claiming a result that was not
recorded.

Version 3.2 added explicit opt-in Measured mode: one canonical frozen work card, an
owner-only non-secret local ledger, deterministic pinned-lane routing, and fresh review.
The v3.2 package also documents explicit opt-in Morph and Constellation routes without a
version bump: Sol remains the verified primary and final reviewer in every mode.

Version 3.3.0 adds a root portable manifest alongside the existing Codex manifest. The
portable package standardizes skill discovery only. On capable non-Codex hosts, an
explicit Morph or Constellation route requires observable model, worker-context, and
fresh-reviewer capabilities; it does not generalize fixed Codex lanes.

Version 3.3.1 makes exact-process and Morph dry runs select a host-compatible Codex
runtime by proving that the active configuration and model catalog parse before any
worker inference. It preserves the requested model, effort, sandbox, workdir, developer
instructions, and private standard-input packet without changing OpenCodex configuration.

Version 3.4.0 adds live, allowlisted Astral status panels to substantive progress updates,
documents copy-ready prompts for its six modes, and makes Constellation's default Sol High
and custom Morph dry-run-to-runtime evidence sequence explicit and testable.

Version 3.5.0 makes native MultiAgentsV2 spawning the standard Codex route, changes the
default worker efforts to Luna Max and Terra High, preserves configurable lane efforts,
and guarantees that Astral Status uses a valid unfenced Markdown table. The bundled
process launcher remains available only for hosts without the required native-v2 fields.

## Identity and migration

Version 3.0.0 was the breaking identity migration from the former Project Pilot
identifiers. Version 3.6.0 renames the primary modes to Comet, Orbit, Event Horizon, and
Pulsar while retaining Quick, Guided, Careful, and Measured as advisory prompt aliases.
The current product version is 3.6.0. The normalized plugin, marketplace,
skill, and profile prefix is
astral-orchestrator; TOML agent names use astral_orchestrator. Route evidence begins
with ASTRAL_ORCHESTRATOR_ROUTE, and persistent effort settings live at
~/.codex/astral-orchestrator/effort-levels.toml.

Users install the v3 package as new. The former profile and settings names are not
modified automatically.

## Assumptions

1. The target is the current Codex plugin and custom-agent format.
2. The primary task starts with gpt-5.6-sol at the configured reasoning effort; High is
   the default. The default implementation efforts are Luna Max and Terra High, and the
   reviewer default is Sol High.
3. Recipients have access to gpt-5.6-luna, gpt-5.6-terra, and gpt-5.6-sol.
4. Optional native custom agents, when installed, live in Codex's personal agents
   directory and are discovered in a newly started task. Their file values take
   precedence over explicit spawn values.
5. On a current MultiAgentsV2 host, native explicit spawning uses the required
   `agent_type`, `task_name`, `model`, `reasoning_effort`, and `fork_turns` fields. A host
   that lacks one or more of those five controls—`agent_type`, `task_name`, `model`,
   `reasoning_effort`, or `fork_turns`—may use the legacy exact-process launcher for the
   same lane.
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
| Narrow, repeatable, fully specified execution | MultiAgentsV2 native `worker`, explicitly pinned to Luna at configured effort (Max default) |
| Context-heavy implementation, debugging, component/external integration, refactoring | MultiAgentsV2 native `worker`, explicitly pinned to Terra at configured effort (High default) |
| Fresh final review | MultiAgentsV2 native `default`, explicitly pinned to Sol at configured reviewer effort (High default) |
| Explicit Singularity | One verified Sol primary at configured orchestrator effort; no child agents or fresh reviewer |
| Explicit Morph worker | User-selected native or `provider/model` worker at requested effort; Sol remains primary and reviewer |
| Explicit Constellation first wave | Cost-aware non-Sol workers by default, only for independent ready cards within advertised capacity |

The default efforts are Sol High, Luna Max, Terra High, and reviewer Sol High. The four
configurable effort levels are independent: every lane reads its value from the per-lane
settings file outside the plugin cache.
Explicit native spawn values are used on current v2 hosts: provide `agent_type`, a unique
lowercase `task_name`, `model`, `reasoning_effort`, and `fork_turns: "none"`. A custom
profile is used only when its fixed values match because custom agent file values take
precedence. A host lacking one or more of `agent_type`, `task_name`, `model`,
`reasoning_effort`, and `fork_turns` may use the legacy exact-process fallback.

Comet mode is the explicit exception: tiny, reversible work stays in the verified Sol
primary at its configured effort. Orbit and Event Horizon use pinned lanes whenever bounded
execution exists.
Singularity is an explicit opt-in for larger low- or medium-risk multi-step work in the
same verified Sol primary at configured orchestrator effort. It never forces Max, starts
no child lanes or planning probes, and uses one Sol self-review with actual change and
verification evidence. It keeps no more than five active steps and one in progress, uses
the smallest sufficient intervention, and stops after one proportional verification pass
unless evidence is ambiguous, contradictory, or defective. A user who wants Sol Max must
configure the orchestrator effort and start a new task. Event Horizon overrides Singularity. All
modes run the primary checker; Singularity requires observed/verified Sol model and
effort, must stop on unavailable evidence, and user confirmation cannot satisfy or
override that requirement.
Pulsar is never auto-selected. Sol freezes exactly one canonical card and chooses Luna
only for fully specified narrow mechanical work with exact checks and no flags; any
debugging, integration, cross-component, context-heavy, or moderate-ambiguity flag uses
Terra. Ambiguous routing receives exactly one Luna and one Terra behaviorally read-only
probe with the identical card; material disagreement defaults to Terra.
Morph and Constellation are never auto-selected. Morph stores the exact worker model id
and requested effort in each card, but does not claim that a provider accepted native
effort semantics. Constellation starts only the independent first wave that fits the
configured roster and host-advertised available slots after the primary uses one. It falls
back to serial Orbit-style routing when capacity or independence cannot be proven.

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
- Missing or mismatched role, model, effort, or native spawn evidence stops the route; a
  missing optional profile on a current v2 host is handled by the explicit built-in
  native route, not by a silent launcher fallback.
- The primary checker returns allowlisted `match`, `mismatch`, or `unavailable` JSON and
  exits zero only for the exact configured Sol route. When evidence is unavailable, only
  non-Singularity modes may use the one-time user-confirmation fallback. Singularity
  requires observed/verified Sol model and effort, must stop on unavailable evidence, and
  user confirmation cannot satisfy or override that requirement; mismatch and invalid
  evidence block every route.
- Unsupported effort settings fail before a delegated Codex process starts.
- Morph never changes the primary or final reviewer, and its requested effort is not a
  claim of verified upstream-native effort semantics.
- Constellation uses no extra Sol implementers by default and falls back to serial routing
  unless it can prove independent ownership and available capacity.
- Portable routes never claim fixed lane names, actual model/effort, concurrency, or fresh
  review without observable host evidence.
- Event Horizon review cannot claim ship unless required read-only isolation is observed.
- Singularity has no subagents or fresh reviewer; a higher-priority instruction requiring
  delegation makes Singularity unavailable rather than a substituted route.
- Pulsar uses an unpersisted Prepare step, one persisted freeze/preflight/route base,
  one or more numbered implementation/verification/review attempts, and Complete only
  after a ship verdict. Its owner-only local state rejects symlinks and records
  prospective/finished events without secrets.

## Success criteria

1. Two GitHub marketplace commands install the plugin; optional setup installs exactly
   three namespaced native profiles.
2. Profiles pin Sol High, Luna Max, and Terra High exactly as specified, while native v2
   children receive the same model and configured effort explicitly.
3. The skill routes by work characteristics and parallelizes only non-overlapping cards.
4. Runtime inspection emits only allowlisted route fields.
5. A non-technical reader can install, invoke, update, share, troubleshoot, and remove it.
6. Tests, package verification, and official validators pass.
7. The original Sol Advisor copyright and MIT permission notice remain included.
8. A non-technical user can show, change, and reset every lane's effort independently.
9. A Pulsar run keeps one canonical card, reproducible safe state, exact routing
   evidence, fresh verification after fixes, and a new fresh reviewer.
10. Morph and Constellation remain explicit opt-ins with the fixed Sol primary and reviewer
    guarantees preserved.
11. Singularity remains explicit opt-in, uses one verified Sol primary with no subagents
    or fresh reviewer, and yields to Event Horizon for high-risk work.
12. The root portable manifest and fixed `skills/` discovery are verified without changing
    the existing Codex/OpenAI manifest or route contract.
