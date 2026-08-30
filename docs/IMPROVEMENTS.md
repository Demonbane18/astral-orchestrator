# Design review and improvements

## Executive assessment

The current Astral Orchestrator v3.8 design provides the model-routed workflow adapted
from Sol Advisor: one Sol orchestrator, two explicitly pinned implementation lanes, exact
route evidence, bounded ownership, independent verification, and a fresh pinned Sol
reviewer. On current Codex MultiAgentsV2 hosts, native explicit spawning is the standard
route; the bundled launcher is compatibility infrastructure only for hosts that lack one
or more of `agent_type`, `task_name`, `model`, `reasoning_effort`, and `fork_turns`.

The design focuses on usability without weakening the route contract. Its eight primary
modes are Comet for tiny self-session work, Orbit as the default project route, Event
Horizon for high-risk gates and concise repair-capable review, Singularity for bounded single-agent
work, Hypernova for maximum safe native Sol Ultra throughput, Pulsar for explicit
evidence, and opt-in Morph and Constellation specialist routes.
Singularity is an explicit low-/medium-risk route: one verified Sol performs the work,
no subagents are spawned, no fresh reviewer is used, and one proportional self-review
checks the result. Event Horizon overrides Singularity whenever its higher-risk gate
applies. The design gives non-technical users a two-command GitHub install with optional
namespaced native profiles, and refuses to silently downgrade a requested model or effort.

Hypernova is the explicit performance-first opposite of Singularity. It requires an
observed Sol Ultra primary, all five native MultiAgentsV2 controls, observed capacity,
built-in Sol Ultra workers for every implementation lane, and a mandatory fresh built-in
Sol Ultra reviewer. It does not change the normal persisted effort settings, invent work,
allow worker delegation, or fall back to another route. High-risk cards retain Event
Horizon confirmation safeguards.

Event Horizon applies Singularity discipline to multi-agent work: YAGNI, one compact
in-context dependency graph, parallel ready cards or the shallowest useful hierarchy,
the smallest relevant checks, and one concise workspace-write review-and-repair pass. The reviewer may fix bounded obvious
issues directly and reports at most three findings. High-risk Pulsar, Morph, and
Constellation work inherits this safeguard.

## Current MultiAgentsV2 native route

For Orbit, Event Horizon, Pulsar, Morph, Constellation, and Hypernova work, inspect the current
`collaboration.spawn_agent` contract first. A MultiAgentsV2 host must expose
`agent_type`, `task_name`, `model`, `reasoning_effort`, and `fork_turns`. Native children
receive a complete standalone packet and explicit model and configured effort. Luna and
Terra use the built-in native worker. The four configurable effort levels are independent,
with Sol High for the orchestrator and reviewer, Luna Max, and Terra High as the defaults:

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

A fresh reviewer without a matching custom reviewer profile uses the built-in native
default with `model: "gpt-5.6-sol"`, the configured reviewer effort, its own distinct
unique reviewer `task_name`, `fork_turns: "none"`, and a complete standalone review
packet. Custom agent file values take precedence over explicit spawn values. Use an
Astral custom profile only when its fixed model and effort match the effective settings
and its fixed capability is needed; otherwise use the built-in native worker or default
with explicit values. Missing or customized optional profiles do not force a nested CLI
process on a v2 host.

The reviewer spawn is explicit too:

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

Hypernova uses a separate fixed native contract. `check-primary.py --require-sol-ultra`
requires the already-started primary to be observed `gpt-5.6-sol` Ultra without mutating
normal settings. Each real ready card uses a built-in `worker`, a distinct unique
lowercase `task_name`, `model: "gpt-5.6-sol"`, `reasoning_effort: "ultra"`, and
`fork_turns: "none"`; workers cannot delegate. Wave size is
`min(ready independent cards, observed available slots - 1 primary)` and is recalculated
after integration. The mandatory fresh reviewer uses a built-in `default` with the same
exact Sol Ultra route and its own task name. The Sol High custom reviewer is ineligible.
Missing or mismatched evidence blocks, and mismatched output is discarded.

The bundled launcher is a **legacy exact-process fallback** only when the host
collaboration tool lacks one or more required v2 controls—`agent_type`, `task_name`,
`model`, `reasoning_effort`, or `fork_turns`. It is not selected merely because a profile
is missing or customized. If the native route or the compatibility fallback cannot be
proven, stop rather than silently substituting another model, effort, or route.

## Route comparison

| Area | Sol Advisor | Astral Orchestrator |
|---|---|---|
| Main session | Sol with high reasoning | Sol at configured effort; High by default |
| Focused lane | Luna with a pinned high reasoning setting | MultiAgentsV2 native `worker` or matching profile; Luna at configured effort; Max by default |
| Context lane | Terra with a pinned high reasoning setting | MultiAgentsV2 native `worker` or matching profile; Terra at configured effort; High by default |
| Reviewer | Fresh Sol High, requested read-only | MultiAgentsV2 native `default` or matching profile; Sol at configured effort; High by default |
| Routing proof | Native metadata plus allowlisted rollout inspection | Explicit v2 spawn fields plus allowlisted rollout inspection |
| User controls | Architecture-oriented workflow | Comet, Orbit (default), Event Horizon, Singularity (one verified Sol/no subagents/no fresh reviewer/one proportional self-review), Hypernova (observed Sol Ultra/native maximum-safe waves/mandatory fresh Sol Ultra review), Pulsar, Morph, and Constellation; high-risk Hypernova cards inherit Event Horizon gates |
| Installation | Companion agent installer | Two-command GitHub plugin install plus optional conflict-safe native-profile setup; legacy launcher only for hosts lacking one or more of `agent_type`, `task_name`, `model`, `reasoning_effort`, and `fork_turns` |
| Removal | Manual profile cleanup | --remove deletes only exact, unmodified profiles |
| Failure | Stop when strict preflight fails | Same; never silently substitute another lane |
| Effort tuning | Profile-oriented | One command and persistent per-lane settings |

## Improvements beyond the original

1. **Two simple install choices.** Two GitHub marketplace commands install the plugin
   for native MultiAgentsV2 routing. `sh scripts/setup.sh` remains an optional,
   conflict-safe native-profile install for faster named-agent selection; the bundled
   launcher is a legacy fallback only for hosts lacking one or more of `agent_type`,
   `task_name`, `model`, `reasoning_effort`, and `fork_turns`.
2. **Safer lifecycle.** Existing different profiles are never overwritten, and modified
   profiles are never removed automatically.
3. **No extra JSON package.** The runtime inspector uses Python 3's standard library
   instead of requiring jq.
4. **Clear lane language.** Luna handles repeatable work; Terra handles context-heavy
   work; Sol retains requirements, architecture, integration, and acceptance.
5. **Proportional orchestration.** Comet avoids coordination overhead; Singularity uses
   one verified Sol with no subagents, no fresh reviewer, and one proportional self-review
   for bounded low-/medium-risk work; and Orbit, Event Horizon, Pulsar, Morph, and
   Constellation use explicit native v2 routes whenever the host exposes them. Hypernova
   is the opt-in opposite: exact Sol Ultra across every native lane and every safely usable
   slot, without invented cards or a fallback route. Event Horizon overrides Singularity
   and supplies the confirmation gates for high-risk Hypernova cards.
6. **Efficient review.** The reviewer uses workspace-write, fixes bounded obvious issues
   directly, and returns one verdict plus at most three findings.
7. **Useful concurrency.** Orbit, Event Horizon, Pulsar, Morph, and Constellation launch
   independent ready cards in parallel and may authorize bounded child workers. Comet
   (Quick) and Singularity remain strictly single-session. Hypernova launches the maximum
   safe wave of exact Sol Ultra workers and forbids downstream delegation.
8. **Native-first explicit routing.** Current MultiAgentsV2 hosts receive explicit
   `agent_type`, `task_name`, `model`, `reasoning_effort`, and `fork_turns` values with a
   complete packet. Built-in native worker/default routes keep missing or customized
   optional profiles from changing the requested route.
9. **Upgrade-resistant effort controls.** Users can tune all four lanes without editing
   profiles. Custom profile values take precedence, so matching profiles are used only
   when their fixed model and effort agree; otherwise native built-ins receive explicit
   values. Unsupported values fail clearly instead of being downgraded.
10. **Explicit Pulsar evidence.** Pulsar freezes one work card and checks, records a
   non-secret local phase ledger, and probes both candidate lanes only for ambiguity.
11. **Explicit maximum-performance route.** Hypernova requires observed Sol Ultra from
    primary through mandatory fresh review, all five native controls, and observed
    capacity. It has no legacy/process/portable/serial/self-review/model/effort fallback,
    and “go nuts” does not bypass safety or authorization.

## Version 3 identity migration

Version 3.0.0 is intentionally breaking: it renames the former Project Pilot package to
Astral Orchestrator. The plugin and marketplace name are astral-orchestrator, TOML agent
names use astral_orchestrator, launcher proof starts with ASTRAL_ORCHESTRATOR_ROUTE, and
settings now persist at ~/.codex/astral-orchestrator/effort-levels.toml.

The new repository home is https://github.com/Demonbane18/astral-orchestrator. The former
settings file is not silently imported because it belongs to a different profile
namespace. The migration instructions in the website documentation and CHANGELOG make
the required user action explicit.

## Tradeoffs

Strict normal routing requires recipients to have all three models and to start a new task
after profile installation. Hypernova additionally requires account access to Sol Ultra
and observed native capacity. This is less portable than generic delegation, but it
directly satisfies the requirement for a real model-routed orchestrator.

Pulsar is intentionally slower and more model-intensive than Orbit. It is never an
automatic default: users opt in when a frozen card and reproducible evidence are worth it.

Runtime rollout formats are host implementation details and may change. The inspector
therefore rejects missing or inconsistent fields instead of guessing, and the skill
prefers trustworthy launch metadata when the host exposes every required field.

## Recommended next improvements

1. Test installation from a clean Codex profile and a remote GitHub checkout.
2. Confirm all three models are available to the intended recipients.
3. Add a PowerShell installer if Windows recipients need it.
4. Prefer public spawn metadata over rollout inspection when the host exposes every
   required field consistently.

## Historical validation evidence

The former Project Pilot 2.1 release candidate passed 23 repository contract tests,
package verification, setup dry-run, whitespace checks, and the official Codex skill and
plugin validators. The tests covered exact profile pins, conflict-safe installation and
removal, allowlisted runtime evidence, exact-process command construction, bounded prompt
handling, per-lane effort configuration and validation, route selection, confirmation
boundaries, and beginner documentation.

This historical evidence predates the current MultiAgentsV2 native controls. Forward
testing on Codex CLI 0.144.5 showed why the compatibility route was necessary at that
time: a generic subagent given a Luna-looking task name still ran Sol High, and the
package rejected that result. Separate historical launcher sessions then proved Luna
XHigh with workspace-write, Terra XHigh with workspace-write, and Sol High with read-only
review. Those old XHigh values are not the current defaults.

## Source reviewed

- Repository: https://github.com/DannyMac180/sol-advisor
- Revision: 92f0fb105854e0fa606bdc98bfe688411e1db989
- Review date: 2026-08-02
- License: MIT
