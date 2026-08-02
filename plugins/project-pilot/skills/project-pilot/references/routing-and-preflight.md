# Routing and preflight

Use this reference for every Guided or Careful run. The purpose is to prove that work
used the intended lanes, not merely to request them.

## Exact route contract

| Role | Agent type | Required model | Effort | Best work |
|---|---|---|---|---|
| Orchestrator | Primary session | `gpt-5.6-sol` | `high` | Requirements, architecture, decomposition, cross-lane integration, acceptance |
| Focused worker | `project_pilot_luna_implementer` | `gpt-5.6-luna` | `xhigh` | Narrow, repeatable, fully specified, mechanical, or high-volume execution |
| Context worker | `project_pilot_terra_implementer` | `gpt-5.6-terra` | `xhigh` | Context-heavy implementation, debugging, component/external integration, and moderate refactoring |
| Reviewer | `project_pilot_sol_reviewer` | `gpt-5.6-sol` | `high` | Fresh final review; requests a read-only sandbox |

Do not silently substitute a built-in agent, a different custom role, model, or effort.
The main session owns lane selection and remains accountable for the combined result.

## Primary-session preflight

Before execution in any mode:

1. Confirm observable runtime evidence identifies the primary model as `gpt-5.6-sol`
   and reasoning as `high`. If the host exposes no primary metadata, obtain one explicit
   user confirmation and label it user-supplied rather than observed.
2. Read applicable workspace instructions and inspect the current change state.
3. Define the work card and identify whether worker cards can have non-overlapping
   ownership.
4. Identify user confirmations required before consequential actions.

Before Guided or Careful execution, additionally:

5. Resolve `../../scripts/install-agents.sh` relative to this skill and run it with
   `--check` so the installed profiles byte-match the shipped profiles.
6. Confirm the collaboration tool exposes all three exact Project Pilot agent types.

If the primary route is neither observable nor explicitly user-confirmed, or if step 5
or 6 fails, stop before implementation. Explain the missing item and the smallest
corrective action: run `sh scripts/setup.sh --refresh` from the Project Pilot repository
when profiles are missing or different, then start a new task with Sol High and High
reasoning. Do not fall back to another route.

Quick mode intentionally uses only the verified Sol High primary session and does not
need custom worker availability.

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

Keep the decision in Sol High when requirements, architecture, safety boundaries,
public interfaces, or acceptance criteria are unsettled. Sol may settle the decision,
then issue bounded execution to Luna or Terra.

## Spawn and runtime evidence

Immediately before spawning, record the current epoch seconds. Choose a unique lowercase
task name. Spawn the exact `agent_type` with `fork_turns: "none"`; do not rely on
inherited history or prose asking a general worker to act like the lane. Give the agent
a complete, standalone implementation or review packet. Instruct it to perform the
assignment directly and never spawn or delegate to another agent.

After launch, collect runtime evidence showing:

- the spawn request used the exact custom `agent_type` and returned task id;
- `agent_path` identifies that spawned task rather than a different task;
- `model` equals the role's required model;
- `effort` equals the role's required effort;
- for the reviewer, the sandbox policy is `read-only` when Careful mode requires hard
  isolation.

Use trustworthy launch metadata when it exposes all fields. If it omits a field, resolve
the bundled `../../scripts/inspect-agent-runtime.sh` relative to this skill. When spawn
returns a lowercase UUID, pass it with `--thread-id`. When it returns a canonical task
path, pass that value with `--agent-path` and the recorded time with `--since-epoch`.
The script emits only allowlisted routing fields; it does not emit prompts, messages,
tool arguments, secrets, or file contents.
Forked rollout snapshots can contain inherited parent records, so the inspector selects
the `session_meta` matching the requested task id and reports the final observed
`turn_context` in that task's snapshot.

If runtime evidence is missing, inconsistent, or mismatched, interrupt the lane when
possible, discard its output, and stop. Report the requested route, observed evidence,
and corrective action. Never infer a successful route from the agent's writing style or
self-description.

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

The reviewer profile requests a read-only sandbox, but the host controls the effective
sandbox. In Guided mode, record the observed sandbox and never overstate isolation. In
Careful mode, observed non-read-only access makes the required independent review
incomplete; stop before a `ship` claim. After any fix, spawn a new reviewer with
`fork_turns: "none"`; never reuse or follow up with the previous reviewer.
