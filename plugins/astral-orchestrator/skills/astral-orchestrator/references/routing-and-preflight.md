# Routing and preflight

The current Sol or Astra session is the primary at its observed effort. Child effort is
independent. Native Astra workers use the configured `astra` effort in worker-capable
modes; retain each mode's ownership and review rules.
Hypernova uses the routes in `hypernova-mode.md`, defaulting to Sol Ultra children.

## Exact route contract

| Role | Native v2 agent type | Required model | Default effort | Best work |
|---|---|---|---|---|
| Orchestrator | Primary session | observed `gpt-5.6-sol` or `gpt-6-astra` | observed session effort | Requirements, architecture, decomposition, cross-lane integration, acceptance |
| Deep-reasoning worker | Built-in `worker` | `gpt-6-astra` | `medium` | Bounded work whose reasoning depth, cross-domain synthesis, or difficult diagnosis justifies Astra cost |
| Focused worker | Built-in `worker`, or matching `astral_orchestrator_luna_implementer` | `gpt-5.6-luna` | `max` | Narrow, repeatable, fully specified, mechanical, or high-volume execution |
| Context worker | Built-in `worker`, or matching `astral_orchestrator_terra_implementer` | `gpt-5.6-terra` | `high` | Context-heavy implementation, debugging, component/external integration, and moderate refactoring |
| Reviewer | Built-in `default`, or matching `astral_orchestrator_sol_reviewer` | `gpt-5.6-sol` | `high` | Exact pinned Sol, concise workspace-write review-and-repair |
| Hypernova primary | Primary session | observed `gpt-5.6-sol` or `gpt-6-astra` | observed session effort | Architecture, maximum-safe-wave planning, integration, and acceptance |
| Hypernova implementation | Built-in `worker` only | `gpt-5.6-sol` | `ultra` | Every independently owned ready implementation card |
| Hypernova reviewer | Fresh built-in `default` only | `gpt-5.6-sol` | `ultra` | Mandatory exact-route review after integrated verification |

The main session owns lane selection and remains accountable for the combined result.
Do not silently substitute a model, effort, or differently configured custom role. On a
current v2 host, deliberately using the built-in native worker for Astra, Luna, or Terra, or the
built-in native default for a reviewer, with the exact requested model and effort is the
standard route, not a substitution.

The effective values come from
`${CODEX_HOME:-~/.codex}/astral-orchestrator/effort-levels.toml`. When the file is absent,
use the defaults in the table. Supported setting names are `minimal`, `low`, `medium`,
`high`, `xhigh`, `max`, and `ultra`; the last two are model- and account-dependent.
Never silently downgrade a value that Codex rejects.

## Live Astral status updates

Codex plugins cannot pin a permanent native UI widget. Keep the user informed through a
compact **Astral status** panel at every mandatory checkpoint. Use the reusable panel in
`work-templates.md` for the detected primary, each selected worker, and the fresh reviewer
when review is required. The initial status appears before implementation or delegation,
even when the route is Comet or Singularity. For Singularity, use only the primary row and
do not repeat unchanged updates. For Hypernova, label each row with its own observed model and effort and include the
observed safe wave size without exposing packet contents. For Comet work, say that workers are not needed; for
any reviewer that is not yet required, say so instead of implying it is running.

Publish the panel at these checkpoints; none may be skipped:

- initial preflight, before implementation or delegation, with unavailable evidence
  labeled honestly;
- before every child launch, with the requested route marked `planned` or `requested`;
- immediately after launch returns, with the task or session id and actual launch state;
- evidence, only when it changes whether the route may continue;
- state changes, including when a lane is blocked, fails, returns, or verification
  completes;
- completion or failure, as part of the final handoff or blocked report; and
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

## Primary-session preflight

Before execution in any mode:

1. Resolve `../../scripts/configure-effort.py` relative to this skill and run
   `python3 configure-effort.py --show --json`. Then resolve
   `../../scripts/check-primary.py` and run it before the ordinary one-time confirmation
   fallback. Use the same check in Hypernova. No mode requires an Ultra flag. It does not
   mutate persisted effort settings.
   Its optional `--thread-id` defaults to `CODEX_THREAD_ID`; use `--sessions-dir` only for
   local test evidence. It invokes the bundled runtime inspector rather than reading
   rollout content itself, emits allowlisted JSON, and exits zero only when the observed
   primary model is `gpt-5.6-sol` or `gpt-6-astra` at any supported observed session effort. The optional
   `--require-sol-ultra` and `--require-astra-ultra` flags still request a strict Ultra
   check when explicitly wanted; they are not mode prerequisites. When its status is `unavailable`,
   a mode other than Singularity or Hypernova may obtain one explicit user confirmation
   and label it user-supplied rather than observed. Singularity and Hypernova require an
   observed/verified supported primary model and observed effort, so either must stop on unavailable; user
   confirmation cannot satisfy or override that requirement. When status is `mismatch`,
   stop and correct the route; do not ask a user to waive a mismatch. `invalid` means
   malformed, ambiguous, or rejected local evidence and also blocks the route; manual
   confirmation cannot waive it.
2. Read applicable workspace instructions and inspect the current change state.
3. Define the work card and identify whether worker cards can have non-overlapping
   ownership.
4. Identify user confirmations required before consequential actions.

Before Orbit, Event Horizon, or Pulsar execution, additionally:

5. Inspect the available `collaboration.spawn_agent` contract. A current Codex
   **MultiAgentsV2** host exposes all five required controls together:
   `agent_type`, `task_name`, `model`, `reasoning_effort`, and `fork_turns`.
6. When `agent_type`, `task_name`, `model`, `reasoning_effort`, and `fork_turns` are all
   present, use the standard native route with the complete standalone work packet. Pass
   a unique lowercase task name, the exact model and configured effort on every child,
   and set `fork_turns: "none"`. Missing or mismatched optional custom profiles are route
   evidence, not a native-v2 preflight failure.
7. Optionally run `../../scripts/install-agents.sh --check` to record profile state. A
   matching custom role is usable only when its fixed model and effort equal the effective
   settings, because custom agent file values take precedence over explicit spawn values.
   Otherwise choose the built-in native worker for Astra, Luna, or Terra, or built-in native
   default for a reviewer, with explicit fields.
8. Use the bundled launcher only as the legacy exact-process fallback when the host lacks
   one or more required v2 controls—`agent_type`, `task_name`, `model`,
   `reasoning_effort`, or `fork_turns`—and compatibility requires it. Require a successful
   dry run for the needed role, workdir, and private packet before launch.

Before Hypernova execution, instead require all five native MultiAgentsV2 controls in
step 5, observed host-advertised capacity, and at least one safely usable child slot after
the primary consumes one slot. Use only the built-in `worker` and built-in `default`
routes with exact selected child values (Sol Ultra by default or Astra at configured
`astra` effort). Custom profiles are ineligible. Missing controls or
capacity block Hypernova; do not run setup, a launcher dry run, or another fallback.

For modes other than Singularity and Hypernova, stop before implementation if the primary route is neither
observable nor explicitly user-confirmed, the selected native v2 route cannot be proven,
or the needed legacy launcher dry run fails. Singularity requires an observed/verified
supported primary model and effort: it stops on unavailable evidence, and user confirmation cannot
satisfy or override that requirement. Explain the missing item and the smallest corrective
action. A current v2 host never falls through to a process merely because optional
profiles are missing or customized. Optional setup restores fixed-role ergonomics; it is
never evidence for a different model or effort. Do not fall back to another route.

Hypernova stops on unavailable, mismatch, or invalid primary evidence; unavailable
native controls or capacity; any worker mismatch; or unavailable/mismatched fresh-review
evidence. It has no user-confirmed, legacy exact-process, process, portable, serial,
self-review, model, or effort fallback. Discard output from a mismatched lane.

Comet mode intentionally uses only the verified primary session at its observed effort
and does not need custom worker availability.

Singularity intentionally uses only one verified primary at its observed effort. It is
explicit opt-in, larger than Comet, and does not inspect
`spawn_agent`, launch child lanes, run planning probes, or request a fresh reviewer.
Read `singularity-mode.md` after opt-in. If a higher-priority instruction requires
delegation, report Singularity unavailable; high-risk work uses Event Horizon instead.

Hypernova intentionally uses an observed Sol or Astra primary at its current effort,
built-in Sol Ultra workers by default, and a mandatory fresh reviewer. Read
`hypernova-mode.md` after explicit opt-in. The primary effort never caps child effort.
Selected Astra children use the configured `astra` effort and the same native controls.

Pulsar uses this same exact route contract and preflight. Its frozen-card state,
resumption question, behavioral planning probes, deterministic selection rules, and
ledger are defined in `pulsar-mode.md`; those details never alter the configured model
or effort for a lane.

Morph and Constellation use this same detected-primary preflight. Read `morph-mode.md` or
`constellation-mode.md` only after the user explicitly opts in. Morph workers use
`run-morph-agent.py` rather than changing the fixed Luna/Terra contracts. Constellation may use
the normal fixed worker routes or explicit Morph cards, but never changes the detected primary
or fresh Sol reviewer.

## Lane decision

Choose Luna when all of these are true:

- the output and acceptance conditions are explicit;
- the implementation is repeatable or mostly mechanical;
- the owned files are narrow and independent;
- little architectural or product judgment remains.

Choose Terra when architecture and acceptance are settled but one or more of these are
true:

- implementation depends on wider repository context;
- debugging requires tracing behavior across components;
- interfaces, integrations, or moderate refactors require careful judgment;
- the change has a wider but still bounded regression surface.

Choose Astra only for a bounded card whose reasoning depth, cross-domain synthesis, or
difficult diagnosis is unlikely to be handled efficiently enough by Luna or Terra. Use
the configured `astra` effort, state why Astra is worth the added cost, and do not choose
it merely because it is available.

Keep the decision in the detected primary session at its observed effort when
requirements, architecture, safety boundaries, public interfaces, or acceptance criteria
are unsettled. The primary may settle the decision, then issue bounded execution to Astra,
Luna, or Terra. For Pulsar, the primary also retains decomposition, integration, and final route selection; use
its stricter deterministic selection rules rather than a general heuristic.

## Choose the execution mechanism

On a current MultiAgentsV2 host, prefer native spawning. For standard Astra, Luna, and Terra
delegation, use the built-in native worker and explicitly pin every child:

```text
collaboration.spawn_agent({
  agent_type: "worker",
  task_name: "<unique_lowercase_task_name>",
  model: "gpt-6-astra", "gpt-5.6-luna", or "gpt-5.6-terra",
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
  model: "gpt-5.6-sol",
  reasoning_effort: "<configured reviewer effort>",
  fork_turns: "none",
  message: "<complete standalone Astral review packet>"
})
```

Hypernova uses Sol Ultra children by default; selected Astra children replace the model
and effort below with `gpt-6-astra` and the configured `astra` effort. Primary effort
remains independent. Every implementation spawn is
a built-in native worker with a distinct unique lowercase task name:

```text
collaboration.spawn_agent({
  agent_type: "worker",
  task_name: "<unique_lowercase_hypernova_task_name>",
  model: "gpt-5.6-sol",
  reasoning_effort: "ultra",
  fork_turns: "none",
  message: "<complete standalone Hypernova implementation packet; delegation forbidden>"
})
```

Its mandatory fresh reviewer is a built-in native default with a separate task name:

```text
collaboration.spawn_agent({
  agent_type: "default",
  task_name: "<unique_lowercase_hypernova_reviewer_task_name>",
  model: "gpt-5.6-sol",
  reasoning_effort: "ultra",
  fork_turns: "none",
  message: "<complete standalone Hypernova review packet; delegation forbidden>"
})
```

Do not use the Sol High custom reviewer or any custom worker for Hypernova. Custom file
values take precedence and make those profiles ineligible for the exact Ultra route.

The packet must name the intended Astral role, model, effort, ownership, boundaries,
checks, and whether downstream delegation is allowed. `agent_type: "worker"` is intentional for
Luna and Terra implementation, while `agent_type: "default"` is intentional for a
reviewer without its matching custom profile. The explicit model and reasoning effort
preserve Astral's configured route. Do not treat a task name as an agent type.

Custom agent file values take precedence over explicit spawn values. Use an Astral custom
agent type only if its installed profile is byte-exact and its fixed model and effort
match the effective lane settings. It may then supply a fixed capability such as concise
bounded review-and-repair. A custom profile that conflicts with a requested
setting is not a reason to launch a nested process on a v2 host: use the appropriate
built-in native agent with the explicit values instead (`worker` for Luna or Terra,
`default` for reviewer). A custom effort remains a per-lane setting, not a reason to use
a conflicting profile. If that native spawn cannot provide the requested model or effort,
block the lane; do not silently substitute.

Use the **legacy exact-process fallback** only when the collaboration tool lacks one or
more required v2 controls—`agent_type`, `task_name`, `model`, `reasoning_effort`, or
`fork_turns`—and a compatible legacy route is needed. Resolve `../../scripts/run-agent.py`,
write the complete standalone work packet to a private temporary regular file, then run:

```text
python3 run-agent.py --role <luna|terra|reviewer> --workdir <workspace> --prompt-file <packet>
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
(Luna/Terra), built-in default (reviewer), or a matching custom role; in every case the
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

For Hypernova, require primary evidence to show supported Sol or Astra at its observed
session effort. Each child must match its selected model and effort (Sol Ultra by default
or Astra at configured `astra` effort); require built-in `worker` for
implementation and a fresh built-in `default` for review. The normal Sol High custom
reviewer is a mismatch. Interrupt mismatched lanes when possible and discard their output.

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

If runtime evidence is missing, inconsistent, or mismatched, interrupt the lane when
possible, discard its output, and stop. Report the requested route, observed evidence,
and corrective action. Never infer a successful route from the agent's writing style or
self-description. Do not invoke the legacy process route after a current v2 failure just
to work around a missing or conflicting optional custom profile.

## Parallel and serial work

Orbit, Event Horizon, Pulsar, Morph, and Constellation are multi-agent modes. Model the
work as a small dependency graph and keep a ready queue of cards whose prerequisites are
complete. Launch every ready independent card concurrently up to observed host capacity.
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

Hypernova uses no hierarchy. Its Sol Ultra workers cannot delegate. For each wave, set
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

Follow YAGNI. Event Horizon uses one exact Sol reviewer in workspace-write with no special
isolation. Give it only the outcome, boundaries, actual change set, and smallest relevant
checks. Do not snapshot the workspace, compute fingerprints, ask for sandbox
authorization, or turn review into a second documentation project.

The reviewer may fix a small, obvious issue directly and run the smallest affected check.
It returns one verdict line—`ship`, `fix-first`, or `rethink`—plus at most three findings.
Do not launch a second reviewer for a bounded direct repair: Sol inspects the actual fix
and reruns the affected check. A change that needs architecture, scope, or safety judgment
returns to Sol as `rethink` instead of expanding the reviewer task.

High-risk Pulsar, Morph, and Constellation work inherits the same concise Event Horizon
confirmation and review-and-repair rule. Sandbox mode is operational context, not an
acceptance gate; report it only when it affected execution or remains uncertain.

Hypernova always requires one fresh built-in reviewer on its selected route after integrated
verification, including when high-risk cards inherit Event Horizon confirmation gates.
If the exact reviewer route cannot be proven, block completion; do not self-review or
substitute the Sol High custom profile.
