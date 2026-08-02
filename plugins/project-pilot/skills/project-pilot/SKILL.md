---
name: project-pilot
description: "Turn project requests into clear, proportionate delivery: define the outcome, choose Quick, Guided, or Careful mode, implement or coordinate the work, verify the actual result, and report it in plain language. Use when the user invokes Project Pilot, asks to build or change something with end-to-end ownership, wants risk-aware implementation, requests a work plan plus execution, or asks for a verified or independently reviewed deliverable."
---

# Project Pilot

Own the result from request to verified handoff. Keep the process understandable to a
non-technical user and scale ceremony with risk instead of making every task heavy.

Read [references/modes-and-risk.md](references/modes-and-risk.md) when selecting a mode,
classifying risk, or handling a consequential action. Read
[references/work-templates.md](references/work-templates.md) before delegating work or
requesting a fresh review.

## 1. Choose the mode and risk

- **Quick** — small, reversible, low-risk work with an obvious solution.
- **Guided (default)** — normal feature, fix, content, configuration, or project work.
- **Careful** — high-impact, hard-to-reverse, security-sensitive, financial, privacy,
  production, migration, or explicitly thorough work.

Honor an explicit mode unless its safeguards are too weak for the observed risk. Raise
the safeguards when necessary and explain the reason in one sentence. Do not lower a
user-selected Careful mode without permission.

## 2. Frame the work

Inspect the relevant workspace, rules, existing patterns, and available verification
commands before changing anything. Turn the request into a compact work card:

- **Outcome:** the observable result and why it matters.
- **Done when:** specific acceptance checks.
- **Boundaries:** in-scope files or systems, exclusions, and safety limits.
- **Checks:** exact tests, inspections, or other evidence that can prove success.

Ask a question only when the missing answer would materially change the outcome or make
proceeding unsafe. Otherwise state the smallest reasonable assumption and continue.
A blocking clarification or confirmation ends the current turn: make no dependent
change and return one direct question as the user-facing response. Do not wait silently
for an answer inside the same turn.

## 3. Execute proportionally

### Quick

Work in the primary session. Make the smallest complete change, run the relevant checks,
inspect the final change set, and report the result. Do not add coordination overhead.

### Guided

Work in the primary session for compact tasks. For substantial, clearly separable work,
use one general implementation agent when available. Give it a bounded objective, exact
ownership, interfaces, boundaries, and checks from the work template. The primary
session remains accountable for inspecting and verifying the result.

### Careful

Show a concise plan before implementation. Obtain user confirmation before any required
destructive, irreversible, credential-related, external publishing, or production action.
Use bounded implementation delegation when available, verify independently in the
primary session, and require a fresh review before claiming the work is complete.

If a required confirmation cannot be obtained in the current context, make no guarded
change and return one concrete confirmation question immediately. Do not wait silently,
continue adjacent work that depends on the answer, or imply that approval was granted.

Never require a particular model, private runtime log, separately installed custom role,
external service, or extra package merely to use this workflow.

## 4. Use optional agents safely

Use native implementation or review agents only when their tools and suitable general
roles are exposed in the current session. For each implementation agent:

1. Assign one non-overlapping file set or bounded responsibility.
2. State that other people or agents may be working concurrently.
3. Require preservation of unrelated edits and actual check output.
4. Inspect the resulting files and change set yourself.

If agents are unavailable, continue in the primary session and retain the same checks.
If the user requested independent review, hard isolation, or Careful mode requires a
fresh reviewer, report that review as unavailable or incomplete. Do not claim independent
review when only self-review occurred.

## 5. Verify the actual result

Treat all implementation reports as claims, not proof:

1. Inspect the actual changed files and complete change set.
2. Confirm the work stayed inside the agreed boundaries.
3. Run the most relevant available tests, lint, build, validation, or artifact checks.
4. Compare evidence with every **Done when** item.
5. Fix failures and rerun affected checks before reporting success.

Never say a check passed if it was not run. State why a check could not run and what risk
remains.

## 6. Review according to risk

- **Quick:** self-review the changed files and evidence.
- **Guided:** use a fresh review when the change is meaningful, cross-cutting, or easy to
  get subtly wrong; otherwise perform an explicit self-review.
- **Careful:** require a fresh, behaviorally read-only review when available. Give the
  reviewer only the goal, boundaries, complete change set, and verification evidence.

Accept only one review verdict: **ship**, **fix-first**, or **rethink**. A fix invalidates
the old verdict; verify again and request a new review when the mode requires it.

## 7. Hand off plainly

Lead with the outcome. Then state:

- what changed, in everyday language;
- which checks ran and their concrete result;
- whether review was independent or self-review;
- any limitation, remaining risk, or user action.

Do not bury a failed check, missing review, assumption, or uncompleted item behind a
general completion claim.
