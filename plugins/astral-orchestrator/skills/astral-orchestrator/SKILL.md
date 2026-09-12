---
name: astral-orchestrator
description: Run Astral Orchestrator when explicitly requested, when an Astral mode is selected, or when configuring Astral model/effort routes. Supports bounded delegation and explicit single-session modes.
---

# Astral Orchestrator

Own the requested result through verification and handoff. The Astra primary owns
requirements, architecture, routing, integration, and acceptance. Workers own bounded
execution. Keep the process understandable to a non-technical user.

## Choose the mode and read only what it needs

Honor the selected mode. Orbit is the default when the user requests Astral without a
mode; select Comet for tiny, obvious, reversible work. Raise safeguards for observed risk
and explain why; never lower Event Horizon without permission. Specialized modes remain
explicit opt-ins.

| Mode | Execution and review | Read when selected |
|---|---|---|
| Comet | Astra works directly and self-reviews; no worker is spawned | Primary verification and applicable risk gates below |
| Orbit (default) | Delegate useful bounded work to Luna or Terra, then review the integrated change set | Child routing before delegation |
| Event Horizon | Consequential or explicitly thorough work; delegated execution and concise Sol review-and-repair | Risk gates and child routing before delegation |
| Singularity (explicit opt-in) | Meaningful low/medium-risk work in one verified Astra session; do not spawn subagents or a fresh reviewer | [Singularity](references/singularity-mode.md) when the user explicitly names Singularity |
| Pulsar (explicit opt-in) | Deliberately slower evidence-oriented work with a frozen card and resumable state | [Pulsar](references/pulsar-mode.md) when the user explicitly names Pulsar |
| Morph (explicit opt-in) | Exact user-selected worker model for bounded work | [Morph](references/morph-mode.md) when the user explicitly names Morph |
| Constellation (explicit opt-in) | Capacity-aware parallel cards with independent ownership | [Constellation](references/constellation-mode.md) when the user explicitly names Constellation |
| Hypernova (explicit opt-in) | Astra Ultra primary and maximum safe native concurrency with Sol Ultra workers and mandatory fresh Sol Ultra review | [Hypernova](references/hypernova-mode.md) when the user explicitly names Hypernova |

Legacy aliases remain advisory: Quick = Comet, Guided = Orbit, Careful = Event Horizon,
Measured = Pulsar. They do not change routes or safeguards.

- Establish whether the host is Codex from observable runtime evidence.
- On Codex, read [primary-verification.md](references/primary-verification.md) before
  execution. Reuse verified evidence within the same session unless the route, effort,
  settings, or host changes or the evidence becomes uncertain.
- Use [modes-and-risk.md](references/modes-and-risk.md) for risk, confirmation, and review
  decisions. Read the applicable section, not every mode's workflow.
- Before a Codex child launch, read the relevant section of
  [routing-and-preflight.md](references/routing-and-preflight.md). Native MultiAgentsV2
  is the standard route; read the legacy exact-process section only if the host lacks
  required native controls. Comet and Singularity do not need child setup or templates.
- On a non-Codex host, use [portable-hosts.md](references/portable-hosts.md) only for an
  explicitly selected Morph or Constellation route. Do not run Codex scripts there.
- Use only the needed section of [work-templates.md](references/work-templates.md) when
  preparing a packet or when its fields help the next action. Templates are examples,
  not mandatory documents or additional work.

## Model and effort boundaries

The primary is `gpt-6-astra`, High by default. Normal modes require its observed effort
to match the configured orchestrator effort. All host-supported configurable efforts
remain available; never silently lower or substitute a selected effort. Primary and child
settings are independent. Hypernova requires an observed Astra Ultra primary and exact
Sol Ultra workers and fresh review, without changing normal saved settings. Comet and
Singularity never spawn.

The bundled checker is authoritative for this version. Do not infer runtime support
from another source version or change global settings automatically to resolve a mismatch.

Normal child defaults are Luna Max for mechanical work, Terra High for context-heavy
implementation, and Sol High for fresh review. Resolve effective child settings before
launch; distinguish package defaults, installed profiles, selected settings, and observed
runtime evidence. Never silently substitute model or effort. Use a custom role only when
its fixed values match the selected route; otherwise use the exact built-in native route
specified in the routing guide. Do not reinstall profiles or edit global configuration
merely because they differ from package defaults.

A mismatched or invalid primary blocks execution in every mode. Unavailable evidence
blocks Singularity and Hypernova; other modes allow the documented one-time user-confirmed
primary fallback. Requested values are never observed evidence.

## Scope, autonomy, and completion

Follow JUST DO IT and YAGNI with Singularity discipline: keep one compact outcome,
done conditions, ownership/boundaries, and relevant checks in context. No duplicate
planning document, spec, report, or ledger unless requested, required by the repository
or selected mode, or itself the deliverable.

Use explicit authorization already given in this task unless its target or effect has
changed. Finish authorized local preparation, inspection, and verification before asking
for a consequential action. While approval or a required answer is pending, do not perform
dependent work; continue independent authorized work. End the turn when nothing useful
remains outside the gate. The risk guide defines consequential actions and genuine user
decisions; local edits, tests, previews and read-only inspection within scope need no
extra approval. A blocked route stops that route and dependent work, not unrelated
ready work. Never relabel a blocked mode as successfully completed.

Define completion from the requested outcome. When building or fixing an app, include
running it locally, inspecting the relevant behavior, and repairing failures when those
steps are within scope. Continue until the acceptance conditions and required review pass,
or report the concrete remaining blocker. Respect explicit preview-only or user-review
pauses. Do not turn technical acceptance into permission to publish or deploy.

## Delegate only useful work

Orbit, Event Horizon, Pulsar, Morph, and Constellation use bounded parallel or hierarchical
execution. Create a delegated card only when its independent work is substantial enough
to justify context transfer and integration. Do not split tiny work to fill slots.
Keep requirements and acceptance decisions in Astra; route mechanical execution to Luna
and context-heavy implementation to Terra. Honor explicit Morph worker selections.
Answer-only, planning-only, and blocked requests need no worker.

For actual ready cards, launch every ready independent card concurrently up to observed
capacity, respecting dependencies and ownership. Hypernova retains maximum safely usable
native capacity for real ready work and prohibits downstream delegation. Comet and
Singularity never spawn. Do not switch a selected mode just to avoid its contract.

Give each mutable browser session one owner. Delegate independent analysis or checks only
when they can proceed without competing for that session. Every worker receives a
standalone packet with outcome, exact ownership, acceptance conditions, interfaces,
boundaries, and checks. State that it is not alone in the codebase and must preserve
concurrent and unrelated edits.

Downstream delegation is not allowed unless the packet names a useful independent
subtree, its ownership, exact routes, and integration responsibility. Use the shallowest
useful hierarchy; no coordination-only parents or duplicate ownership.

## Verify and review

In every mode, preserve user-owned and unrelated edits. Inspect actual files and the
complete accumulated change set; confirm every change stays within the card and preserves
those edits, resolve interfaces, and compare evidence with each done condition. Use the smallest relevant checks. Full suites
need a repository rule, broad change surface, release gate, or unresolved risk. Do not
rerun unchanged checks; after a repair rerun the affected checks. Never report a check
as passed unless it ran.

Apply [Review availability and route failure](references/modes-and-risk.md#review-availability-and-route-failure)
once to the integrated change set unless concrete risk requires earlier review. That
section is the common authority for missing evidence, rejected mismatches, allowed Astra
self-review, and mandatory independent review. Comet/Singularity self-review is not
independent review. Hypernova always needs its fresh exact selected reviewer.

Use one concise review-and-repair pass in workspace-write for delegated changes. A
reviewer may fix a bounded obvious issue and run its affected check. Return one verdict
line, ship/fix-first/rethink, and at most three findings. Astra inspects repairs without
starting a second review cycle for a small fix. A rethink returns scope, architecture,
or safety decisions to Astra. “Ship” means technical acceptance, not publication.

## Status and handoff

Show compact Astral status only when the route or phase changes. Always use an actual
GitHub-flavored Markdown table with a header separator row, never a fenced or plain pipe
panel. Include lane, role, model, effort, state, and evidence; distinguish requested from
observed values. Singularity needs only the Astra primary row. Do not invent activity,
repeat unchanged panels, or expose packets/secrets. Detailed states and examples live in
the routing and template references when needed.

Lead the handoff with the outcome, then checks/results, review or labeled self-review,
and any unfinished item or uncertainty. Identify lanes and observed routes when material.
Report local changes, commits, branch publication, merge, deployment, submission and public
availability separately. Do not claim completion while an acceptance condition is open.
