# Modes and risk guide

Use this guide when choosing an Astral Orchestrator mode or deciding whether work needs user
confirmation or a fresh review.

## Mode summary

| Mode | Best for | Planning | Agent route | Review |
|---|---|---|---|---|
| Comet | Small, obvious, reversible work | Mental or one sentence | Astra at configured effort | Astra self-review at configured effort |
| Orbit (default) | Normal project work | Compact work card | Luna or Terra at configured effort | Fresh Sol review of the integrated change set |
| Event Horizon | Consequential or explicitly thorough work | One compact in-context dependency graph; YAGNI | Parallel ready cards or a bounded hierarchy using Singularity discipline | One concise workspace-write Sol review-and-repair pass with at most three findings |
| Singularity (explicit opt-in) | Meaningful low- or medium-risk work larger than Comet | One compact card, five active steps maximum | One verified Astra primary at configured orchestrator effort; no subagents | One Astra self-review using actual changes and evidence; no fresh reviewer |
| Hypernova (explicit opt-in) | Maximum safe native speed and throughput | Smallest real dependency graph; never invent work | Observed Astra Ultra primary plus maximum safe waves of built-in Sol Ultra workers | Mandatory fresh built-in Sol Ultra reviewer; no self-review fallback |
| Pulsar (explicit opt-in) | A deliberately slower, evidence-oriented route decision | One frozen dependency graph and named checks | One parent lane may fan out independent frozen items; Luna/Terra probes only for routing ambiguity | Fresh Sol review; high-risk work also uses Event Horizon safeguards |
| Morph (explicit opt-in) | Bounded cards that need user-selected routed models | Compact cards plus exact worker models and requested efforts | Astra remains primary; independent Morph cards may run in parallel or form an authorized hierarchy | Fresh exact Sol review at configured effort |
| Constellation (explicit opt-in) | Several independently owned, ready cards | Astra proves independence and capacity before a concurrent first wave | Cost-aware non-Sol workers by default; capacity-limited fan-out | One fresh exact Sol review after integrated verification |

Orbit, Event Horizon, Pulsar, Morph, and Constellation are multi-agent modes. They launch
useful ready independent cards in parallel up to observed capacity and may use hierarchical
delegation when an owning parent can split a coherent subtree into non-overlapping child
cards. Use the shallowest useful hierarchy. Comet (Quick) and Singularity never spawn.
Hypernova is also multi-agent, but it uses exact built-in Sol Ultra child lanes, fills the
maximum safely available native MultiAgentsV2 capacity, and prohibits worker delegation.

Orbit is the default. A user can simply say “Use Astral Orchestrator” without learning the
mode system. Pulsar is never auto-selected: use it only when the user explicitly names
it. It is intentionally slower and more model-intensive, so recommend Orbit for normal
work.
Singularity, Morph, Constellation, and Hypernova are also explicit opt-in. They are never
selected merely because another model is available or because concurrent work would be
convenient. Read the selected mode's dedicated reference before execution. “Go nuts” may
mean use Hypernova's maximum safe native capacity only after explicit mode selection; it
does not bypass safety, scope, confirmation, or authorization.

On a non-Codex host, Comet, Orbit, Event Horizon, and Pulsar retain their documented modes but do
not acquire a generic replacement for their fixed Codex routes. Only explicitly selected Morph
or Constellation may use portable-host rules, and only after those capabilities are observed.
Hypernova is Codex-native only and has no portable or serial fallback.

## Risk levels

### Low risk

Typical signs:

- Small documentation, copy, styling, or isolated configuration changes
- Easy rollback with no stored-data effect
- No authentication, authorization, secrets, personal data, money, or production access
- Clear existing pattern and focused verification

Use Comet when the task is also small and obvious. For meaningful low- or medium-risk
work that the user explicitly wants completed in one verified Astra session, use
Singularity. Use Hypernova only when the user explicitly requests its performance-first
Astra Ultra primary and Sol Ultra child route; otherwise use Orbit.

### Medium risk

Typical signs:

- Normal application code or multi-file changes
- Public behavior changes with a bounded blast radius
- A bug whose root cause or regression surface needs investigation
- Moderate refactoring, dependencies, or integration work

Use Orbit. Review the complete integrated change set once at the configured reviewer
effort unless concrete risk requires earlier review. Answer-only
or no-change Orbit work may use a clearly labeled primary-session self-review.
Singularity is also available only by explicit opt-in when the bounded multi-step work can
stay in one Astra session; it has no subagents or fresh reviewer and does not weaken Event Horizon.
Hypernova is available only by explicit opt-in when its observed Astra Ultra primary,
native controls, capacity, implementation lanes, and mandatory fresh reviewer can all be
proven. It never falls back to another mode, route, model, effort, or self-review.

### High risk

Typical signs:

- Authentication, authorization, security controls, credentials, or secrets
- Payments, financial calculations, legal or regulated behavior
- Personal, medical, confidential, or high-volume data
- Database migrations, destructive actions, irreversible conversions, or data deletion
- Production infrastructure, external publishing, or messages sent to other people
- Broad public interfaces, concurrency, cryptography, or a large blast radius

Use Event Horizon even if the user asked for Comet. Explain that the risk raises the
confirmation and acceptance safeguards, not the scope or paperwork. High-risk Pulsar
work keeps its evidence-oriented routing and inherits Event Horizon confirmation plus
its concise review-and-repair pass.
Event Horizon overrides Singularity. Its safeguards also override Morph or Constellation whenever the work has this level of risk: keep
the exact Astra primary and Sol reviewer, use the required confirmation gates, and serialize any
card whose safety, interface, or verification depends on another card.
High-risk Hypernova cards inherit the same Event Horizon confirmation gates and required
safety dependencies while retaining exact Sol Ultra child lanes. Maximum concurrency never
makes a gated or dependent card ready.

## User confirmation gate

Obtain user confirmation before a destructive, irreversible, credential-related,
external publishing, or production action unless its specific target and effect were
already clearly authorized in this task. Carry authorization across turns; ask again
only if its target or effect changes. Resolve the target and explain the effect before
asking one concrete question.

Finish authorized local preparation, inspection, and verification before asking for the
consequential action. While approval or a required answer is pending, make no changes
behind that gate and do not perform dependent work. Continue independent authorized work;
end the turn when nothing useful remains outside the gate. Elapsed time is not approval.
Respect explicit preview-only, review, and other user-decision pauses.

Planning, local edits, tests, previews, dry runs, and read-only inspection do not need an
extra confirmation when already within the request. A sensitive subject can require
stronger review without making every local preparatory action a new approval gate.

## Review availability and route failure

This section is the common review authority for Codex modes. Review the complete
integrated change set once before acceptance, unless concrete risk requires earlier review.

- Comet and Singularity use clearly labeled Astra self-review, not independent review.
- Orbit, Event Horizon, Pulsar, Morph, and Constellation normally use a fresh exact Sol
  reviewer after integrated worker changes. Answer-only or no-change requests need no
  fresh reviewer. Use one concise workspace-write review-and-repair pass with no special
  isolation; the reviewer may repair bounded obvious issues and run affected checks.
- In Codex Orbit, Event Horizon, Pulsar, Morph, and Constellation, unavailable reviewer
  evidence permits clearly labeled Astra self-review unless the user or applicable policy
  requires independent review. Reject mismatched or inconsistent reviewer output; the
  same allowed self-review path may assess the actual change set itself, but cannot accept
  or relabel that rejected verdict.
- Hypernova always requires a fresh built-in reviewer on its exact Sol Ultra route.
  Hypernova, any explicit fresh-review requirement, and portable-host fresh-context requirements block acceptance
  until the required fresh route/context is verified. No self-review fallback applies.
- Do not request extra sandbox authorization, capture mutation fingerprints, or launch
  a second reviewer for a small direct repair unless an applicable policy requires it.
  Astra inspects the repair and reruns only affected checks. A substantial change to scope,
  architecture, or safety returns to Astra for a new decision.

Missing reviewer evidence and a known route mismatch are distinct. Neither permits a
silent model/effort substitution or a claim of independent review without evidence.
A blocked review stops acceptance, not independent authorized preparation. A reviewer
`ship` verdict means technical acceptance, not authorization or proof of publication.

## Proportionality checks

Follow YAGNI and use the smallest relevant checks. Long suites, persistent planning
documents, and extra review cycles need a repository rule, broad change surface, release
gate, or concrete unresolved risk.

Before adding a process step, ask:

1. Does it reduce a real risk in this request?
2. Will its output change the implementation or acceptance decision?
3. Is there a lighter way to obtain the same evidence?

Skip steps that do not improve the outcome, safety, or confidence.
