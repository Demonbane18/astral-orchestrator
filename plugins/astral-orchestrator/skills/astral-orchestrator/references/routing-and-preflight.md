# Routing and preflight

Use this reference for every Guided, Careful, or Measured run. The purpose is to prove that work
used the intended lanes, not merely to request them.

## Exact route contract

| Role | Agent type | Required model | Default effort | Best work |
|---|---|---|---|---|
| Orchestrator | Primary session | `gpt-5.6-sol` | `high` | Requirements, architecture, decomposition, cross-lane integration, acceptance |
| Focused worker | `astral_orchestrator_luna_implementer` | `gpt-5.6-luna` | `xhigh` | Narrow, repeatable, fully specified, mechanical, or high-volume execution |
| Context worker | `astral_orchestrator_terra_implementer` | `gpt-5.6-terra` | `xhigh` | Context-heavy implementation, debugging, component/external integration, and moderate refactoring |
| Reviewer | `astral_orchestrator_sol_reviewer` | `gpt-5.6-sol` | `high` | Fresh final review; requests a read-only sandbox |

Do not silently substitute a built-in agent, a different custom role, model, or effort.
The main session owns lane selection and remains accountable for the combined result.

The effective values come from
`${CODEX_HOME:-~/.codex}/astral-orchestrator/effort-levels.toml`. When the file is absent,
use the defaults in the table. Supported setting names are `minimal`, `low`, `medium`,
`high`, `xhigh`, `max`, and `ultra`; the last two are model- and account-dependent.
Never silently downgrade a value that Codex rejects.

## Primary-session preflight

Before execution in any mode:

1. Resolve `../../scripts/configure-effort.py` relative to this skill and run
   `python3 configure-effort.py --show --json`. Confirm the configured orchestrator effort
   matches observable runtime evidence for the `gpt-5.6-sol` primary model. If the host
   exposes no primary metadata, obtain one explicit
   user confirmation and label it user-supplied rather than observed.
2. Read applicable workspace instructions and inspect the current change state.
3. Define the work card and identify whether worker cards can have non-overlapping
   ownership.
4. Identify user confirmations required before consequential actions.

Before Guided, Careful, or Measured execution, additionally:

5. Resolve `../../scripts/install-agents.sh` relative to this skill and run it with
   `--check`. A pass records `native profiles: exact`; a missing or different profile
   records `native profiles: unavailable` and is not a preflight failure.
6. Use native selection only when step 5 passed, the collaboration tool exposes the
   exact custom `agent_type`, and the native profile effort equals the configured value.
   Otherwise, resolve `../../scripts/run-agent.py` and require a successful dry-run for
   the needed role, workdir, and private packet.

If the primary route is neither observable nor explicitly user-confirmed, or if both the
native route and bundled launcher dry-run fail, stop before implementation. Explain the
missing item and the smallest corrective action. Missing or different native profiles
force the exact-process route; they do not permit substitution and do not require setup.
Optional setup can restore native named-agent ergonomics, but it is never evidence for a
different model or effort. Do not fall back to another route.

Quick mode intentionally uses only the verified Sol primary session at the configured
orchestrator effort and does not need custom worker availability.

Measured uses this same exact route contract and preflight. Its frozen-card state,
resumption question, behavioral planning probes, deterministic selection rules, and
ledger are defined in `measured-mode.md`; those details never alter the configured model
or effort for a lane.

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
For Measured, Sol also retains decomposition, integration, and final route selection; use
its stricter deterministic selection rules rather than a general heuristic.

## Choose the execution mechanism

Prefer a native custom agent only when the installed native profile check passed, the
collaboration tool exposes an explicit `agent_type` field, the exact Astral Orchestrator
role, and its native profile effort matches the configured value. Do not treat a task name
as an agent type; current hosts can otherwise create a default Sol agent under a
Luna-looking name. A custom effort that differs from the native profile always uses the
exact-process mechanism. Missing or different native profiles force the exact-process
route; they do not permit substitution.

When native selection is unavailable, use the **exact-process** mechanism. Resolve
`../../scripts/run-agent.py` relative to this skill, write the complete standalone work
packet to a private temporary regular file, then run:

```text
python3 run-agent.py --role <luna|terra|reviewer> --workdir <workspace> --prompt-file <packet>
```

The launcher reads the shipped profile, reads the effective effort settings, pins the
model and configured effort on `codex exec`, injects the profile's developer
instructions that forbid further delegation, and selects workspace-write for workers
or read-only for the reviewer. Its evidence marks whether the effort is the default and
whether a native profile would be compatible. A successful dry-run proves this bundled
exact-process contract without requiring installed native profiles. Remove only the
exact temporary packet after the process exits. A non-zero exit blocks the lane.

## Spawn and runtime evidence

For a native lane, immediately record the epoch seconds, choose a unique lowercase task
name, and spawn the exact `agent_type` with `fork_turns: "none"`. For an exact-process
lane, launch a new process for every packet and capture its `ASTRAL_ORCHESTRATOR_ROUTE` header,
Codex startup header, session id, final response, and exit status. Both mechanisms use a
complete standalone packet and forbid downstream delegation.

After launch, collect runtime evidence showing:

- the native spawn used the exact custom `agent_type`, or the launcher header names the
  exact role;
- the returned task or process session id identifies that lane;
- `model` equals the role's required model;
- `effort` equals the role's configured effort;
- for the reviewer, the sandbox policy is `read-only` when Careful mode requires hard
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

The reviewer profile requests a read-only sandbox, and the exact-process launcher passes
that mode explicitly. The host still controls the effective sandbox. Record the observed
sandbox and never overstate isolation. In Careful mode, require the exact pinned Sol
reviewer and observed read-only access; requested read-only access alone is insufficient.
Observed non-read-only access makes review incomplete. After any fix, create a new native reviewer with
`fork_turns: "none"` or a new reviewer process; never reuse the previous review context.
