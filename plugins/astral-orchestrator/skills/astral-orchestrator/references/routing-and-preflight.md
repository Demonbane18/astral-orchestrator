# Routing and preflight

Use this reference only before a Codex child launch or when its evidence needs inspection.
Normal modes keep the detected primary effort and use configured child efforts. Hypernova
uses Sol Max children by default or Astra at its configured effort. Primary verification
lives in primary-verification.md.

## Exact route contract

| Role | Native v2 agent type | Required model | Default effort | Best work |
|---|---|---|---|---|
| Orchestrator | Primary session | Current `gpt-6-sol`, `gpt-6-luna`, or `gpt-6-astra` | Observed session effort | Requirements, architecture, decomposition, cross-lane integration, acceptance |
| Deep-reasoning worker | Built-in `worker` | `gpt-6-astra` | `medium` | Bounded difficult diagnosis or synthesis whose benefit justifies the cost |
| Focused worker | Built-in `worker`, or matching `astral_orchestrator_luna_implementer` | `gpt-6-luna` | `max` | Narrow, repeatable, fully specified, mechanical, or high-volume execution |
| Context worker | Built-in `worker`, or matching `astral_orchestrator_sol_implementer` | `gpt-6-sol` | `high` | Context-heavy implementation, debugging, component/external integration, and moderate refactoring |
| Reviewer | Built-in `default`, or matching `astral_orchestrator_sol_reviewer` | `gpt-6-sol` | `high` | Exact pinned Sol, concise workspace-write review-and-repair |
| Hypernova primary | Primary session | Current `gpt-6-sol`, `gpt-6-luna`, or `gpt-6-astra` | Observed session effort | Architecture, maximum-safe-wave planning, integration, and acceptance |
| Hypernova implementation | Built-in `worker` only | `gpt-6-sol` by default or `gpt-6-astra` | `max` or configured Astra effort | Every independently owned ready implementation card |
| Hypernova reviewer | Fresh built-in `default` only | `gpt-6-sol` | `high` | Mandatory pinned review after integrated verification |

The main session owns lane selection and remains accountable for the combined result.
Do not silently substitute a model, effort, or differently configured custom role. On a
current v2 host, deliberately using the built-in native worker for Astra, Luna, or Sol, or the
built-in native default for a reviewer, with the exact requested model and effort is the
standard route, not a substitution.

The effective values come from
`${CODEX_HOME:-~/.codex}/astral-orchestrator/effort-levels.toml`. When the file is absent,
use the defaults in the table. Supported setting names are `minimal`, `low`, `medium`,
`high`, `xhigh`, `max`, and `ultra`; the last two are model- and account-dependent.
Never silently downgrade a value that Codex rejects.
GPT-5.6 Sol, Luna, and Terra remain explicit legacy choices only; they are never
automatic candidates. The exact-process launcher exposes `legacy-luna`, `terra`,
and `legacy-reviewer` for those older routes; native agents must explicitly pin
the selected legacy model and effort. GPT-6 Sol and Luna do not support Ultra.

## Optional TypeSafe and Adaptive judgments

The separate TypeSafe Session plugin keeps independent TypeSafe and Adaptive states
for one task. When either is on,
prepare a short non-sensitive task summary and observed model/effort availability,
then run `../../scripts/choose-worker.py` with a private JSON input file. The selector
first enforces mode, delegation permission, settled acceptance, exact user choices,
and observed availability. `TypeSafe on` uses Jev Choice for the worker model and
keeps configured effort. `Adaptive on typesafe` or `Adaptive on openrouter` uses
Choice and Score in one request to select a worker model and valid effort per card.
If both are on, make only that one Adaptive request. An explicit model remains fixed;
an explicit effort remains fixed; the fresh Sol High reviewer never enters Jev's
candidates. Adaptive may vary Hypernova's default worker effort. Do not adapt a
older process launcher that cannot apply the selected effort.
For OpenCodex transport, set `transport` to `opencodex` and pass the available
models and efforts observed on the current Codex host. The selector additionally
checks exact model IDs and efforts against the active Codex home's OpenCodex
catalog. Use the compatible Codex runtime probe before any exact-process launch.
OpenCodex remains model transport, not the Jev provider or routing authority.
Non-OpenAI provider models remain explicit Morph selections.
For Comet or Singularity, set `recommend_only: true` only to display a future-task
recommendation; never use that result to spawn or change the current primary.
The primary remains in charge of requirements, execution, and authorization. No
worker is launched from a missing key, unavailable route, invalid answer, or uncertain
choice; report the reason and continue independent work. When both toggles are off,
use the deterministic lane rules below without an API call.

If a separate Astra-Ares CLI is active, map only its documented `Astra-Jev`,
`Sol-Jev`, or `Luna-Jev` selections to the corresponding GPT-6 model. Use
`../../scripts/inspect-ares.py` with the observed primary model and effort and
the selected Adaptive provider. A provider mismatch blocks the combined route.
The provider checker reports compatibility, not native effort application;
the primary checker requires Ares's applied checkpoint evidence for a logical
selection whose rollout omits effort. Ares currently documents single-agent CLI
checkpoints, not Desktop or multi-agent native adaptation. When the primary's
evidence source is `ares-native-checkpoint`, use only Comet or Singularity; block
delegated modes rather than claiming an untested Ares multi-agent path. Ordinary
Codex CLI or Desktop remains the route for Adaptive delegated work.

## Live Astral status updates

Codex plugins cannot pin a permanent native UI widget. Keep the user informed through a
compact **Astral status** panel in the first user-facing progress update, before and after
every child launch, when route evidence or state changes, and in the final handoff. Use the reusable
panel in `work-templates.md` for the detected primary, each selected worker, and the fresh
reviewer when review is required. For Singularity, use only the primary row and do
not repeat unchanged updates. For Hypernova, label each row with its own observed model and effort and include the
observed safe wave size without exposing packet contents. For Comet work, say that workers are not needed; for
any reviewer that is not yet required, say so instead of implying it is running.

Publish the panel only at these decision points:

- preflight, after recording the requested route and available primary evidence;
- launch, after a native spawn or exact-process request is made;
- evidence, only when it changes whether the route may continue;
- state changes, including when a lane is blocked, fails, returns, or verification
  completes;
- completion or failure, as part of the handoff or blocked report; and
- for long-running work, a periodic update only when there is new observable progress or
  enough elapsed time that silence would be misleading. Do not spam unchanged panels.

### Truthful states and evidence

Use states that describe what the host has actually shown: `planned`, `requested`,
`launched`, `running`, `returned`, `verified`, `blocked`, `failed`, or `not needed`.
`requested` means the route was asked for; it is not proof that a lane started.
`launched` requires a returned task or process id. Mark a lane `running` only when the
host reports it as running. `returned` means the lane replied or its process exited, not
that its change is accepted. `verified` requires the applicable runtime and work evidence
to have been inspected.

Keep requested and observed facts distinct in the model, effort, and evidence fields.
Requested values may state the configured route. Observed values require matching
runtime evidence from the primary checker, native spawn/startup metadata, runtime
inspector, or exact-process header. Do not label a lane observed, its model/effort
observed, or its state running merely because Astral requested that route. If evidence is
missing, say `observed: not yet available`; if it conflicts, state the conflict, mark the
lane blocked or failed as appropriate, and follow the existing stop rules. A
user-confirmed primary remains user-confirmed, not observed.

Keep the panel allowlisted: never include prompts, packet contents, messages, tool
arguments, credentials, secrets, personal data, or arbitrary file contents. A lane's
task/session id and the minimal route and check results are sufficient correlation.

## Child preflight

Read only the section for the next child route. The primary has already followed
[primary-verification.md](primary-verification.md); do not repeat that setup or load this
child guide for Comet or Singularity. Resolve effective child effort with
`../../scripts/configure-effort.py --show --json` relative to the skill directory before
launch, reusing unchanged settings within the task.

Before Orbit, Event Horizon, or Pulsar delegation:

1. Inspect the available `collaboration.spawn_agent` contract. A current Codex
   **MultiAgentsV2** host exposes all five required controls together:
   `agent_type`, `task_name`, `model`, `reasoning_effort`, and `fork_turns`.
2. When `agent_type`, `task_name`, `model`, `reasoning_effort`, and `fork_turns` are all
   present, use the standard native route with the complete standalone work packet. Pass
   a unique lowercase task name, the exact model and configured effort on every child,
   and set `fork_turns: "none"`. Missing or mismatched optional custom profiles are route
   evidence, not a native-v2 preflight failure.
3. Optionally run `../../scripts/install-agents.sh --check` to record profile state. A
   matching custom role is usable only when its fixed model and effort equal the effective
   settings, because custom agent file values take precedence over explicit spawn values.
   Otherwise choose the built-in native worker for Astra, Luna, or Sol, or built-in native
   default for a reviewer, with explicit fields.
4. Use the bundled launcher only as the legacy exact-process fallback when the host lacks
   one or more required v2 controls—`agent_type`, `task_name`, `model`,
   `reasoning_effort`, or `fork_turns`—and compatibility requires it. Require a successful
   dry run for the needed role, workdir, and private packet before launch.

Before Hypernova execution, instead require all five native MultiAgentsV2 controls in
step 1, observed host-advertised capacity, and at least one safely usable child slot after
the primary consumes one slot. Use only the built-in `worker` and built-in `default`
routes with exact Sol Max children by default or Astra at the configured effort. Custom
profiles with mismatched fixed values are ineligible. Missing controls or
capacity block Hypernova; do not run setup, a launcher dry run, or another fallback.

A failed child preflight blocks that lane and dependent work. Continue independent
already-authorized work; do not substitute routes or claim the blocked lane completed.
Missing or customized optional profiles on a current v2 host do not justify a process
fallback. Custom agent file values take precedence over explicit spawn values: use a
matching profile or the exact built-in route.

Hypernova uses [hypernova-mode.md](hypernova-mode.md) for its stricter capacity, selected
child, and fresh-review requirements. Morph and Constellation use their own references
only after explicit opt-in. Pulsar's frozen-card and resumption rules remain in its mode
reference. These modes preserve the detected primary and the configured child routes;
Hypernova uses its selected child contract independently of primary effort.

## Lane decision

Choose Luna when all of these are true:

- the output and acceptance conditions are explicit;
- the implementation is repeatable or mostly mechanical;
- the owned files are narrow and independent;
- little architectural or product judgment remains.

Choose Sol when architecture and acceptance are settled but one or more of these are
true:

- implementation depends on wider repository context;
- debugging requires tracing behavior across components;
- interfaces, integrations, or moderate refactors require careful judgment;
- the change has a wider but still bounded regression surface.

Choose Astra when the architecture and acceptance are settled and a bounded difficult
diagnosis or deep cross-domain synthesis is worth its added cost.

Keep the decision in the detected primary session at its observed effort when requirements,
architecture, safety boundaries, public interfaces, or acceptance criteria are unsettled.
The primary may settle the decision, then issue bounded execution to Astra, Luna, or Sol.
For Pulsar, the primary also retains decomposition, integration, and final route selection; use
its stricter deterministic selection rules rather than a general heuristic.

## Choose the execution mechanism

On a current MultiAgentsV2 host, prefer native spawning. For standard Astra, Luna, and Sol
delegation, use the built-in native worker and explicitly pin every child:

```text
collaboration.spawn_agent({
  agent_type: "worker",
  task_name: "<unique_lowercase_task_name>",
  model: "gpt-6-astra", "gpt-6-luna", or "gpt-6-sol",
  reasoning_effort: "<configured lane effort>",
  fork_turns: "none",
  message: "<complete standalone Astral packet>"
})
```

For standard reviewer delegation without a matching custom reviewer profile, use the
built-in native default and explicitly pin the fresh Sol child with its own distinct
unique lowercase task name:

```text
collaboration.spawn_agent({
  agent_type: "default",
  task_name: "<unique_lowercase_reviewer_task_name>",
  model: "gpt-6-sol",
  reasoning_effort: "<configured reviewer effort>",
  fork_turns: "none",
  message: "<complete standalone Astral review packet>"
})
```

For Hypernova's exact built-in Sol Max or configured Astra worker and reviewer examples, use
[hypernova-mode.md](hypernova-mode.md#exact-native-route). Do not load or duplicate those
launch recipes for an ordinary child. Its custom profiles remain ineligible.

The packet must name the intended Astral role, model, effort, ownership, boundaries,
checks, and whether downstream delegation is allowed. `agent_type: "worker"` is intentional for
Astra, Luna, and Sol implementation, while `agent_type: "default"` is intentional for a
reviewer without its matching custom profile. The explicit model and reasoning effort
preserve Astral's configured route. Do not treat a task name as an agent type.

Custom agent file values take precedence over explicit spawn values. Use an Astral custom
agent type only if its installed profile is byte-exact and its fixed model and effort
match the effective lane settings. It may then supply a fixed capability such as concise
bounded review-and-repair. A custom profile that conflicts with a requested
setting is not a reason to launch a nested process on a v2 host: use the appropriate
built-in native agent with the explicit values instead (`worker` for Astra, Luna, or Sol,
`default` for reviewer). A custom effort remains a per-lane setting, not a reason to use
a conflicting profile. If that native spawn cannot provide the requested model or effort,
block the lane; do not silently substitute.

Use the **legacy exact-process fallback** only when the collaboration tool lacks one or
more required v2 controls—`agent_type`, `task_name`, `model`, `reasoning_effort`, or
`fork_turns`—and a compatible legacy route is needed. Resolve `../../scripts/run-agent.py`,
write the complete standalone work packet to a private temporary regular file, then run:

```text
python3 run-agent.py --role <luna|sol|reviewer> --workdir <workspace> --prompt-file <packet>
```

The launcher reads the shipped profile, reads the effective effort settings, pins the
model and configured effort on `codex exec`, injects the profile's developer
instructions that forbid further delegation, and selects workspace-write for workers
and the reviewer. Before either a dry run or launch, it checks a small set of
Codex runtimes supplied by Astral, the host, the installed app, and the current command
environment. It selects the first runtime whose `codex features list` check proves that
the active user configuration and model catalog can be parsed. This check does not send
the work packet to a model. `ASTRAL_CODEX_PATH` may name an absolute executable as an
explicit override; an inherited `CODEX_CLI_PATH` is treated as a host hint. Invalid or
incompatible candidates are rejected, and no model or provider is substituted.

The allowlisted route evidence records `codex_runtime_source`, `codex_version`, and
`codex_config_probe: "pass"` without printing the executable path, candidate environment
values, configuration contents, credentials, or packet. It also marks whether the effort
is the default and whether a native profile would be compatible. A successful dry-run
therefore proves both this bundled exact-process contract and Codex configuration parsing
without requiring installed native profiles or invoking inference. Remove only the exact
temporary packet after the process exits. A non-zero exit blocks the lane.

## Spawn and runtime evidence

For a native v2 lane, immediately record the epoch seconds, choose a unique lowercase
task name, and spawn with explicit `agent_type`, `task_name`, `model`,
`reasoning_effort`, and `fork_turns: "none"`. Record whether it used the built-in worker
(Astra/Luna/Sol), built-in default (reviewer), or a matching custom role; in every case the
packet is complete and standalone. For a legacy exact-process lane, launch a new process
for every packet and capture its `ASTRAL_ORCHESTRATOR_ROUTE` header, Codex startup header,
session id, final response, and exit status. Both mechanisms allow downstream delegation
only when the complete packet explicitly authorizes it and supplies the child contract.
Hypernova is stricter: every child uses a built-in native route, its complete packet
forbids downstream delegation, and no exact-process evidence can satisfy the mode.

After launch, collect runtime evidence showing:

- the native v2 spawn used its recorded built-in or matching custom `agent_type`, unique
  `task_name`, exact `model`, configured `reasoning_effort`, and `fork_turns: "none"`; or
  the launcher header names the exact legacy role;
- an exact-process launcher reports a passing Codex configuration probe and the selected
  runtime source and version;
- the returned task or process session id identifies that lane;
- `model` equals the role's required model;
- `effort` equals the role's configured effort; and
- for the reviewer, the requested sandbox is `workspace-write`.

For Hypernova, require primary evidence to show supported Sol, Luna, or Astra at its observed
effort and every child to show the selected exact route: `gpt-6-sol` Max by default
or `gpt-6-astra` at configured Astra effort. Require built-in `worker` for implementation
and a fresh built-in `default` for review. Any conflicting custom profile is a mismatch.
Interrupt mismatched lanes when possible and discard their output.

Use trustworthy launch or startup metadata when it exposes all fields. If it omits a field, resolve
the bundled `../../scripts/inspect-agent-runtime.sh` relative to this skill. When spawn
returns a lowercase UUID, pass it with `--thread-id`. When it returns a canonical task
path, pass that value with `--agent-path` and the recorded time with `--since-epoch`.
For an exact-process lane, pass the Codex startup header's session id with `--thread-id`.
The script emits only allowlisted routing fields; it does not emit prompts, messages,
tool arguments, secrets, or file contents.
Forked rollout snapshots can contain inherited parent records, so the inspector selects
the `session_meta` matching the requested task id and reports the final observed
`turn_context` in that task's snapshot.

If worker runtime evidence is missing, inconsistent, or mismatched, interrupt the lane
when possible, reject its output, and stop that lane and dependent work. Report the
requested route, observed evidence, and corrective action. For reviewer evidence, apply
[Review availability and route failure](modes-and-risk.md#review-availability-and-route-failure).
Never infer a route from writing style or self-description, or invoke the legacy process
route after a current v2 failure to bypass a profile conflict.

## Parallel and serial work

Orbit, Event Horizon, Pulsar, Morph, and Constellation are multi-agent modes. Model the
work as a small dependency graph. Create a card only when its independent work justifies
context transfer and integration; do not split tiny work to fill slots. Keep a ready queue
of useful cards whose prerequisites are complete. Give each mutable browser session one
owner, and delegate other checks only when they do not compete for that session. Launch every ready independent card concurrently up to observed host capacity.
This parallel rule applies without requiring Constellation; Constellation adds explicit
capacity-aware model selection for larger fan-out.

Hierarchical delegation is allowed when it is faster than routing every leaf through the primary.
A packet that authorizes downstream delegation must name the child boundary, exact model
and effort, checks, maximum scope, and non-overlapping ownership. The parent worker owns
integration and evidence for its subtree and may spawn bounded child workers only while
capacity remains. Use the shallowest useful hierarchy, and never create a coordination-only
parent or assign the same file/system to two live lanes. Child lanes inherit the same
rules and may delegate again only when their own packet explicitly authorizes it.

Comet (Quick) and Singularity never spawn workers. Reviewers and planning probes do not
create implementation children; hierarchy is for bounded implementation only.

Hypernova uses no hierarchy. Its selected workers cannot delegate. For each wave, set
the worker count to `min(ready independent cards, observed available slots - 1 primary)`,
launch every worker in that wave concurrently, then inspect, integrate, and recalculate
readiness and observed capacity. Never invent work to fill a slot. A real dependency,
confirmation gate, or ownership conflict keeps a card out of the ready set. If capacity
cannot be observed, block Hypernova instead of using a serial fallback.

Serial execution is required only when:

- two cards touch the same file;
- one card consumes another card's output;
- an interface must be settled before implementation;
- a user confirmation gates later work;
- verification of one card determines whether the next should run; or
- observed capacity cannot fit another ready card.

Tell each worker it is not alone and must preserve concurrent edits. The primary or the owning
parent inspects every returned change before another dependent lane builds on it.

## Efficient review and repair

Review the complete integrated change set once unless concrete risk requires earlier
review. Apply the common review availability rule in modes-and-risk.md.

Follow YAGNI. Event Horizon uses one exact Sol reviewer in workspace-write with no special
isolation. Give it only the outcome, boundaries, actual change set, and smallest relevant
checks. Do not snapshot the workspace, compute fingerprints, ask for sandbox
authorization, or turn review into a second documentation project.

The reviewer may fix a small, obvious issue directly and run the smallest affected check.
It returns one verdict line—`ship`, `fix-first`, or `rethink`—plus at most three findings.
Do not launch a second reviewer for a bounded direct repair: the primary inspects the actual fix
and reruns the affected check. A change that needs architecture, scope, or safety judgment
returns to the primary as `rethink` instead of expanding the reviewer task.

High-risk Pulsar, Morph, and Constellation work inherits the same concise Event Horizon
confirmation and review-and-repair rule. Sandbox mode is operational context, not an
acceptance gate; report it only when it affected execution or remains uncertain.

Hypernova always requires one fresh built-in selected-route reviewer after integrated
verification, including when high-risk cards inherit Event Horizon confirmation gates.
If the exact reviewer route cannot be proven, block completion; do not self-review or
substitute the Sol High custom profile.
