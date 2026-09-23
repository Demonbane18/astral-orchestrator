# Later: Astra-Ares with Astral Orchestrator

This is a separate follow-up after Astral Orchestrator v3.12.0. It does not change the current release or its TypeSafe worker selector.

## What already exists

[Astra-Ares](https://github.com/miuuyy/Astra-Ares) runs a separate, patched Codex CLI for adaptive **GPT-6 Astra reasoning effort**. Its [provider configuration](https://github.com/miuuyy/Astra-Ares/blob/main/docs/configuration.md) already offers `openrouter` with `OPENROUTER_API_KEY` and `typesafe` with `TYPESAFE_API_KEY`. Provider switching is explicit. The repository says OpenRouter has a funded-key live test; its direct TypeSafe adapter has contract tests but no live acceptance. Its README says the normal Codex Desktop app remains unchanged by installation.

Astral v3.12 uses Jev to choose an eligible **worker route** before delegation. Ares uses Jev to adjust **Astra reasoning effort** during a running CLI task. These are separate decisions and should stay separate in the integration.

## CLI integration experiment

1. Install Ares into an isolated test environment, keeping the existing Codex executable and profile intact. Record the Ares commit and patched Codex version.
2. Configure each provider separately using its existing private configuration or environment-variable route. Never copy keys into Astral's plugin package, Git, logs, or Vercel. Run `ares doctor`; run the small billable `ares doctor --probe` only with a funded key and an explicit test budget.
3. Start `astra-ares` with an Astral-enabled test project and select Astra-Jev as the primary. Confirm Ares reports a native effort application, and Astral observes the *current* primary effort without changing its model. Test one bounded Astral worker card, then a fresh review, with fixed child routes and existing permission gates.
4. Repeat under both TypeSafe and OpenRouter, and test missing key, provider error, uncertain Jev result, session restart, and explicit TypeSafe off. Measure cost, latency, applied effort, and route evidence without retaining raw task text or secrets in the experiment report.

## Desktop feasibility experiment

Do not assume a CLI patch reaches Codex Desktop. First identify which executable and configuration Desktop actually uses. Ares documents a separate patched CLI; [Codex configuration](https://learn.chatgpt.com/docs/config-file/config-reference) has custom model-provider `base_url` and `env_key` fields, but a configurable endpoint alone does not prove Desktop can apply Ares's native per-generation effort changes.

Test a local proxy only after documenting its exact trust boundary and protocol: OpenAI Responses-compatible model traffic, authentication, streaming/tool calls, approvals, cancellation, and session resume. The TypeSafe/OpenRouter key in Ares is for Jev decisions, not automatically an inference credential. Compare a Desktop run against the CLI's confirmed `APPLIED` effort evidence. If Desktop cannot route its process through the patched client or cannot prove native effort application, publish the integration as **CLI only** and keep Desktop support explicitly unverified. Do not alter the user's global Codex settings or active Desktop profile during this experiment.

## Completion criteria

- Both key providers work through Ares with observed Jev decisions and native effort application, or each failure is reported precisely.
- Astral's primary, child route, reviewer, permission, and TypeSafe session contracts remain intact.
- A Desktop claim requires a real Desktop task showing the requested and applied effort; a proxy health check alone is insufficient.
- Installation, rollback, credential handling, and supported surfaces are documented from the observed result.
