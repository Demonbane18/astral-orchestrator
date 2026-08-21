# Routing and preflight

Use this reference for every Codex run that needs primary-route proof. The purpose is to prove
that work used the intended lanes, not merely to request them. Morph and Constellation add worker
rules only when the user explicitly selects those modes; they do not alter this primary,
fixed-route, or reviewer contract.

## Exact route contract

| Role | Native v2 agent type | Required model | Default effort | Best work |
|---|---|---|---|---|
| Orchestrator | Primary session | `gpt-5.6-sol` | `high` | Requirements, architecture, decomposition, cross-lane integration, acceptance |
| Focused worker | Built-in `worker`, or matching `astral_orchestrator_luna_implementer` | `gpt-5.6-luna` | `max` | Narrow, repeatable, fully specified, mechanical, or high-volume execution |
| Context worker | Built-in `worker`, or matching `astral_orchestrator_terra_implementer` | `gpt-5.6-terra` | `high` | Context-heavy implementation, debugging, component/external integration, and moderate refactoring |
| Reviewer | Built-in `default`, or matching `astral_orchestrator_sol_reviewer` | `gpt-5.6-sol` | `high` | Fresh final review; requests a read-only sandbox when the matching profile is used |

The main session owns lane selection and remains accountable for the combined result.
Do not silently substitute a model, effort, or differently configured custom role. On a
current v2 host, deliberately using the built-in native worker for Luna or Terra, or the
built-in native default for a reviewer, with the exact requested model and effort is the
standard route, not a substitution.

The effective values come from
`${CODEX_HOME:-~/.codex}/astral-orchestrator/effort-levels.toml`. When the file is absent,
use the defaults in the table. Supported setting names are `minimal`, `low`, `medium`,
`high`, `xhigh`, `max`, and `ultra`; the last two are model- and account-dependent.
Never silently downgrade a value that Codex rejects.

## Live Astral status updates

Codex plugins cannot pin a permanent native UI widget. Keep the user informed through a
compact **Astral status** panel in substantive progress commentary. Use the reusable
panel in `work-templates.md` for the Sol primary, each selected worker, and the fresh
reviewer when review is required. For Singularity, use only the Sol primary row and do
not repeat unchanged updates. For Comet work, say that workers are not needed; for
any reviewer that is not yet required, say so instead of implying it is running.

Publish the panel at these points:

- preflight, after recording the requested route and available primary evidence;
- launch, after a native spawn or exact-process request is made;
- evidence, when a task/session id, runtime metadata, sandbox result, command result, or
  reviewer verdict is received;
- state changes, including when a lane is blocked, fails, returns, or verification
  completes;
- completion and failure, as part of the handoff or blocked report; and
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
   `../../scripts/check-primary.py` and run it before the non-Singularity one-time
   confirmation fallback.
   Its optional `--thread-id` defaults to `CODEX_THREAD_ID`; use `--sessions-dir` only for
   local test evidence. It invokes the bundled runtime inspector rather than reading
   rollout content itself, emits allowlisted JSON, and exits zero only when the observed
   primary model is `gpt-5.6-sol` and its effort equals the configured orchestrator effort.
   When its status is `unavailable`, a non-Singularity mode may obtain one explicit user
   confirmation and label it user-supplied rather than observed. Singularity requires an
   observed/verified Sol model and effort, so it must stop on unavailable; user
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
   Otherwise choose the built-in native worker for Luna or Terra, or built-in native
   default for a reviewer, with explicit fields.
8. Use the bundled launcher only as the legacy exact-process fallback when the host lacks
   one or more required v2 controls—`agent_type`, `task_name`, `model`,
   `reasoning_effort`, or `fork_turns`—and compatibility requires it. Require a successful
   dry run for the needed role, workdir, and private packet before launch.

For non-Singularity modes, stop before implementation if the primary route is neither
observable nor explicitly user-confirmed, the selected native v2 route cannot be proven,
or the needed legacy launcher dry run fails. Singularity requires an observed/verified
Sol model and effort: it stops on unavailable evidence, and user confirmation cannot
satisfy or override that requirement. Explain the missing item and the smallest corrective
action. A current v2 host never falls through to a process merely because optional
profiles are missing or customized. Optional setup restores fixed-role ergonomics; it is
never evidence for a different model or effort. Do not fall back to another route.

Comet mode intentionally uses only the verified Sol primary session at the configured
orchestrator effort and does not need custom worker availability.

Singularity intentionally uses only one verified Sol primary at the configured
orchestrator effort. It is explicit opt-in, larger than Comet, and does not inspect
`spawn_agent`, launch child lanes, run planning probes, or request a fresh reviewer.
Read `singularity-mode.md` after opt-in. If a higher-priority instruction requires
delegation, report Singularity unavailable; high-risk work uses Event Horizon instead.

Pulsar uses this same exact route contract and preflight. Its frozen-card state,
resumption question, behavioral planning probes, deterministic selection rules, and
ledger are defined in `pulsar-mode.md`; those details never alter the configured model
or effort for a lane.

Morph and Constellation use this same exact Sol primary preflight. Read `morph-mode.md` or
`constellation-mode.md` only after the user explicitly opts in. Morph workers use
`run-morph-agent.py` rather than changing the fixed Luna/Terra contracts. Constellation may use
the normal fixed worker routes or explicit Morph cards, but never changes the Sol primary
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

Keep the decision in the Sol primary session at the configured orchestrator effort when
requirements, architecture, safety boundaries, public interfaces, or acceptance criteria
are unsettled. Sol may settle the decision, then issue bounded execution to Luna or Terra.
For Pulsar, Sol also retains decomposition, integration, and final route selection; use
its stricter deterministic selection rules rather than a general heuristic.

## Choose the execution mechanism

On a current MultiAgentsV2 host, prefer native spawning. For standard Luna and Terra
delegation, use the built-in native worker and explicitly pin every child:

```text
collaboration.spawn_agent({
  agent_type: "worker",
  task_name: "<unique_lowercase_task_name>",
  model: "gpt-5.6-luna" or "gpt-5.6-terra",
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

The packet must name the intended Astral role, model, effort, ownership, boundaries, and
checks, and forbid downstream delegation. `agent_type: "worker"` is intentional for
Luna and Terra implementation, while `agent_type: "default"` is intentional for a
reviewer without its matching custom profile. The explicit model and reasoning effort
preserve Astral's configured route. Do not treat a task name as an agent type.

Custom agent file values take precedence over explicit spawn values. Use an Astral custom
agent type only if its installed profile is byte-exact and its fixed model and effort
match the effective lane settings. It may then supply a fixed capability such as the
reviewer profile's read-only request. A custom profile that conflicts with a requested
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
or read-only for the reviewer. Before either a dry run or launch, it checks a small set of
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
session id, final response, and exit status. Both mechanisms forbid downstream delegation.

After launch, collect runtime evidence showing:

- the native v2 spawn used its recorded built-in or matching custom `agent_type`, unique
  `task_name`, exact `model`, configured `reasoning_effort`, and `fork_turns: "none"`; or
  the launcher header names the exact legacy role;
- an exact-process launcher reports a passing Codex configuration probe and the selected
  runtime source and version;
- the returned task or process session id identifies that lane;
- `model` equals the role's required model;
- `effort` equals the role's configured effort;
- for the reviewer, the sandbox policy is `read-only` when Event Horizon mode requires hard
  isolation.

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

Parallel execution is allowed only when worker cards have independent outcomes and
non-overlapping file or system ownership. Tell each worker it is not alone and must
preserve concurrent edits.

Use serial execution when:

- two cards touch the same file;
- one card consumes another card's output;
- an interface must be settled before implementation;
- a user confirmation gates later work;
- verification of one card determines whether the next should run.

The orchestrator inspects every returned change before another lane builds on it.

## Review isolation

The matching reviewer profile requests a read-only sandbox, and the legacy exact-process
launcher passes that mode explicitly. A built-in v2 reviewer receives the same complete
behaviorally read-only review packet, but the host still controls the effective sandbox.
Record the observed sandbox and never overstate isolation. In Event Horizon mode, require the
exact pinned Sol `model`, configured reviewer `reasoning_effort`, a distinct unique reviewer
`task_name`, `fork_turns: "none"`, and observed read-only access; requested read-only access
alone is insufficient. Do not weaken this safeguard when a custom
profile is unavailable or when the built-in native default is used. Observed non-read-only
access, or absent sandbox evidence, makes review incomplete. After any fix, create a new
native reviewer with explicit `agent_type`, its own distinct unique `task_name`, exact
`model`, configured `reasoning_effort`, and `fork_turns: "none"`, or a new reviewer
process; never reuse the previous review context.
