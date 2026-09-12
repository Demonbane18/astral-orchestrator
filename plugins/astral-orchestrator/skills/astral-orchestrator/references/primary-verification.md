# Primary verification

Use this reference on Codex before execution in any mode. Reuse matching evidence in the
same session unless the route, effort, settings, or host changes or the evidence becomes
uncertain. Comet and Singularity need no child preflight or work templates.

Before execution:

1. Resolve `../../scripts/configure-effort.py` from the skill directory and run
   `--show --json` to read effective settings. Then run the bundled
   `../../scripts/check-primary.py`. For Hypernova add `--require-astra-ultra`;
   `--require-sol-ultra` remains its compatibility alias. These checks do not mutate
   settings. Normal modes require observed `gpt-6-astra` effort to equal the configured
   orchestrator effort; Hypernova requires observed Astra Ultra independently of normal
   saved defaults.
   The optional `--thread-id` defaults to `CODEX_THREAD_ID`. Use `--sessions-dir` only
   for local test evidence. The checker uses the bundled runtime inspector and emits
   allowlisted JSON, not raw rollout contents.
   `unavailable` may use one explicit user confirmation outside Singularity and Hypernova;
   label that evidence user-confirmed, not observed. Singularity and Hypernova require
   observed model/effort: user confirmation cannot satisfy or override that requirement.
   `mismatch` or `invalid` blocks the route; manual confirmation cannot waive either.
2. Read applicable workspace instructions and inspect the current change state.
3. Define the requested outcome, boundaries, acceptance conditions, and relevant checks.
4. Identify user confirmations required before consequential actions.

Use the current runtime evidence and this published checker's configured-effort contract.
Do not change global settings or restart merely because older prose names Sol as primary.
If actual evidence fails preflight, report the mismatch and the supported corrective
options; do not claim that saved defaults are ignored. An explicitly requested primary
setting change applies to a new task, not the one already running.

Worker settings remain independent. Before child launch reuse unchanged effective settings,
or run `configure-effort.py --show --json` if they are not yet known. When an authorized
settings change is requested, preserve unspecified lanes and use `--reset` only if the
user asks for defaults. Never silently downgrade unsupported values.

A blocked primary stops dependent execution. Continue independent authorized work outside
that route where possible; never imply that the blocked mode completed.
