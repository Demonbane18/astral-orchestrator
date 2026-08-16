# Astral Orchestrator work templates

Load only the template needed for the next action. Replace every angle-bracketed field.

## Astral status panel

Use this compact panel in every substantive progress update while Astral is active. It
is progress commentary, not a permanent native UI widget. Keep one row for the Sol
primary, one for each selected worker, and one for the fresh reviewer when required.
Use `not needed` when a lane will not be used, and use `planned` for a required reviewer
that is waiting to launch. Write `not yet required` only in the evidence field as an
explanation, never as a state. Requested facts are the intended route; observed facts
require runtime evidence. Do not call a requested lane `running` or observed without
that evidence. Always emit the panel as an actual GitHub-flavored Markdown table with
the header separator row below: never fence it and never use plain pipe text.

| Lane | Role | Model | Effort | State | Evidence |
|---|---|---|---|---|---|
| Sol primary | requested: primary session; observed: <primary runtime or not yet available> | requested: gpt-5.6-sol; observed: <value or not yet available> | requested: <configured effort>; observed: <value or not yet available> | <planned/requested/launched/running/returned/verified/blocked/failed/not needed> | <primary checker, user-confirmed fallback, or runtime evidence> |
| Worker <card> | requested: worker, matching astral_orchestrator_luna_implementer profile, matching astral_orchestrator_terra_implementer profile, or Morph worker; observed: <agent type or Morph route / not yet available> | requested: <model>; observed: <value or not yet available> | requested: <configured effort>; observed: <value or not yet available> | <planned/requested/launched/running/returned/verified/blocked/failed/not needed> | <task or session id and matching runtime evidence> |
| Fresh reviewer | requested: default or matching astral_orchestrator_sol_reviewer profile; observed: <agent type or not yet available> | requested: gpt-5.6-sol; observed: <value or not yet available> | requested: <configured effort>; observed: <value or not yet available> | <planned/requested/launched/running/returned/verified/blocked/failed/not needed> | <task or session id, runtime evidence, and sandbox when applicable> |

Use `planned`, `requested`, `launched`, `running`, `returned`, `verified`, `blocked`,
`failed`, or `not needed` only as defined in `routing-and-preflight.md`. Update the
panel at preflight, launch, new evidence, state changes, completion, failure, and at a
restrained interval for long-running work. Do not repeat it merely to create activity.

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
Perform this assignment directly. Do not spawn or delegate to another agent.

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

## Fresh review

```text
ROLE
Perform a fresh review. Remain behaviorally read-only: do not edit, format, delete, or
implement files. Perform the review directly; do not spawn or delegate to another agent.

OUTCOME
<The user's requested result.>

DONE WHEN
- <Acceptance condition.>

BOUNDARIES
- <Required compatibility, scope limits, and safety constraints.>

CHANGE SET
<Complete diff or exact base/head revisions plus allowed files.>

CHECKS
- <Command or inspection> -> <actual observed evidence>

REVIEW
Inspect the actual files and complete change set. Judge correctness, completeness,
regressions, scope discipline, interface preservation, test adequacy, and material risk.

VERDICT
Return exactly one:
- ship — the inspected result and evidence satisfy the outcome;
- fix-first — bounded corrections are required;
- rethink — architecture, scope, or assumptions must change.

REPORT
- Verdict: ship, fix-first, or rethink
- Route: observed agent path, model, effort, sandbox, and task id
- Reason: decisive evidence-based reason
- Findings: precise references and required fixes, or none
- Residual risk: most important remaining risk, or none
```

## Plain-language handoff

```text
RESULT
<What now works or exists.>

CHANGED
- <Everyday-language summary.>

CHECKS
- <Check> -> <observed result.>

REVIEW
<Independent review, self-review, or incomplete review, plus verdict when applicable.>

NOTES
<Remaining risk, assumption, limitation, or user action; omit when none.>
```
