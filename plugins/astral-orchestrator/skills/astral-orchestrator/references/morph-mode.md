# Morph mode

Morph is an explicit opt-in: use it only when the user explicitly names it. Morph keeps the configured
`gpt-5.6-sol` Sol primary responsible for requirements, architecture, decomposition,
integration, verification, and the final decision. The normal exact Sol reviewer remains
required. Only a bounded worker card may use a user-selected model.

## Codex route: before launch

1. Complete the normal primary preflight and prove the configured Sol primary. Morph does
   not enable a non-Sol primary or a non-Sol final reviewer.
2. Record one private worker card with its exact ownership, exact `provider/model` or
   native model identifier, and requested effort. Keep non-overlapping work serial unless
   the user also explicitly selects Constellation.
3. Resolve `../../scripts/run-morph-agent.py`, write the card to a private regular file,
   and require a successful dry run:

   ```text
   python3 run-morph-agent.py --model <provider/model> --effort <label> \
     --workdir <workspace> --prompt-file <private-card> --dry-run
   ```

   The dry run selects a compatible Codex runtime and runs `codex features list` so the
   active user configuration and model catalog must parse before launch. It does not send
   the private card to a model. Astral checks an explicit `ASTRAL_CODEX_PATH` override,
   the host's `CODEX_CLI_PATH` hint, known installed app/runtime locations, and finally
   the current `codex` command. Each path must be absolute, executable, and a regular
   file. If every candidate fails, stop and report the sanitized candidate-source errors;
   do not edit the user's configuration or catalog.

4. Start the same command without `--dry-run` only after the card is ready. It launches
   `codex exec` with the exact worker model, requested effort, and workspace-write
   sandbox. Capture its `ASTRAL_ORCHESTRATOR_ROUTE` evidence, process identity, exit
   status, and actual result. A launch or runtime failure blocks that worker; do not
   substitute a different worker silently.
5. After the process exits, including a non-zero exit, remove only that exact private
   packet. Do not use a broad or recursive deletion, and do not remove any other packet
   or user file.

The evidence labels the requested effort separately from upstream-native effort and also
records the selected runtime source, its allowlisted version, and a passing configuration
probe. It never includes the executable path, environment values, configuration contents,
credentials, or private packet. An accepted effort label is **requested-only** and does
not verify upstream-native effort semantics. Depending on the configured provider and
model, effort can be native, mapped, clamped, emulated, or absent. Do not call it native
unless independent upstream evidence proves that fact.

## OpenCodex boundary

OpenCodex is optional and independently installed and configured by the user. Astral
never modifies ~/.opencodex, starts services, installs packages, handles provider
credentials, rewrites `$CODEX_HOME/config.toml` or a model catalog, or assumes provider
terms-of-service compatibility. It adds no network dependency: the launcher invokes only
a compatible runtime from the user's existing Codex installation.

Provider/model support and effort semantics are capability-dependent. A user must wire an
OpenCodex provider route to Codex separately before Morph can use it. If the provider,
model, requested effort, or process route fails at runtime, stop that worker and report
the smallest corrective action; do not claim that Morph completed.

A user-configured external or non-OpenAI provider can receive the worker packet as part of
model inference. “No network dependency” means Astral adds no network client, service, or
credential handling; it does not mean provider traffic or model inference is local.

## Portable-host route

On a non-Codex host, first read `portable-hosts.md`. Do not run `run-morph-agent.py`,
`check-primary.py`, or use a Codex agent name. The host must expose an observed separate
worker context, actual provider/model selection, and a separate fresh reviewer context.
Record actual and requested provider, model, and effort separately. A requested effort is
not evidence that the provider accepted or natively supported it.

Give the external or non-OpenAI worker only its bounded private packet; it must perform the
card directly and must not spawn or delegate. It may receive the packet as part of provider
inference, so say that plainly. After the worker exits, including a failure, remove only that
exact private packet with a narrow host operation. If any required capability is absent or
unobservable, stop rather than attempting a Codex fallback or claiming a fixed Astral lane.

## Review and risk

After a Morph worker changes anything, Sol integrates and verifies the actual change set,
then starts a new exact fresh Sol reviewer using the normal route. Event Horizon safeguards
override Morph whenever risk requires confirmation, observed read-only review isolation,
or serial routing. Morph never changes those requirements.
