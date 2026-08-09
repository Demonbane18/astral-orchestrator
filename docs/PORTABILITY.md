# Portability boundary

Astral Orchestrator 3.3.0 ships two additive manifests in one package:

- `plugin.json` is the root Agent Plugins 1.0 manifest. It supplies portable package
  identity and lets compatible hosts discover the `skills/astral-orchestrator/SKILL.md`
  skill through the fixed `skills/` location.
- `.codex-plugin/plugin.json` remains the Codex/OpenAI manifest. It preserves the
  existing Codex interface metadata and fixed route integration.

The [Agent Plugins 1.0 specification](https://agent-plugins.org/specification) and its
[plugin manifest guide](https://agent-plugins.org/plugin-authors/manifest) standardize
skills and MCP discovery only, not agents, concurrency, model selection, or reasoning
effort. A root portable manifest therefore contains only
the closed metadata fields defined by its canonical schema; it does not declare Codex
interface or routing fields. The [skills guide](https://agent-plugins.org/plugin-authors/skills)
defines immediate `skills/*/SKILL.md` discovery, and the package verifier confirms that
each discovered skill resolves within the package rather than through a symlink escape.

## Host capabilities, not names

The [compatible-client directory](https://agent-plugins.org/compatible-clients) currently
lists VS Code, Cursor, GitHub Copilot, ChatGPT/Codex, and Kiro. It also says clients can
adopt component types incrementally. The list is evidence that those clients document
some Agent Plugins components; it is not evidence that every client supports Astral
Orchestrator’s model routing or multi-worker workflow.

On a non-Codex host, only an explicitly requested Morph or Constellation route may run.
Before doing so, Astral requires observable evidence of the capabilities the route needs:

- choosing a specific provider/model and reporting the actual selected provider/model;
- separate worker contexts for worker work and a fresh reviewer context;
- a requested-versus-actual effort value, when the host exposes effort;
- concurrent worker contexts for Constellation; and
- a fresh reviewer context distinct from the primary and workers.

If an exact model, effort, or fresh context cannot be observed, Astral does not label it
Sol, Luna, Terra, or “fresh.” Morph stops when its minimum worker/reviewer capabilities
are absent. An explicitly requested Constellation can instead use its documented serial
portable fallback only when the other required capabilities are proven; it never pretends
that serial work was concurrent.

Codex remains the only route in this package with fixed Sol/Luna/Terra profiles and
automatic local primary-route evidence. The portable package adds a discovery surface; it
does not change, weaken, or generalize those Codex guarantees.
