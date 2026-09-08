![Animated outer-space Astral Orchestrator banner with Sol at the center, Luna and Terra orbiting, twinkling stars, and a passing comet.](assets/brand/astral-orchestrator-banner.gif)

# Astral Orchestrator

Astral Orchestrator v3.10.0 is an installable, open-source Codex plugin that turns a goal
into routed, verified work. Astra keeps the plan and final decisions, Astral coordinates
the right model and effort for each bounded task, and checks run before handoff.

Version 3.10.0 accepts the selected Astra effort in every mode, including Hypernova.
A Light or Medium primary can launch explicitly selected Astra Max or Ultra workers.
Hypernova keeps Sol Ultra children as its default. Route checks and fresh review remain.

Astral Orchestrator is an independent open-source project. It is not affiliated with or
endorsed by OpenAI.

## Quick Install

From a terminal where Codex is available, run exactly these two commands:

```sh
codex plugin marketplace add Demonbane18/astral-orchestrator --ref main
codex plugin add astral-orchestrator@astral-orchestrator
```

Start a new Codex task after installation so Codex can discover the plugin.

## Requirements

- A current Codex CLI or desktop app with plugins enabled.
- Access to `gpt-6-astra`, `gpt-5.6-sol`, `gpt-5.6-luna`, and `gpt-5.6-terra` for their fixed routes.
- Python 3.11 or newer; Astral's local tools use only the standard library.
- For Hypernova only: native multi-agent controls and `gpt-5.6-sol` with Ultra effort.

Astral stops when an exact required model, effort, or route cannot be proven. It never
silently substitutes a different one, and model availability depends on your account.

## First use

Open a new Codex task and say:

```text
Use Astral Orchestrator to add a search box and verify the result.
```

Orbit is the recommended default. Name another mode only when you want its specific
workflow.

## Eight modes

| Mode | Best for | Route in brief |
|---|---|---|
| Comet | Tiny, obvious, reversible work | Sol completes the change directly and self-reviews. |
| Orbit (default) | Normal changes and projects | Sol plans, Luna or Terra implements bounded work, and fresh Sol reviews. |
| Event Horizon | High-risk or hard-to-reverse work | Necessary confirmation gates, targeted checks, and one fresh review-and-repair pass. |
| Singularity (opt-in) | Meaningful work suited to one session | One verified Sol completes and self-reviews a compact card; no subagents. |
| Pulsar (opt-in) | Deliberately evidence-oriented work | Sol freezes one card and acceptance checks, then records non-secret route evidence. |
| Morph (opt-in) | A bounded card needing a selected worker model | Sol stays primary and reviewer while the chosen worker route is proven. |
| Constellation (opt-in) | Several independent, ready cards | Work fans out only within observed capacity, then Sol integrates and reviews it. |
| Hypernova (opt-in) | Maximum throughput when speed matters more than token efficiency | An observed Sol Ultra primary launches independent built-in Sol Ultra workers and requires a fresh Sol Ultra reviewer. |

Hypernova is Codex-native, performance-first, and never automatic. It requires the exact
native route for every lane and has no process, portable, lower-effort, alternate-model,
self-review, or serial fallback. Dependent or safety-sensitive cards may still be
sequenced within that exact native route; dependency scheduling is not a fallback.
High-risk Hypernova work inherits Event Horizon's confirmation and authorization gates;
“go nuts” never bypasses safety or scope.

Legacy prompts still map Quick to Comet, Guided to Orbit, Careful to Event Horizon, and
Measured to Pulsar.

## Safety and privacy

- Astral does not broaden your request or authorize publishing, deployment, credentials,
  destructive actions, or other consequential external changes.
- Risk can raise safeguards, but a mode name cannot lower required safeguards.
- The plugin adds no API key, analytics, background service, or paid runtime dependency.
- External providers selected through Morph may process that bounded work under their own
  terms; Astral does not configure or operate them.

Read the full [Safety and privacy guide](https://astral-orchestrator.vercel.app/docs/safety/).

## Update

The installed Codex CLI verifies this marketplace update flow:

```sh
codex plugin marketplace upgrade astral-orchestrator
codex plugin add astral-orchestrator@astral-orchestrator
```

Start a new Codex task after updating.

## Documentation

Start at the [documentation home](https://astral-orchestrator.vercel.app/docs/), then use
the focused guides:

- [Getting started](https://astral-orchestrator.vercel.app/docs/getting-started/)
- [Modes](https://astral-orchestrator.vercel.app/docs/modes/)
- [Routing and runtime](https://astral-orchestrator.vercel.app/docs/routing/)
- [Safety and privacy](https://astral-orchestrator.vercel.app/docs/safety/)
- [Evidence and benchmarks](https://astral-orchestrator.vercel.app/docs/evidence/)
- [Maintenance](https://astral-orchestrator.vercel.app/docs/maintenance/)
- [Contributing](https://astral-orchestrator.vercel.app/docs/contributing/)

For help or policies, see [Support](https://astral-orchestrator.vercel.app/support/),
[Privacy](https://astral-orchestrator.vercel.app/privacy/), and
[Terms](https://astral-orchestrator.vercel.app/terms/).

## Contributing

Run the essential checks from the repository root:

```sh
python3 -m unittest discover -s tests -v
sh plugins/astral-orchestrator/scripts/verify.sh
```

See the [contributing guide](https://astral-orchestrator.vercel.app/docs/contributing/)
for validation, packaging, and release details. Do not push, publish, deploy, or change a
user's global Codex configuration without explicit authorization.

## License and attribution

Astral Orchestrator is distributed under the [MIT License](LICENSE). It independently
adapts ideas from [Sol Advisor](https://github.com/DannyMac180/sol-advisor) at revision
`92f0fb105854e0fa606bdc98bfe688411e1db989`. The original copyright and MIT notice are
preserved in [NOTICE.md](NOTICE.md) and [LICENSE](LICENSE).
