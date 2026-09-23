---
name: typesafe-session
description: Turn TypeSafe Jev judgments on or off for this Codex task, or report the current session state.
---

# TypeSafe session

Use the exact standalone user commands `TypeSafe on`, `TypeSafe off`, and `TypeSafe status`.
The trusted plugin hook records the setting for this Codex session and restores it after
compaction. The default is off. A project may opt in with `TypeSafe session: on` in its
root `AGENTS.md`; an explicit `TypeSafe off` overrides that for the rest of this session.

When on, use TypeSafe only where semantic judgment helps. Keep candidate validation,
known rules, permissions, and execution in code. A missing key or failed call is visible;
never claim a Jev judgment occurred when it did not. The hook stores only the on/off
state, session id, and project path. It never receives or saves an API key.

Codex must trust this plugin's hooks before automatic session persistence works. If
hooks are unavailable, disclose that limitation and use the user's current instruction
for this turn without claiming a persistent toggle.
