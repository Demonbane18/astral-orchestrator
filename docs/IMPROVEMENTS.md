# Design review and improvements

## Executive assessment

Astral Orchestrator v3.0 provides the model-routed workflow adapted from Sol Advisor:
one Sol orchestrator, two pinned implementation lanes, exact route evidence, bounded
ownership, independent verification, and a fresh pinned Sol reviewer.

The design focuses on usability without weakening the route contract. It keeps Quick,
Guided, and Careful language, uses namespaced profiles, gives non-technical users one
setup command, and refuses to silently downgrade a requested model or effort.

## Route comparison

| Area | Sol Advisor | Astral Orchestrator |
|---|---|---|
| Main session | Sol with high reasoning | Sol at configured effort; High by default |
| Focused lane | Luna with a pinned high reasoning setting | Luna at configured effort; XHigh by default |
| Context lane | Terra with a pinned high reasoning setting | Terra at configured effort; XHigh by default |
| Reviewer | Fresh Sol High, requested read-only | Fresh Sol at configured effort; High by default and requested read-only |
| Routing proof | Native metadata plus allowlisted rollout inspection | Same guarantee with a Python standard-library inspector |
| User controls | Architecture-oriented workflow | Quick, Guided, and Careful modes |
| Installation | Companion agent installer | Plugin setup plus conflict-safe profile installer |
| Removal | Manual profile cleanup | --remove deletes only exact, unmodified profiles |
| Failure | Stop when strict preflight fails | Same; never silently substitute another lane |
| Effort tuning | Profile-oriented | One command and persistent per-lane settings |

## Improvements beyond the original

1. **One beginner setup path.** sh scripts/setup.sh registers the marketplace, installs
   all three profiles, and installs the plugin.
2. **Safer lifecycle.** Existing different profiles are never overwritten, and modified
   profiles are never removed automatically.
3. **No extra JSON package.** The runtime inspector uses Python 3's standard library
   instead of requiring jq.
4. **Clear lane language.** Luna handles repeatable work; Terra handles context-heavy
   work; Sol retains requirements, architecture, integration, and acceptance.
5. **Proportional orchestration.** Quick avoids coordination overhead, while Guided and
   Careful use exact pinned routes.
6. **Honest host boundary.** The reviewer requests read-only access, records the
   effective sandbox, and does not overclaim host-enforced isolation.
7. **Host-compatible exact routing.** When native custom-agent selection is unavailable,
   a bundled launcher starts a fresh process with the same pinned model, configured
   effort, role instructions, and sandbox instead of falling back to a generic worker.
8. **Upgrade-resistant effort controls.** Users can tune all four lanes without editing
   profiles. Custom values force the exact-process route and unsupported values fail
   clearly instead of being downgraded.

## Version 3 identity migration

Version 3.0.0 is intentionally breaking: it renames the former Project Pilot package to
Astral Orchestrator. The plugin and marketplace name are astral-orchestrator, TOML agent
names use astral_orchestrator, launcher proof starts with ASTRAL_ORCHESTRATOR_ROUTE, and
settings now persist at ~/.codex/astral-orchestrator/effort-levels.toml.

The new repository home is https://github.com/Demonbane18/astral-orchestrator. The former
settings file is not silently imported because it belongs to a different profile
namespace. The migration instructions in README and CHANGELOG make the required user
action explicit.

## Tradeoffs

Strict routing requires recipients to have all three models and to start a new task after
profile installation. This is less portable than generic delegation, but it directly
satisfies the requirement for a real model-routed orchestrator.

Runtime rollout formats are host implementation details and may change. The inspector
therefore rejects missing or inconsistent fields instead of guessing, and the skill
prefers trustworthy launch metadata when the host exposes every required field.

## Recommended next improvements

1. Test installation from a clean Codex profile and a remote GitHub checkout.
2. Confirm all three models are available to the intended recipients.
3. Add a PowerShell installer if Windows recipients need it.
4. Prefer public spawn metadata over rollout inspection when the host exposes every
   required field consistently.

## Historical validation evidence

The former Project Pilot 2.1 release candidate passed 23 repository contract tests,
package verification, setup dry-run, whitespace checks, and the official Codex skill and
plugin validators. The tests covered exact profile pins, conflict-safe installation and
removal, allowlisted runtime evidence, exact-process command construction, bounded prompt
handling, per-lane effort configuration and validation, route selection, confirmation
boundaries, and beginner documentation.

Forward testing on Codex CLI 0.144.5 showed why the compatibility route is necessary: a
generic subagent given a Luna-looking task name still ran Sol High, and the package
rejected that result. Separate launcher sessions then proved Luna XHigh with
workspace-write, Terra XHigh with workspace-write, and Sol High with read-only review.

## Source reviewed

- Repository: https://github.com/DannyMac180/sol-advisor
- Revision: 92f0fb105854e0fa606bdc98bfe688411e1db989
- Review date: 2026-08-02
- License: MIT
