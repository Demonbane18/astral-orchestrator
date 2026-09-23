---
name: typesafe-session
description: Turn TypeSafe Jev judgments on or off for this Codex task, or report the current session state.
---

# TypeSafe session

Use the exact standalone user commands `TypeSafe on`, `TypeSafe off`, and `TypeSafe status`.
For task-by-task model and effort selection, use `Adaptive on typesafe`,
`Adaptive on openrouter`, `Adaptive off`, or `Adaptive status`. A provider must be
named whenever Adaptive turns on; it never switches providers automatically.
The trusted plugin hook records both settings independently for this Codex session and restores them after
compaction. The default is off. A project may opt in with `TypeSafe session: on` in its
root `AGENTS.md`; an explicit `TypeSafe off` overrides that for the rest of this session.
Adaptive always starts off for a new task. `TypeSafe off` does not turn Adaptive off,
and `Adaptive off` does not turn TypeSafe off.
When a trusted project or system instruction enables TypeSafe without that marker,
run the bundled `scripts/session.py set SESSION_ID PROJECT_ROOT on` helper once, using
the observed Codex session id and project root. Respect an explicit user off command
until the task ends.

When on, use TypeSafe only where semantic judgment helps. Keep candidate validation,
known rules, permissions, and execution in code. A missing key or failed call is visible;
never claim a Jev judgment occurred when it did not. The hook stores only the on/off
states, selected Adaptive provider, session id, and project path. It never receives
or saves an API key. Use `TYPESAFE_API_KEY` for direct TypeSafe or
`OPENROUTER_API_KEY` for OpenRouter, from a private project `.env.local` or process
environment. If both toggles are on, Astral makes one Jev request per worker card.

Codex must trust this plugin's hooks before automatic session persistence works. If
hooks are unavailable, disclose that limitation and use the user's current instruction
for this turn without claiming a persistent toggle.
