# Modes and risk guide

Use this guide when choosing a Project Pilot mode or deciding whether work needs user
confirmation or a fresh review.

## Mode summary

| Mode | Best for | Planning | Agent route | Review |
|---|---|---|---|---|
| Quick | Small, obvious, reversible work | Mental or one sentence | Sol High only | Sol High self-review |
| Guided | Normal project work | Compact work card | Luna XHigh or Terra XHigh for bounded execution | Fresh Sol High review after every worker-produced change |
| Careful | Consequential or explicitly thorough work | Visible plan | Strict pinned implementation lanes | Fresh Sol High review with observed read-only isolation |

Guided is the default. A user can simply say “Use Project Pilot” without learning the
mode system.

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

Use Guided. Every worker-produced change receives a fresh Sol High review. Answer-only
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
not the scope.

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

- Use the pinned Sol reviewer for Careful work and every Guided worker-produced change.
- If the exact reviewer role, model, or effort cannot be proven, stop and report the
  independent review as incomplete. Do not silently substitute self-review.
- If Careful mode requires hard read-only isolation and it cannot be observed, stop the
  review and report the limitation.
- Quick work and truly trivial answer-only Guided work may use a clearly labeled Sol High
  self-review because no independent implementation was performed.

## Proportionality checks

Before adding a process step, ask:

1. Does it reduce a real risk in this request?
2. Will its output change the implementation or acceptance decision?
3. Is there a lighter way to obtain the same evidence?

Skip steps that do not improve the outcome, safety, or confidence.
