# Ares and OpenCodex compatibility

Astral's **Adaptive** feature selects an eligible worker model and effort once before
each delegated task. It uses either TypeSafe's direct Jev API or OpenRouter's Jev
Decisions API, chosen by `Adaptive on typesafe` or `Adaptive on openrouter`. It does
not alter the running primary. OpenCodex can carry the selected model request in
Codex CLI and Desktop; its catalog is checked before the worker is launched.

[Astra-Ares](https://github.com/miuuyy/Astra-Ares) solves a different problem. Its
patched Codex CLI has native checkpoints that can change the reasoning effort of
the **current** GPT-6 Astra, Sol, or Luna primary during a single-agent task. It
is a separate install and does not patch ordinary Codex Desktop. Astral's
`inspect-ares.py` maps its documented `Astra-Jev`, `Sol-Jev`, and `Luna-Jev`
selections, compares the observed primary route, and checks that Ares's configured
Jev provider matches Adaptive's selected provider. Astral's primary checker also
correlates Ares's logical rollout selection with a matching private decision log and
native `effort_selected` acknowledgment. A compatible configuration alone does not
prove Ares applied an effort; that correlated checkpoint evidence does.

Ares's current [architecture](https://github.com/miuuyy/Astra-Ares/blob/main/docs/architecture.md)
documents standard single-agent GPT-6 requests, with restrictions on compaction.
Its [configuration](https://github.com/miuuyy/Astra-Ares/blob/main/docs/configuration.md)
supports both `TYPESAFE_API_KEY` and `OPENROUTER_API_KEY`, without automatic provider
fallback. An OpenRouter key has not been configured in this project.

## Desktop boundary

Per-worker Adaptive selection is a normal Codex spawn request, so its Desktop
claim requires an observed Desktop worker with the requested model and effort.
OpenCodex's [sub-agent documentation](https://github.com/lidge-jun/opencodex/blob/main/docs-site/src/content/docs/guides/sub-agent-surface.md)
describes those explicit overrides. Ares's within-task primary effort change is
not established for Desktop merely because its model traffic reaches an HTTP
proxy. A Desktop bridge may ship only after an isolated run proves the applied
effort while preserving streaming, tool calls, approvals, cancellation, and resume
through OpenCodex. Until then, within-task Desktop adaptation is unsupported.

No integration step changes the user's OpenCodex service, global Codex settings,
catalog, Ares configuration, or credentials automatically.

## Local acceptance on 2026-09-23

An isolated Adaptive session made one live direct TypeSafe Choice/Score request
against the active OpenCodex catalog and selected GPT-6 Luna Low. A read-only
Codex CLI request through OpenCodex 2.63.0 and a separate Codex Desktop worker
probe both reported GPT-6 Luna at Low effort; the Desktop worker's primary checker
returned `match`. This proves that route on this host, not every model, effort, or
provider combination. OpenRouter live acceptance is pending because no OpenRouter
key is available.

Astra-Ares commit `a1dbc976103e300419cb0b4ab54150ad6a3e0b4b` passed its 38 provider
contract tests and built a separate patched Codex 0.155.0-alpha.9.2 in an isolated
temporary profile. Its direct TypeSafe `doctor --probe` passed. A read-only `Luna-Jev`
CLI task succeeded both with native OpenAI transport and through OpenCodex; the
private Ares log recorded GPT-6 Luna Low and `native_step_context_captured` in each
case. Inside a live Ares task, Astral's primary checker returned `match` with
`evidence_source: ares-native-checkpoint`. This validates the single-agent CLI path
for the tested route. OpenRouter Ares and Desktop Ares remain unverified.
