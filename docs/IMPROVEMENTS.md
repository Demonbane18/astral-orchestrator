# Design review and improvements

## Executive assessment

Project Pilot v2 now provides the core behavior the original Sol Advisor is built for:
one strong orchestrator, two model-pinned implementation lanes, exact route evidence,
bounded ownership, independent verification, and a fresh model-pinned reviewer.

The customization is mainly about usability. Project Pilot keeps Quick, Guided, and
Careful language, uses namespaced profiles, gives non-technical users one setup command,
and adds conflict-safe removal. It does not silently downgrade when the requested route
is missing.

## Route comparison

| Area | Sol Advisor | Project Pilot v2 |
|---|---|---|
| Main session | Sol with high reasoning | Sol High, verified before Guided/Careful work |
| Focused lane | Luna with a pinned high reasoning setting | Luna XHigh for repeatable, fully specified work |
| Context lane | Terra with a pinned high reasoning setting | Terra XHigh for context-heavy implementation |
| Reviewer | Fresh Sol High, requested read-only | Fresh Sol High, requested read-only |
| Routing proof | Native metadata plus allowlisted rollout inspection | Same guarantee with a Python standard-library inspector |
| User controls | Architecture-oriented workflow | Quick, Guided, Careful modes |
| Installation | Companion agent installer | Plugin setup plus conflict-safe profile installer |
| Removal | Manual profile cleanup | `--remove` deletes only exact unmodified profiles |
| Failure | Stop when strict preflight fails | Same; never silently substitute another lane |

## Improvements beyond the original

1. **One beginner setup path.** `sh scripts/setup.sh` registers the marketplace,
   installs all three profiles, and installs the plugin.
2. **Safer lifecycle.** Existing different profiles are never overwritten, and modified
   profiles are never removed automatically.
3. **No extra JSON package.** The runtime inspector uses Python 3's standard library
   instead of requiring `jq`.
4. **Clear lane language.** Luna handles repeatable work; Terra handles context-heavy
   work; Sol retains requirements, architecture, integration, and acceptance.
5. **Proportional orchestration.** Quick intentionally avoids coordination overhead,
   while Guided and Careful use exact pinned routes.
6. **Honest host boundary.** The reviewer requests read-only access, but Project Pilot
   records the effective sandbox and does not overclaim host-enforced isolation.
7. **Host-compatible exact routing.** When a Codex build cannot select native custom
   agents, a bundled launcher starts a fresh process with the same pinned model, effort,
   role instructions, and sandbox instead of falling back to a generic worker.

## Tradeoffs

Strict routing requires recipients to have all three models and to start a new task after
profile installation. That is less portable than Project Pilot v1's generic fallback,
but it directly satisfies the requirement for a real model-routed orchestrator.

Runtime rollout formats are host implementation details and may change. The inspector
therefore rejects missing or inconsistent fields instead of guessing, and the skill can
prefer trustworthy launch metadata when Codex exposes it directly.

## Recommended next improvements

### Before public sharing

1. Choose the final publisher name and GitHub repository.
2. Test installation from a clean Codex profile and a remote GitHub checkout.
3. Confirm all three models are available to the intended recipients.
4. Tag v2.0.0 and keep future version changes semantic.

### Usability follow-up

1. Test setup and first use with three to five non-technical users.
2. Add a PowerShell installer if Windows recipients need a terminal-free path.
3. Add a small status command that explains missing profiles in plain language.
4. Prefer public spawn metadata over rollout inspection when the host exposes every
   required field consistently.

## Validation evidence

The 2026-08-02 release candidate passed 19 repository contract tests, package
verification, setup dry-run, whitespace checks, and the official Codex skill and plugin
validators. The tests cover exact profile pins, conflict-safe installation and removal,
allowlisted runtime evidence, exact-process command construction, bounded prompt
handling, route selection, confirmation boundaries, and beginner documentation.

Forward testing on Codex CLI 0.144.5 showed why the compatibility route is necessary: a
generic subagent given a Luna-looking task name still ran Sol High. Project Pilot rejected
that result. Separate launcher sessions then proved Luna XHigh with workspace-write
(`019fc049-9034-7b33-bf08-1619c8e6b053`), Terra XHigh with workspace-write
(`019fc04c-42b7-7fc0-91df-2d6f10e36677`), and Sol High with read-only review. The final
fresh Sol High review (`019fc05a-b89d-7fb2-91c9-2960cb3f3077`) returned `ship`.

The locally installed cache is `2.0.0+codex.20260802025027`. Its launcher, skill, and
routing guide byte-match the reviewed source; all three installed profiles also match
their shipped files exactly.

## Source reviewed

- Repository: <https://github.com/DannyMac180/sol-advisor>
- Revision: `92f0fb105854e0fa606bdc98bfe688411e1db989`
- Review date: 2026-08-02
- License: MIT
