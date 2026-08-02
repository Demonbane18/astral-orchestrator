# Design review and improvements

## Executive assessment

Sol Advisor has strong engineering discipline: explicit role ownership, verification
of actual diffs, conflict-safe companion installation, and a fresh review gate. Its
main weakness for broad sharing is operational weight. The workflow assumes specific
model access, three separately installed custom-agent profiles, command-line tooling,
runtime metadata inspection, and a final fresh review even for tiny changes.

Project Pilot keeps the outcome-oriented parts and makes the guarantees proportional.
That is easier to install, explain, and maintain, but it intentionally gives up strict
proof that a particular model handled a particular role.

## What changed

| Area | Sol Advisor | Project Pilot | Why this is easier |
|---|---|---|---|
| Primary session | Requires a particular model and reasoning setting | Works with the current capable Codex session | No model picker prerequisite |
| Implementation | Two pinned custom-agent profiles | Primary session or optional native implementation help | No companion files to install |
| Review | A pinned custom reviewer for every deliverable | Risk-based fresh review; self-review is labeled honestly | Small work stays small |
| Preflight | Exact file, role, model, effort, and runtime checks | Workspace, scope, risk, and verification check | Focuses on user-visible correctness |
| Failure behavior | Stops when the required route cannot be proven | Falls back for routine work and clearly reports missing independence | More compatible across Codex versions |
| Dependencies | Separate installer and command-line JSON processing | Plugin-only runtime; setup and checks use common local tools | Fewer failure points |
| Language | Architecture and runtime terminology | Quick, Guided, Careful; Outcome, Done when, Boundaries, Checks | Explainable to non-technical users |
| Review isolation | Attempts to observe host sandbox behavior | Requires behavioral read-only review and never overclaims it | Portable, with an explicit limitation |

## Improvements made beyond simplification

1. **Proportional modes.** The user can ask normally, choose a simple mode, or let risk
   raise the safeguards automatically.
2. **Explicit confirmation boundary.** Destructive, irreversible, credential-related,
   external publishing, and production actions require clear authorization.
3. **Honest fallback semantics.** Self-review is never presented as independent review;
   Careful work remains review-incomplete when a fresh reviewer is unavailable.
4. **Beginner-complete lifecycle.** The README covers install, first use, mode choice,
   update, sharing, removal, and troubleshooting.
5. **No fake metadata.** Publisher URLs are omitted until a real public location exists.
6. **Portable contract tests.** Standard-library tests protect the packaging and safety
   promises without introducing a project build system.
7. **Clear derivative status.** The original copyright, license, source, and reviewed
   revision are preserved and easy to find.

## Tradeoffs

Project Pilot is the better default for general users, mixed Codex versions, and teams
that value a low-friction workflow. Sol Advisor remains the stronger choice when exact
model routing, reasoning settings, custom role files, and runtime-level routing evidence
are themselves requirements.

Project Pilot does not prove model identity or operating-system-enforced review isolation.
It proves what it can observe: the actual change set, verification output, review context,
and whether the review was fresh or self-performed.

## Recommended next improvements

### Before public sharing

1. Choose the final publisher name and GitHub repository.
2. Add the real repository and homepage fields to the plugin manifest.
3. Test remote installation from a clean Codex profile, not only a local checkout.
4. Tag the first release and keep version changes semantic.

### Usability follow-up

1. Observe three to five non-technical users installing and invoking the plugin.
2. Record where they hesitate; shorten those steps rather than adding more explanation.
3. Add a PowerShell setup helper if Windows users cannot rely on Codex-assisted install.
4. Add an optional logo and screenshots only after the workflow itself tests well.

### Advanced optional edition

If future plugin support can safely bundle custom roles, offer a separate advanced pack
with strict role pins and stronger isolation checks. Keep it opt-in so the basic plugin
does not regain the setup burden it was designed to remove.

## Forward-test evidence

The packaged skill was exercised in fresh agent contexts against disposable fixtures:

1. **Quick:** corrected exactly two spelling errors, verified only those substitutions,
   and labeled the handoff as self-reviewed.
2. **Guided:** added a small Python summary function plus focused tests, preserved the
   existing function, ran three passing tests, and reported the evidence plainly.
3. **Careful:** encountered a production-like reset script, preserved the existing data,
   and returned a confirmation question naming the exact file and replacement effect.

The first Careful run revealed that a blocked agent could wait too long before returning
control. The skill and risk guide now state that a blocking clarification ends the current
turn and must be returned immediately; a regression test protects that behavior.

## Source reviewed

- Repository: <https://github.com/DannyMac180/sol-advisor>
- Revision: `92f0fb105854e0fa606bdc98bfe688411e1db989`
- Review date: 2026-08-02
- License: MIT
