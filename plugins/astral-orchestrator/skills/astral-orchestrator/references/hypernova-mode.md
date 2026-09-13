# Hypernova mode

Hypernova is an **explicit opt-in**, Codex-native performance mode. It is the
**opposite of Singularity**: Singularity minimizes coordination and token use in one primary
session, while Hypernova favors **speed and throughput over token efficiency** by using
the maximum safely available concurrency. Never auto-select Hypernova.

The current Sol or Astra primary uses its observed session effort. Every implementation
lane and the mandatory fresh reviewer default to `gpt-5.6-sol` at **Ultra**. The user may
select `gpt-6-astra` at the configured `astra` effort for workers and/or fresh review.
A lower-effort primary can therefore launch a higher-effort Astra worker. Record each selected
child route before launch; primary effort never caps child effort. No silent downgrade
or substitution is allowed after route selection. Hypernova is not permission to widen
the request, skip checks, or weaken confirmation boundaries.

## Blocking preflight

Run `python3 check-primary.py` with no Ultra flag. It accepts the supported model and
effort observed in the running Sol or Astra session, independently of saved defaults. Hypernova
requires an **observed** primary match. `unavailable`, `mismatch`, or `invalid` evidence
blocks the mode; user confirmation cannot replace runtime evidence.

Inspect `collaboration.spawn_agent` and require all five native MultiAgentsV2 controls:

- `agent_type`;
- `task_name`;
- `model`;
- `reasoning_effort`; and
- `fork_turns`.

Also require observed host-advertised capacity with at least one safely usable child
slot after the primary consumes one slot. Hypernova has **no legacy exact-process
fallback**, no nested process route, no portable route, no serial fallback for missing
capacity, no self-review fallback, and no model or effort fallback. It has **no silent
downgrade**. If the native controls or capacity cannot be observed, stop.

## Exact native route

Use the built-in native `worker` for every implementation lane. Do not use a custom
worker profile. The default implementation spawn is below. For a selected Astra route,
set `model: "gpt-6-astra"` and `reasoning_effort` to the configured `astra` value. Verify that
the host advertises the selected route before launch. Every implementation spawn must use
the same native controls:

```text
collaboration.spawn_agent({
  agent_type: "worker",
  task_name: "<unique_lowercase_task_name>",
  model: "gpt-5.6-sol",
  reasoning_effort: "ultra",
  fork_turns: "none",
  message: "<complete standalone Hypernova implementation packet>"
})
```

Each task name is a distinct **unique lowercase** name. Each packet states exact ownership, boundaries,
done conditions, checks, and that downstream delegation is not allowed. Hypernova
workers cannot delegate or spawn children.

Requested values are not observed evidence. Inspect launch/runtime evidence for the
exact built-in agent type, task name, model, effort, and fork setting before accepting a
lane. Interrupt a mismatched lane when possible, discard its output, and block that card;
never salvage it through another route.

## Maximum safe waves

Create the smallest dependency graph that represents the user's actual request. A card
is ready only when its prerequisites, interface decisions, and applicable confirmation
gates are complete, and its file and system ownership does not overlap another live card.
Do not invent work, duplicate a card, or split coherent work artificially to occupy a
slot.

For every wave, calculate:

```text
worker count = min(ready independent cards, observed available slots - 1 primary)
```

Launch that entire safe wave concurrently. Inspect and integrate returned work, then
recalculate readiness and currently available capacity before the next wave. A real
dependency or safety gate can make a later wave smaller; that is safe scheduling inside
Hypernova, not permission to switch to a serial fallback. If missing capacity is the
reason concurrency cannot be proven, Hypernova blocks.

The primary retains requirements, architecture, decomposition, cross-lane integration,
and acceptance. It does not become an implementation fallback merely because a card is
blocked or capacity changes.

## Mandatory fresh Sol Ultra review

After all accepted worker output is integrated and the focused checks pass, launch one
fresh built-in native `default` reviewer. The default is Sol Ultra; an explicitly
selected Astra reviewer uses `gpt-6-astra` and the configured `astra` effort in the same packet:

```text
collaboration.spawn_agent({
  agent_type: "default",
  task_name: "<unique_lowercase_reviewer_task_name>",
  model: "gpt-5.6-sol",
  reasoning_effort: "ultra",
  fork_turns: "none",
  message: "<complete standalone Hypernova review packet>"
})
```

The reviewer task name must be distinct from every worker task name. The existing Sol
High `astral_orchestrator_sol_reviewer` custom profile is ineligible: custom profile
values take precedence and would violate the Ultra contract. The reviewer works directly
and does not delegate. Require matching runtime evidence before accepting its verdict.
Missing or mismatched reviewer evidence blocks completion; primary-session self-review
cannot substitute for the mandatory fresh reviewer.

## Risk and authorization

High-risk or consequential cards inherit **Event Horizon safeguards**. Obtain the same
specific confirmation immediately before destructive, irreversible, credential-related,
external publishing, or production actions unless the exact action was already clearly
authorized. Keep a gated or safety-dependent card out of the ready set and serialize only
the dependency required for safety; never reinterpret that as a lower-assurance route.

“Go nuts,” “maximum speed,” or similar language asks Hypernova to use every safe native
slot. It **does not bypass safety**, scope, ownership, user confirmation, external-action
authorization, focused verification, exact runtime evidence, or the fresh review.

## Handoff

Report the observed primary model and effort and each accepted worker/reviewer model and
effort separately. Do not label the primary Ultra unless runtime evidence says Ultra.
State the wave sizes and capacity evidence, checks run, review verdict, and
any blocked or discarded lane. Never describe a requested route, mismatched output, or a
fallback as successful Hypernova execution.
