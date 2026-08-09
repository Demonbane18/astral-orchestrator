# Modes and risk guide

Use this guide when choosing an Astral Orchestrator mode or deciding whether work needs user
confirmation or a fresh review.

## Mode summary

| Mode | Best for | Planning | Agent route | Review |
|---|---|---|---|---|
| Quick | Small, obvious, reversible work | Mental or one sentence | Sol at configured effort | Sol self-review at configured effort |
| Guided | Normal project work | Compact work card | Luna or Terra at configured effort | Fresh Sol review at configured effort after every worker-produced change |
| Careful | Consequential or explicitly thorough work | Visible plan | Strict pinned implementation lanes at configured effort | Fresh Sol review at configured effort with observed read-only isolation |
| Measured (explicit opt-in) | A deliberately slower, evidence-oriented route decision | One frozen work card and named checks | Sol selects one pinned worker; Luna/Terra probes only for routing ambiguity | Fresh Sol review; high-risk work also uses Careful safeguards |
| Morph (explicit opt-in) | A bounded worker card that needs a user-selected routed model | Compact work card plus exact worker model and requested effort | Sol remains the configured primary; only the worker uses the explicit Morph route | Fresh exact Sol review at configured effort |
| Constellation (explicit opt-in) | Several independently owned, ready cards | Sol proves independence and capacity before a concurrent first wave | Cost-aware non-Sol workers by default; capacity-limited fan-out | One fresh exact Sol review after integrated verification |

Guided is the default. A user can simply say “Use Astral Orchestrator” without learning the
mode system. Measured is never auto-selected: use it only when the user explicitly names
it. It is intentionally slower and more model-intensive, so recommend Guided for normal
work.
Morph and Constellation are also explicit opt-in. They are never selected merely because another
model is available or because concurrent work would be convenient. Read their dedicated
references before using either mode.

On a non-Codex host, Quick, Guided, Careful, and Measured retain their documented modes but do
not acquire a generic replacement for their fixed Codex routes. Only explicitly selected Morph
or Constellation may use portable-host rules, and only after those capabilities are observed.

## Risk levels

### Low risk

Typical signs:

- Small documentation, copy, styling, or isolated configuration changes
- Easy rollback with no stored-data effect
- No authentication, authorization, secrets, personal data, money, or production access
- Clear existing pattern and focused verification

Use Quick when the task is also small and obvious. Otherwise use Guided.

### Medium risk

Typical signs:

- Normal application code or multi-file changes
- Public behavior changes with a bounded blast radius
- A bug whose root cause or regression surface needs investigation
- Moderate refactoring, dependencies, or integration work

Use Guided. Every worker-produced change receives a fresh Sol review at the configured
reviewer effort. Answer-only
or no-change Guided work may use a clearly labeled primary-session self-review.

### High risk

Typical signs:

- Authentication, authorization, security controls, credentials, or secrets
- Payments, financial calculations, legal or regulated behavior
- Personal, medical, confidential, or high-volume data
- Database migrations, destructive actions, irreversible conversions, or data deletion
- Production infrastructure, external publishing, or messages sent to other people
- Broad public interfaces, concurrency, cryptography, or a large blast radius

Use Careful even if the user asked for Quick. Explain that the risk raises the safeguards,
not the scope. High-risk Measured work keeps its evidence-oriented routing and also
inherits Careful confirmation and observed read-only isolation safeguards.
Careful safeguards override Morph or Constellation whenever the work has this level of risk: keep
the exact Sol primary and reviewer, use the required confirmation gates, and serialize any
card whose safety, interface, or verification depends on another card.

## User confirmation gate

Obtain user confirmation immediately before a destructive, irreversible, credential-related,
external publishing, or production action unless that exact action was already clearly
authorized in the current request. First resolve the specific target and explain the effect.

Ask one concrete question that names the target and effect. If confirmation cannot be
obtained in the current context, make no changes behind the gate.
Return the question immediately. Do not wait silently, assume approval, or continue work
that depends on it.

Planning, local edits, tests, previews, dry runs, and read-only inspection do not need an
extra confirmation when they are already within the request.

## Review availability and route failure

Fresh review means a separate agent context that did not implement the change and is
instructed to remain behaviorally read-only.

- Use the pinned Sol reviewer for Careful work and every Guided, Measured, Morph, or Constellation
  worker-produced change.
- If the exact reviewer role, model, or effort cannot be proven, stop and report the
  independent review as incomplete. Do not silently substitute self-review.
- If Careful mode, or high-risk Measured work, requires hard read-only isolation and it
  cannot be observed, stop the review and report the limitation.
- Quick work and truly trivial answer-only Guided work may use a clearly labeled Sol
  self-review at the configured orchestrator effort because no independent implementation
  was performed.

## Proportionality checks

Before adding a process step, ask:

1. Does it reduce a real risk in this request?
2. Will its output change the implementation or acceptance decision?
3. Is there a lighter way to obtain the same evidence?

Skip steps that do not improve the outcome, safety, or confidence.
