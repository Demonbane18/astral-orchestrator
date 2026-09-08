# Astral Orchestrator work templates

Load only the template needed for the next action. Replace every angle-bracketed field.
Follow YAGNI: keep plans in context, use the smallest relevant checks, and do not create
documents or evidence packets that are not required deliverables. Event Horizon review
uses workspace-write so a reviewer can repair a bounded issue without another prompt.
Orbit, Event Horizon, Pulsar, Morph, and Constellation may run independent cards in
parallel or use bounded hierarchical delegation. Comet (Quick) and Singularity never
spawn workers. Hypernova uses maximum safely available native waves on the selected child routes and never
allows its workers or reviewer to delegate.

## Astral status panel

Use this compact panel only when the route or phase changes while Astral is active. It
is progress commentary, not a permanent native UI widget. Keep one row for the Astra
primary, one for each selected worker, and one for the fresh reviewer when required.
Use `not needed` when a lane will not be used, and use `planned` for a required reviewer
that is waiting to launch. Write `not yet required` only in the evidence field as an
explanation, never as a state. Requested facts are the intended route; observed facts
require runtime evidence. Do not call a requested lane `running` or observed without
that evidence. Always emit the panel as an actual GitHub-flavored Markdown table with
the header separator row below: never fence it and never use plain pipe text.

| Lane | Role | Model | Effort | State | Evidence |
|---|---|---|---|---|---|
| Astra primary | requested: primary session; observed: <primary runtime or not yet available> | requested: gpt-6-astra; observed: <value or not yet available> | requested: <configured effort>; observed: <value or not yet available> | <planned/requested/launched/running/returned/verified/blocked/failed/not needed> | <primary checker, user-confirmed fallback, or runtime evidence> |
| Worker <card> | requested: worker, matching astral_orchestrator_luna_implementer profile, matching astral_orchestrator_terra_implementer profile, or Morph worker; observed: <agent type or Morph route / not yet available> | requested: <model>; observed: <value or not yet available> | requested: <configured effort>; observed: <value or not yet available> | <planned/requested/launched/running/returned/verified/blocked/failed/not needed> | <task or session id and matching runtime evidence> |
| Fresh reviewer | requested: default or matching astral_orchestrator_sol_reviewer profile; observed: <agent type or not yet available> | requested: gpt-5.6-sol; observed: <value or not yet available> | requested: <configured effort>; observed: <value or not yet available> | <planned/requested/launched/running/returned/verified/blocked/failed/not needed> | <task or session id, runtime evidence, and sandbox when applicable> |

Use `planned`, `requested`, `launched`, `running`, `returned`, `verified`, `blocked`,
`failed`, or `not needed` only as defined in `routing-and-preflight.md`. Update the
panel at preflight, launch, new evidence, state changes, completion, failure, and at a
restrained interval for long-running work. Do not repeat it merely to create activity.

For Singularity, emit only the Astra primary row from this panel. Do not add worker or
fresh-reviewer placeholders: Singularity has no subagents and no fresh reviewer.

For Hypernova, record the Astra session effort separately and each selected child route
(Sol Ultra by default or explicit Astra Max/Ultra). Name the
built-in `worker` or built-in `default` route, and include observed capacity and the safe
wave calculation in evidence. Do not label requested values as observed. Missing or
mismatched evidence blocks the route and the output is discarded.

## Work card

```text
OUTCOME
<Observable result and why it matters.>

DONE WHEN
- <Specific acceptance condition.>

BOUNDARIES
- In scope: <files, systems, or deliverables.>
- Out of scope: <nearby work that must not expand this request.>
- Safety: <actions requiring user confirmation or prohibited actions.>

CHECKS
- Run: <exact command or inspection>
  Pass means: <concrete evidence>
```

## Singularity work card

```text
OBJECTIVE
<Observable result and why it matters.>

DONE
- <Specific acceptance condition.>

NON-GOALS
- <Related work to park rather than pursue.>

CONSTRAINTS
- <Scope, safety, compatibility, or confirmation boundary.>

CHECKS
- <One proportional verification pass and its pass evidence.>
```

Keep no more than five active steps, with one in progress. Use the smallest sufficient
intervention; stop after DONE first passes unless evidence is ambiguous, contradictory,
or defective. Astra self-reviews once using the actual change set and evidence.

## Hypernova wave card

```text
OUTCOME
<Observable result and why maximum safe native concurrency helps.>

READY INDEPENDENT CARDS
- <Card id>: <exact non-overlapping ownership and done condition>

CAPACITY
- Observed available slots: <count and evidence>
- Primary consumes one slot.
- Worker count: min(<ready independent count>, <available slots> - 1 primary) = <wave size>

ROUTE
- Primary: observed gpt-6-astra, <selected session effort>
- Every implementation lane: built-in worker, Sol Ultra or explicitly selected Astra Max/Ultra
- Fresh reviewer: built-in default, Sol Ultra or explicitly selected Astra Max/Ultra
- Every spawn: distinct unique lowercase task name, fork_turns: "none"
- Downstream delegation: forbidden

BOUNDARIES
- Do not invent work to fill capacity.
- Keep gated, dependent, or overlapping cards out of the ready set.
- High-risk cards inherit Event Horizon confirmation safeguards.

CHECKS
- <Focused checks and concrete pass evidence.>
```

Recalculate readiness and observed capacity after every integrated wave. Missing native
controls, capacity, exact runtime evidence, or the mandatory fresh review blocks
Hypernova; do not use a legacy, process, portable, serial, self-review, model, or effort
fallback.

## Implementation delegation

```text
ROLE
<astral_orchestrator_luna_implementer or astral_orchestrator_terra_implementer>
Implement the bounded work card below. Surface material ambiguity instead of expanding
scope or redesigning settled decisions. The orchestrator selected this lane because:
<one concrete routing reason>

OUTCOME
<Paste the work-card outcome.>

OWNERSHIP
You own only:
- <Exact file set or bounded responsibility.>

You are not alone in the codebase. Preserve concurrent and unrelated edits, do not
revert work you do not own, and adapt to changes already present.

DOWNSTREAM DELEGATION
<Allowed or not allowed. Default to allowed for a coherent independent subtree when the
host has capacity.>
When allowed, you may spawn bounded child workers only with exact model and effort,
standalone packets, non-overlapping ownership, and focused checks. You own integration
and evidence for the subtree. Use the shallowest useful hierarchy; do not create a
coordination-only child or delegate the same card twice. When not allowed or not useful,
perform the assignment directly.

DONE WHEN
- <Acceptance condition.>

INTERFACES
- <Behavior, schema, command, or signature that must remain compatible.>

BOUNDARIES
- <Scope and safety limits.>

CHECKS
- Run: <exact command>
  Pass means: <concrete result>

RETURN
- Status: complete, partial, or blocked
- Route: observed agent path, model, effort, and task id
- Changes: file-by-file summary from the actual change set
- Checks: exact commands and observed results
- Decisions: material judgment calls, or none
- Gaps: unfinished work or remaining uncertainty, or none
```

## Hypernova implementation delegation

```text
ROLE
Built-in native worker, requested <selected model and effort: Sol Ultra by default or explicit Astra Max/Ultra>. Implement the exact bounded card
directly. Do not spawn or delegate to another agent.

SPAWN CONTRACT
- agent_type: "worker"
- task_name: "<unique_lowercase_task_name>"
- model: "gpt-5.6-sol"
- reasoning_effort: "ultra"
- fork_turns: "none"

OUTCOME
<Paste the Hypernova card outcome.>

OWNERSHIP
You own only:
- <Exact non-overlapping file set or bounded responsibility.>

You are not alone in the codebase. Preserve concurrent and unrelated edits, do not
revert work you do not own, and adapt to changes already present.

DOWNSTREAM DELEGATION
Not allowed. Perform the assignment directly.

DONE WHEN
- <Acceptance condition.>

BOUNDARIES
- <Scope, safety, and Event Horizon confirmation limits.>

CHECKS
- Run: <exact command>
  Pass means: <concrete result>

RETURN
- Status, exact files changed, exact checks/results, decisions, and gaps
- Observed route evidence when available; requested values alone are not proof
```

## Concise review and repair

```text
ROLE
Perform one concise review-and-repair pass in workspace-write. Fix a bounded, obvious
issue directly when that is faster than returning it. Do not broaden scope, redesign
architecture, create process documents, stage, commit, or publish. Perform the review
directly; do not spawn or delegate to another agent.

OUTCOME
<The user's requested result.>

DONE WHEN
- <Acceptance condition.>

BOUNDARIES
- <Required compatibility, scope limits, and safety constraints.>

CHANGE SET
<Complete diff or exact base/head revisions plus allowed files.>

CHECKS
- <Smallest relevant check> -> <actual observed evidence>

REVIEW
Inspect the actual files and complete change set. Judge correctness, completeness,
regressions, scope discipline, interface preservation, test adequacy, and material risk.
If you make a small repair, inspect it and run the smallest affected check.

VERDICT
Return exactly one:
- ship — the inspected result and evidence satisfy the outcome;
- fix-first — bounded corrections are required;
- rethink — architecture, scope, or assumptions must change.

REPORT
- One verdict line: ship, fix-first, or rethink
- Findings: at most three concise actionable findings, or none
- Repairs: bounded files changed and focused checks run, or none
```

## Hypernova mandatory fresh review

```text
ROLE
Fresh built-in native default reviewer, requested <selected model and effort: Sol Ultra by default or explicit Astra Max/Ultra>. Review directly;
do not spawn or delegate to another agent. The Sol High custom reviewer is ineligible.

SPAWN CONTRACT
- agent_type: "default"
- task_name: "<unique_lowercase_reviewer_task_name>"
- model: "gpt-5.6-sol"
- reasoning_effort: "ultra"
- fork_turns: "none"

OUTCOME
<The user's requested result.>

BOUNDARIES
- <Required compatibility, scope limits, and safety constraints.>

CHANGE SET AND EVIDENCE
<Complete accepted change set, focused checks, wave sizes, and observed lane routes.>

REVIEW
Inspect correctness, completeness, regressions, ownership, checks, safety gates, and the
exact Hypernova route. Reject requested-only, missing, or mismatched lane evidence.

VERDICT
Return ship, fix-first, or rethink with at most three actionable findings.
```

Require matching fresh reviewer runtime evidence before accepting the verdict. If the
route is unavailable or mismatched, block completion; there is no self-review fallback.

## Plain-language handoff

```text
RESULT
<What now works or exists.>

CHANGED
- <Everyday-language summary.>

CHECKS
- <Check> -> <observed result.>

REVIEW
<Concise review-and-repair or labeled self-review, plus verdict.>

NOTES
<Remaining risk, assumption, limitation, or user action; omit when none.>
```
