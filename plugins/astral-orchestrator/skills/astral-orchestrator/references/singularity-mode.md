# Singularity mode

Singularity is an **explicit opt-in** for meaningful low- or medium-risk work that is
larger than Comet but does not need multi-agent orchestration. It uses **one verified Sol
primary** at the configured orchestrator effort from start to finish. Never auto-select
Singularity: Orbit remains the default.

## Route and boundary

- Verify the Sol primary with the normal primary-session preflight before work starts.
- Singularity requires observed/verified Sol model and effort. If `check-primary.py`
  reports unavailable, unavailable evidence blocks Singularity; user confirmation cannot
  override that requirement. A `mismatch` or `invalid` result also blocks the route.
- Use the configured orchestrator effort; do not force Max or change global settings. A
  user who wants Sol Max must configure the orchestrator effort and **start a new task**.
- Do not spawn subagents, planning probes, worker lanes, or a fresh reviewer: there are
  **no subagents** and no fresh reviewer. Sol self-reviews once against the actual
  changes and observed evidence.
- If a higher-priority instruction requires delegation, report Singularity unavailable
  instead of pretending the one-session route ran.
- **Event Horizon overrides Singularity** for high-risk work. Keep Event Horizon confirmation gates,
  pinned lanes, and independent reviewer requirements.

## Token-disciplined execution

Create one compact work card with an objective, done conditions, non-goals, constraints,
and checks. Keep **no more than five active steps** and only one in progress. Load only
the context needed for the next decision; use native host planning or compaction when it
helps rather than introducing another process.

Use the **smallest sufficient intervention** in this order: answer or no change, existing
configuration or workflow, narrow edit, then new abstraction. Park detours outside the
card. Stop once DONE first passes and perform **one proportional verification pass**;
continue only when evidence is ambiguous, contradictory, or defective.

Use a compact Astral status panel with **only the Sol primary row**. Update it when there
is new evidence or state, not merely to repeat unchanged work.

## Evidence and provenance

Singularity adapts scope-control and verification patterns—one capable agent end to end,
limited active steps, smallest-sufficient intervention, and proportional verification—from
the external design reference at https://github.com/blavkgokuvnn/single-agent-skills
commit `7fc169557e84e0d27fe22e7d4fc2a6bffeefe4b2`. The external plugin and runtime are
not bundled or required. Astral has **no StateM dependency**.

A social-media claim of using 4% of a five-times plan over six hours and doubling speed
is **anecdotal**, unverified self-report. Astral does not promise it, claim to have
measured it, or treat it as outcome evidence.
