---
name: astral-orchestrator
description: "Orchestrate project work with a Sol lead, fixed Luna and Terra lanes, explicit opt-in Morph and Constellation workers, configurable reasoning effort, and a fresh Sol reviewer. Use when the user invokes Astral Orchestrator, asks for real multi-agent delegation, wants to change Astral Orchestrator effort levels, wants a request built or fixed end to end, requests risk-aware execution, or wants model-routed implementation with verified results."
---

# Astral Orchestrator

Own the result from request to verified handoff. Keep the Sol primary at its configured
effort accountable for planning, routing, integration, and final decisions; use pinned
workers for bounded execution; and keep the process understandable to a non-technical
user.

Read [references/modes-and-risk.md](references/modes-and-risk.md) for mode, risk, and
confirmation decisions. Before spawning a Codex lane, read
[references/routing-and-preflight.md](references/routing-and-preflight.md) and
[references/work-templates.md](references/work-templates.md). Before a portable worker,
read `portable-hosts.md` and the work templates instead.
When the user explicitly names Measured, also read
[references/measured-mode.md](references/measured-mode.md).
When the user explicitly names Morph, also read
[references/morph-mode.md](references/morph-mode.md). When the user explicitly names Constellation,
also read [references/constellation-mode.md](references/constellation-mode.md).

## Host boundary

First identify whether the host is Codex from observable host/runtime evidence, not
from a user guess. On Codex, use the fixed routes and bundled preflight below. On a
non-Codex Agent Plugins-compatible host, load
[references/portable-hosts.md](references/portable-hosts.md) before doing anything beyond
mode selection. Only explicitly selected Morph or Constellation portable routes may run
there. Do not attempt Codex scripts, `CODEX_THREAD_ID`, or Astral agent names on a
non-Codex host.

Portable routes require observable host capabilities for model selection, separate worker
contexts, a fresh reviewer context, and—only for concurrent Constellation—available
concurrency. Record the actual and requested provider, model, and effort separately. If
the exact model, effort, or fresh context cannot be proven, stop or use the documented
serial portable Constellation fallback; never claim Sol/Luna/Terra unless observed.

## Live Astral status

Codex plugins cannot pin a permanent native UI widget. The reliable portable surface is
progress commentary and status updates. While Astral is active, include a compact
**Astral status** panel in every progress update that contains substantive progress.
Show the Sol primary, each selected worker, and the fresh reviewer when required, with
lane, role, requested and observed model and effort, state, and evidence. A requested
route is not observed route evidence: use the template and routing guide to label it
plainly. Keep the panel current through preflight, running work, review, and handoff
without inventing activity or repeating unchanged detail.

## 1. Choose the mode and risk

- **Quick** — tiny, reversible, low-risk work with an obvious solution. The Sol primary
  works directly at its configured effort and self-reviews; no worker is spawned.
- **Guided (default)** — normal feature, fix, content, configuration, or project work.
  Sol routes bounded execution to Luna or Terra at their configured effort and integrates
  it.
- **Careful** — high-impact, hard-to-reverse, security-sensitive, financial, privacy,
  production, migration, or explicitly thorough work. Use visible planning, strict
  confirmation gates, pinned implementation lanes, and a fresh Sol review at the
  configured reviewer effort.
- **Measured (explicit opt-in)** — a deliberately slower, evidence-oriented route for a
  user who explicitly names Measured. Freeze one canonical work card and its acceptance
  checks, keep a non-secret resumable local ledger, and use planning probes only when
  Luna/Terra selection is ambiguous. Measured is never auto-selected; recommend Guided
  for normal work. Its detailed state machine is in the Measured reference.
- **Morph (explicit opt-in)** — a user-selected routed or native worker model for a
  bounded card. Sol remains the configured primary and the exact fresh Sol reviewer
  remains required. Read the Morph reference before launch.
- **Constellation (explicit opt-in)** — a capacity-limited concurrent first wave for independently
  owned ready cards. Sol remains one primary and one fresh reviewer; no extra Sol
  implementers are spawned by default. Read the Constellation reference before launch.

Honor an explicit mode unless its safeguards are too weak for the observed risk. Raise
the safeguards when necessary and explain why in one sentence. Never lower Careful
without permission.

## 2. Prove the Codex orchestration preflight

On Codex, Astral Orchestrator v3 uses these exact models. Their default efforts are:

- main orchestrator: **Sol High** (`gpt-5.6-sol`, reasoning `high`);
- focused worker: `astral_orchestrator_luna_implementer` (Luna XHigh);
- context-heavy worker: `astral_orchestrator_terra_implementer` (Terra XHigh);
- fresh reviewer: `astral_orchestrator_sol_reviewer` (Sol High, requested read-only).

Resolve the bundled `../../scripts/configure-effort.py` and run it with `--show --json`
to obtain the effective effort for all four lanes. Missing settings mean the defaults
above. For every mode, resolve and run `../../scripts/check-primary.py` first. It uses the
host's local rollout inspector and `CODEX_THREAD_ID` when available, then exits zero only
when the observed primary is `gpt-5.6-sol` at the configured orchestrator effort. If its
allowlisted JSON says unavailable, ask the user once to confirm the model and effort;
record that as **user-confirmed**, not observed evidence. The checker never asks the user
itself. A `mismatch` or `invalid` result blocks the route; manual confirmation cannot
override either one. A changed orchestrator setting applies to a new task, not the task
already running.

For Guided, Careful, and Measured work, select one of two exact fixed routes. First run the
bundled profile installer's exact `--check`. A pass permits native selection only when
the host exposes the exact role and its native profile effort equals the configured
effort. When that check reports missing or different native profiles, or the host cannot
make that exact native selection, run a successful dry-run of the bundled exact-process
launcher for the needed role. That route starts the pinned model with the configured
effort and shipped role instructions. Missing or different native profiles force the
exact-process route; they do not permit substitution or make optional setup required.
Stop only when neither exact route can be proven. A blocking preflight ends the current
turn. Never silently lower an unsupported effort.

Morph and Constellation retain this exact Sol primary preflight and fresh Sol review. Their worker
rules are explicit opt-ins defined only in their dedicated references; never treat either
as permission to change the primary or final-review model.

When the user explicitly asks to show or change effort settings, run the configuration
script. Preserve unspecified lanes and report the resulting four values. Use `--reset`
only when the user asks to restore defaults. Explain that `max` and `ultra` are
model- and account-dependent.

Do not silently substitute a built-in or differently configured agent. Give every lane
a complete standalone work packet. For a native lane, use `fork_turns: "none"`. For an
exact-process lane, use the bundled launcher with the matching role. Combine the native
profile status or successful launcher dry-run, requested route, task or session id, and
observed model/effort evidence before accepting its work. The routing guide defines the
exact behavior.

## 3. Frame and decompose the work

Inspect the workspace rules, relevant files, existing patterns, and available checks.
Turn the request into a compact work card:

- **Outcome:** the observable result and why it matters.
- **Done when:** specific acceptance conditions.
- **Boundaries:** in-scope files or systems, exclusions, and safety limits.
- **Checks:** exact tests or inspections that can prove success.

Ask only when a missing answer materially changes the outcome or makes proceeding
unsafe. Otherwise state the smallest reasonable assumption and continue. A blocking
clarification or confirmation ends the current turn: make no dependent change and
return one direct question immediately. Do not wait silently in the same turn.

For Guided or Careful work, split execution into the fewest useful non-overlapping work
cards. Measured freezes exactly one canonical work card; it may describe multiple bounded
items inside that card, but one selected lane owns all edits. Morph uses a separately
selected exact worker model only for its bounded card. Constellation may fan out only cards proven
independent by its reference. Keep requirements,
architecture, task decomposition, acceptance decisions, and cross-lane integration in
the Sol primary session at its configured effort.

## 4. Route bounded execution

Select each lane by the work, never by prestige:

- Use Luna at its configured effort for narrow, repeatable, fully specified, or mechanical
  work.
- Use Terra at its configured effort for normal implementation that is context-heavy, implements a
  component or external integration, is moderately ambiguous, or needs judgment inside
  a settled architecture.
- Keep work in the Sol primary when it changes requirements, architecture, safety
  boundaries, or acceptance decisions. Settle those decisions before delegating
  execution.

Give every worker the complete implementation contract from the template: outcome,
ownership, done-when conditions, interfaces and boundaries, and exact checks. State
that it is not alone in the codebase, must preserve unrelated edits, must do the work
directly, and must not spawn or delegate further.

Parallelize only independent cards with non-overlapping ownership. Run dependent work
or shared-file edits serially. Do not spawn agents merely to make the run look busy.
Guided, Careful, and Measured implementation must use at least one pinned worker whenever bounded
execution exists; answer-only, planning-only, and blocked requests need no worker. Morph
and Constellation use only their explicit worker rules and never weaken Careful safeguards.

## 5. Integrate and verify

Treat every worker report as a claim, not proof:

1. Inspect the actual files and complete accumulated change set.
2. Confirm every change stays within its work card and preserves user-owned edits.
3. Resolve cross-lane interfaces in the primary session.
4. Run the relevant tests, lint, build, validators, or artifact inspections.
5. Compare observed evidence with every **Done when** item.

Never claim a check passed if it was not run. Fix failures through the appropriate
pinned lane, rerun affected checks, and inspect the result again.

## 6. Require the right review

- **Quick:** Sol self-review at the configured orchestrator effort using the actual
  change and evidence.
- **Guided:** use a new `astral_orchestrator_sol_reviewer` native lane or reviewer process after
  every worker-produced change. For a no-change or answer-only request with no worker,
  label primary-session Sol self-review plainly.
- **Careful:** always use the exact Sol reviewer lane, and require observed read-only
  isolation before accepting its independent review.
- **Measured:** use the normal fresh Sol reviewer after the selected worker. High-risk
  Measured work also inherits Careful confirmation and observed read-only isolation.
- **Morph and Constellation:** use the normal fresh exact Sol reviewer after integrated worker
  changes. Careful risk still requires observed read-only isolation.

Give the fresh reviewer only the outcome, acceptance conditions, boundaries, complete
change set, and verification evidence. Accept exactly one verdict: **ship**,
**fix-first**, or **rethink**. A fix invalidates the old verdict; verify again and request
a new fresh reviewer, never a follow-up to the earlier reviewer. A `rethink` verdict
returns architecture or scope decisions to the Sol primary and may require user direction.

If the reviewer route or required isolation cannot be proven, stop and report review
as incomplete. Do not replace it with self-review or claim an independent review.

## 7. Hand off plainly

Lead with the outcome. Then state:

- what changed in everyday language;
- which lane handled each bounded part;
- the observed role, model, and effort evidence;
- which checks ran and their concrete results;
- the fresh review verdict or clearly labeled self-review;
- any limitation, remaining risk, or user action.

Do not bury a failed check, missing route proof, incomplete review, assumption, or
unfinished item behind a general completion claim.
