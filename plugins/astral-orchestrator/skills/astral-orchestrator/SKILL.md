---
name: astral-orchestrator
description: "Orchestrate project work with the current Sol or Astra session as lead, configurable Astra, Luna, and Terra workers, explicit opt-in modes, mandatory route visibility, and verified results. Use when the user invokes Astral Orchestrator, asks for real multi-agent delegation or disciplined one-session work, wants to change effort levels, wants a request built or fixed end to end, requests risk-aware execution, or wants model-routed implementation."
---

# Astral Orchestrator

Own the result from request to verified handoff. Detect the current session model and
effort, keep that session as the primary orchestrator, use configured workers for bounded
execution, and make every route visible to the user.

## Primary detection and worker independence

Every mode accepts the current primary when runtime evidence identifies either Sol
(`gpt-5.6-sol`) or Astra (`gpt-6-astra`) at a supported observed effort. The model and
effort already running the user's task define the primary route. Do not replace that
session, require a preferred lead model, or compare it with the saved orchestrator effort.

Worker effort is independent of primary effort. In modes that allow workers, an
explicitly selected native Astra worker uses the configured `astra` effort, including a
higher effort than a Sol or Astra primary. Use the built-in `worker`, explicit
`gpt-6-astra`, the configured effort, and `fork_turns: "none"`; verify the actual route.
Choose Astra only when its deeper reasoning is materially useful for a bounded card.
Default to Luna or Terra for ordinary implementation so Astra cost is deliberate.
Comet and Singularity still never spawn. Hypernova keeps its mode-specific child rules.

## Mandatory Astral status

Do not skip route visibility, even for a fast task or when no worker is needed. The first
user-facing progress update after this skill activates must include an **Astral status**
panel with the detected or still-unverified primary model and effort. For any child lane,
emit the panel immediately before launch, after the launch returns an identifier, when
runtime evidence changes, and in the final handoff. Show failed, blocked, discarded, and
not-needed lanes instead of silently removing them. If a Markdown table cannot render,
use compact bullets with the same fields; omitting the status is not allowed.

## Execution economy

Follow **JUST DO IT** and **YAGNI**. Use Singularity discipline in every mode: the primary does
the thinking once, keeps the request narrow, and delegates only when a bounded worker
will materially improve execution. No duplicate planning document, spec,
research report, or evidence ledger unless the user requested it, the repository requires
it, or it is itself the deliverable.

Prefer the smallest relevant checks. Run long or full suites only when repository rules,
a broad change surface, or a release gate requires them. Do not rerun unchanged checks.
Orbit, Event Horizon, Pulsar, Morph, and Constellation are standard multi-agent modes:
launch every ready independent card concurrently when capacity exists, and allow bounded
hierarchical delegation when it removes a real bottleneck. Use the shallowest useful
hierarchy. Hypernova is the explicit performance-first multi-agent route: it fills every
safely usable native slot with selected workers (Sol Ultra by default or Astra at the
configured `astra` effort), but its workers never delegate.
Comet and Singularity never spawn. Security risk strengthens confirmation and acceptance
criteria; it does not justify unrelated documentation or repeated review cycles.

Read [references/modes-and-risk.md](references/modes-and-risk.md) for mode, risk, and
confirmation decisions. Before spawning a Codex lane or using Singularity, read
[references/routing-and-preflight.md](references/routing-and-preflight.md) and
[references/work-templates.md](references/work-templates.md). Comet retains progressive
disclosure and does not load those references unless another rule requires them. Before a portable worker,
read `portable-hosts.md` and the work templates instead.
When the user explicitly names Pulsar, also read
[references/pulsar-mode.md](references/pulsar-mode.md).
When the user explicitly names Singularity, also read
[references/singularity-mode.md](references/singularity-mode.md) after the routing and
work-template references above.
When the user explicitly names Morph, also read
[references/morph-mode.md](references/morph-mode.md). When the user explicitly names Constellation,
also read [references/constellation-mode.md](references/constellation-mode.md).
When the user explicitly names Hypernova, also read
[references/hypernova-mode.md](references/hypernova-mode.md) after the routing and
work-template references above.

## Host boundary

First identify whether the host is Codex from observable host/runtime evidence, not
from a user guess. On Codex, use the fixed routes and bundled preflight below. On a
non-Codex Agent Plugins-compatible host, load
[references/portable-hosts.md](references/portable-hosts.md) before doing anything beyond
mode selection. Only explicitly selected Morph or Constellation portable routes may run
there. Do not attempt Codex scripts, `CODEX_THREAD_ID`, or Astral agent names on a
non-Codex host. Hypernova is Codex-native only and has no portable route.

Portable routes require observable host capabilities for model selection, separate worker
contexts, a fresh reviewer context, and—only for concurrent Constellation—available
concurrency. Record the actual and requested provider, model, and effort separately. If
the exact model, effort, or fresh context cannot be proven, stop or use the documented
serial portable Constellation fallback; never claim Sol/Luna/Terra unless observed.

## Live Astral status

Codex plugins cannot pin a permanent native UI widget. Progress commentary and the final
handoff are the reliable portable surfaces. Follow the mandatory checkpoints above and
show the detected primary, each selected worker, and the reviewer when required, with
lane, role, requested and observed model and effort, state, and evidence. A requested
route is not observed route evidence: use the template and routing guide to label it
plainly. Keep the panel current without inventing activity, repeating unchanged detail,
or dumping evidence that does not affect the next decision.
Always emit it as an actual GitHub-flavored Markdown table with a header separator row;
never fence it and never use plain pipe text.

## 1. Choose the mode and risk

- **Comet** — tiny, reversible, low-risk work with an obvious solution. The detected primary
  works directly at its observed effort and self-reviews; no worker is spawned.
- **Orbit (default)** — normal feature, fix, content, configuration, or project work.
  The primary routes bounded execution to Luna, Terra, or Astra at the selected lane's
  configured effort and integrates it.
- **Event Horizon** — high-impact, hard-to-reverse, security-sensitive, financial, privacy,
  production, migration, or explicitly thorough work. Apply Singularity discipline with
  multi-agent execution: use the minimum confirmation gates needed for consequential
  actions, parallelize ready independent cards, use the smallest relevant checks, and run
  one concise workspace-write Sol review-and-repair pass after integration.
- **Singularity (explicit opt-in)** — meaningful low- or medium-risk work that is larger
  than Comet, but stays in one verified primary session at its observed effort. Do not
  spawn subagents, planning probes, worker lanes, or a fresh reviewer; the primary
  self-reviews once using actual changes and evidence. Read the Singularity
  reference before using it. Event Horizon overrides Singularity for high-risk work.
- **Hypernova (explicit opt-in)** — the performance-first opposite of Singularity. One
  observed Sol or Astra primary at its current effort launches every ready independent implementation card across
  the maximum safely available native MultiAgentsV2 capacity, using built-in Sol
  Ultra workers by default, or selected Astra workers at the configured `astra` effort,
  then requires one fresh built-in reviewer on the selected review route. Hypernova never
  auto-selects and never falls back to a legacy process, portable route, serial route,
  self-review, or another model or effort. High-risk cards retain Event Horizon
  confirmation safeguards.
- **Pulsar (explicit opt-in)** — a deliberately slower, evidence-oriented route for a
  user who explicitly names Pulsar. Freeze one canonical work card and its acceptance
  checks, keep a non-secret resumable local ledger, and use planning probes only when
  Luna/Terra selection is ambiguous. Pulsar is never auto-selected; recommend Orbit
  for normal work. Its detailed state machine is in the Pulsar reference.
- **Morph (explicit opt-in)** — a user-selected routed or native worker model for a
  bounded card. The detected session remains primary and the exact fresh Sol reviewer
  remains required. Read the Morph reference before launch.
- **Constellation (explicit opt-in)** — a capacity-limited concurrent first wave for independently
  owned ready cards. The detected session remains primary with one fresh Sol reviewer; no extra Sol
  implementers are spawned by default. Read the Constellation reference before launch.

Legacy aliases are advisory prompt compatibility only: Quick maps to Comet; Guided maps
to Orbit; Careful maps to Event Horizon; Measured maps to Pulsar. A legacy alias never
changes the corresponding route or safeguards.

Honor an explicit mode unless its safeguards are too weak for the observed risk. Raise
the safeguards when necessary and explain why in one sentence. Never lower Event Horizon
without permission.

## 2. Prove the Codex orchestration preflight

On Codex, Astral Orchestrator v3 uses these exact models and defaults:

- primary orchestrator: the current `gpt-5.6-sol` or `gpt-6-astra` session at its
  observed effort;
- deep-reasoning worker: built-in native `worker` with `gpt-6-astra` at configured Astra
  effort (Medium by default);
- focused worker: `astral_orchestrator_luna_implementer` (Luna Max);
- context-heavy worker: `astral_orchestrator_terra_implementer` (Terra High);
- reviewer: `astral_orchestrator_sol_reviewer` (Sol High, workspace-write review-and-repair).

Resolve the bundled `../../scripts/configure-effort.py` and run it with `--show --json`
to obtain the effective effort for all five lanes. Missing settings mean the defaults
above. For every mode, run `../../scripts/check-primary.py` without an Ultra flag.
It detects `gpt-5.6-sol` or `gpt-6-astra` and accepts the supported effort observed in
that session, independently of saved settings. The optional `--require-sol-ultra` and
`--require-astra-ultra` flags perform strict checks only; no mode requires them.
If evidence is unavailable, modes other than Singularity and Hypernova may ask once for
model and effort confirmation and label it **user-confirmed**, not observed.
Unavailable evidence blocks Singularity, and unavailable evidence blocks Hypernova;
user confirmation cannot override this. `mismatch` or `invalid` evidence blocks every
mode. The detected primary remains the orchestrator for the whole run.

For Orbit, Event Horizon, and Pulsar work, first inspect the `collaboration.spawn_agent`
contract. Current Codex **MultiAgentsV2** hosts expose all five required controls:
`agent_type`, `task_name`, `model`, `reasoning_effort`, and `fork_turns`. When all five
fields are available, use native spawning as the standard fixed route: choose a unique
lowercase `task_name`, pass the role's exact model and configured effort, set
`fork_turns: "none"`, and send the complete standalone work packet. An unavailable,
missing, or mismatched optional custom profile does not force a nested CLI process on a
current v2 host. Use the built-in native worker with explicit values for Astra, Luna, or Terra
implementation, or the built-in native default with explicit values for a reviewer,
preserving the requested-versus-observed route evidence.

Custom agent file values take precedence over explicit spawn values. Therefore use an
Astral custom role only when its fixed model and effort match the effective settings and
the role adds a needed fixed capability. In all
other v2 cases, deliberately choose the appropriate built-in native agent rather than
silently substituting model or effort. A failed native v2 route blocks the lane; it does
not fall through to a process merely because profiles are absent or customized.

Hypernova requires those same five native controls plus observed host-advertised
capacity. It uses the built-in `worker` for every implementation lane and the built-in
`default` for its mandatory fresh reviewer. Every child is explicitly pinned to
its selected route (Sol Ultra by default, or Astra at configured `astra` effort), receives a distinct unique lowercase `task_name`, and
sets `fork_turns: "none"`. Existing custom profiles, including the Sol High reviewer,
are ineligible because their fixed settings can override explicit spawn values.
Hypernova workers cannot delegate. If native controls, capacity, or an exact observed
route is missing or mismatched, stop Hypernova and discard output from the mismatched
lane; do not use a legacy exact-process, process, portable, serial, self-review, model,
or effort fallback.

Keep the bundled exact-process route as a clearly bounded **legacy exact-process fallback**
only when the host collaboration tool lacks one or more required v2 controls—
`agent_type`, `task_name`, `model`, `reasoning_effort`, or `fork_turns`—and compatibility
requires it. Require its successful dry run for the needed role, workdir, and private
packet. That route starts the pinned model with the configured effort and shipped role
instructions. Stop when the chosen native route or this legacy fallback cannot be
proven. A blocking preflight ends the current turn. Never silently lower an unsupported
effort.

Singularity retains the exact detected-primary preflight but never uses child lanes or a
fresh reviewer. Hypernova requires the observed primary at its current effort and a fresh
observed review on the selected child route. Morph and Constellation retain the normal
detected-primary preflight and fresh Sol review. Their worker
rules are explicit opt-ins defined only in their dedicated references; never treat either
as permission to change the primary or final-review model.

When the user explicitly asks to show or change effort settings, run the configuration
script. Preserve unspecified lanes and report the resulting five values. Use `--reset`
only when the user asks to restore defaults. Explain that `max` and `ultra` are
model- and account-dependent.

Give every lane a complete standalone work packet. For a native lane, explicitly provide
`agent_type`, a unique lowercase `task_name`, `model`, `reasoning_effort`, and
`fork_turns: "none"`. For a legacy exact-process lane, use the bundled launcher with the
matching role. Combine the native spawn request or successful launcher dry-run, requested
route, task or session id, and observed model/effort evidence before accepting its work.
The routing guide defines the exact behavior.

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

Keep the card in the current message or working context; no duplicate planning document
is needed. For every multi-agent mode, turn the request into the smallest dependency graph
that exposes independent cards without inventing work. Pulsar freezes exactly one canonical work card; it may describe multiple bounded
items inside that card, and one selected parent lane owns integration while authorized
children may own independent items. Singularity keeps one card
with no more than five active steps and one in progress. Morph uses a separately
selected exact worker model only for its bounded card. Constellation may fan out only cards proven
independent by its reference. Hypernova makes only real requested work into cards, proves
independence and observed capacity, and sizes every wave to the smaller of ready
independent cards or observed available slots minus the primary's one slot. Recalculate
after each wave; never invent work to fill capacity. Keep requirements,
architecture, task decomposition, acceptance decisions, and cross-lane integration in
the detected primary session at its observed effort.

## 4. Route bounded execution

Select each lane by the work, never by prestige:

- Use Luna at its configured effort for narrow, repeatable, fully specified, or mechanical
  work.
- Use Terra at its configured effort for normal implementation that is context-heavy, implements a
  component or external integration, is moderately ambiguous, or needs judgment inside
  a settled architecture.
- Use Astra at its configured effort for a bounded worker card only when Luna or Terra is
  unlikely to handle the reasoning depth, cross-domain synthesis, or difficult diagnosis
  efficiently enough to justify the added cost. Record that reason in the work card.
- Keep work in the primary session when it changes requirements, architecture, safety
  boundaries, or acceptance decisions. Settle those decisions before delegating
  execution.

These normal worker-selection rules do not apply to Hypernova. Its detected primary uses
the current session effort. Implementation and fresh review use Sol Ultra by default or
selected Astra at the configured `astra` effort.

Give every worker the complete implementation contract from the template: outcome,
ownership, done-when conditions, interfaces and boundaries, exact checks, and whether
downstream delegation is allowed. State that it is not alone in the codebase and must
preserve unrelated edits.

Orbit, Event Horizon, Pulsar, Morph, and Constellation are standard multi-agent modes. Launch every
ready independent card concurrently up to observed host capacity. A parent worker may
spawn bounded child workers only when its packet explicitly allows it, assigns exact
non-overlapping ownership, pins each child route, and makes the parent responsible for
integration and evidence. Use the shallowest useful hierarchy; do not add coordination-only
parents or duplicate a card at two levels. Comet and Singularity never spawn.

Hypernova launches every ready independent card concurrently up to its exact safe wave
limit and prohibits downstream delegation. A safety gate or real dependency keeps a card
out of the ready set; it does not authorize a different route. A one-card wave produced
by the exact readiness-and-capacity calculation is still Hypernova, but unavailable
capacity never permits a serial fallback.

Serial execution is required only when cards share ownership, depend on another output or
interface decision, wait on a confirmation gate, or exceed available capacity. Do not
serialize ready independent work merely for convenience, and do not spawn agents merely
to make the run look busy. Answer-only, planning-only, and blocked requests need no worker.

## 5. Integrate and verify

Treat every worker report as a claim, not proof:

1. Inspect the actual files and complete accumulated change set.
2. Confirm every change stays within its work card and preserves user-owned edits.
3. Resolve cross-lane interfaces in the primary session.
4. Run the smallest relevant checks: focused tests, lint, build, validators, or artifact inspections.
5. Compare observed evidence with every **Done when** item.

Never claim a check passed if it was not run. Fix failures through the appropriate
pinned lane, rerun affected checks, and inspect the result again.

## 6. Require the right review

- **Comet:** primary-session self-review at the observed primary effort using the actual
  change and evidence.
- **Orbit:** use a new native reviewer with an explicit `agent_type`, a distinct unique
  lowercase `task_name`, exact Sol `model`, configured reviewer `reasoning_effort`, and
  `fork_turns: "none"` after every worker-produced change. Prefer a matching
  `astral_orchestrator_sol_reviewer` profile only when its fixed values match; otherwise
  use the built-in native default with those explicit values and a complete review packet.
  For a no-change or answer-only request with no worker, label primary-session Sol
  self-review plainly.
- **Event Horizon:** use one concise review-and-repair pass with the exact Sol reviewer
  lane after a worker-produced change. The reviewer uses workspace-write with no special
  isolation, may fix bounded obvious issues directly, and runs the smallest affected
  check. Return one verdict line and at most three findings. Do not launch a second
  reviewer for a small repair; the primary inspects the fix and reruns the affected check.
- **Singularity:** do not spawn a reviewer. The primary self-reviews once using the actual change
  set and verification evidence; this is not independent review.
- **Hypernova:** always launch one fresh built-in native `default` reviewer after
  integration and focused verification. Pin it to Sol Ultra by default or explicitly
  selected `gpt-6-astra` at the configured `astra` effort, with a distinct unique lowercase task name and `fork_turns: "none"`. The Sol High custom
  reviewer is ineligible. Missing or mismatched reviewer evidence blocks completion;
  there is no self-review fallback.
- **Pulsar:** use the normal Sol reviewer after the selected worker. High-risk Pulsar
  work inherits Event Horizon confirmation and concise review-and-repair.
- **Morph and Constellation:** use the normal exact Sol reviewer after integrated worker
  changes. Event Horizon risk still requires its confirmation gates and concise
  review-and-repair.

Give the reviewer only the outcome, acceptance conditions, boundaries, complete change
set, and focused verification evidence. Accept exactly one verdict: **ship**,
**fix-first**, or **rethink**, followed by at most three actionable findings. The reviewer
may fix a small, obvious issue directly; the primary then inspects that repair and reruns
the smallest relevant checks without starting another reviewer cycle. A `rethink` verdict
returns architecture or scope decisions to the primary and may require user direction.

If the exact reviewer route cannot be proven, the primary performs and labels a concise
primary-session self-review unless an external policy or Hypernova explicitly requires
independent review. Hypernova blocks instead. Do not manufacture isolation evidence or
block ordinary completion on sandbox mode alone.

## 7. Hand off plainly

Lead with the outcome. Then state:

- what changed in everyday language;
- which lane handled each bounded part;
- the observed role, model, and effort only when it affected routing or remains uncertain;
- which checks ran and their concrete results;
- the review-and-repair verdict or clearly labeled self-review;
- any limitation, remaining risk, or user action.

Do not bury a failed check, missing route proof, incomplete review, assumption, or
unfinished item behind a general completion claim.
