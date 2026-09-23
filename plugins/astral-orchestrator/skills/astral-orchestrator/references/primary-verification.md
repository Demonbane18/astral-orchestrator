# Primary verification

Use this reference on Codex before execution in any mode. Reuse matching evidence in the
same session unless the route, effort, settings, or host changes or the evidence becomes
uncertain. Comet and Singularity need no child preflight or work templates.

Before execution:

1. Resolve `../../scripts/configure-effort.py` from the skill directory and run
   `--show --json` to read effective worker settings. Then run the bundled
   `../../scripts/check-primary.py` without a strict flag. It accepts an observed
   `gpt-6-sol`, `gpt-6-luna`, or `gpt-6-astra` primary at the effort already running in the session.
   It does not compare the session with the saved orchestrator value or mutate settings.
   Optional `--require-sol-ultra` and `--require-astra-ultra` flags are strict diagnostics;
   no mode requires them.
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

Use the current runtime evidence and this published checker's detected-primary contract.
Do not change global settings or restart merely because older prose names one fixed primary.
If actual evidence fails preflight, report the mismatch and the supported corrective
options. A primary effort change applies when the user starts a new task at that effort,
not through Astral's saved worker settings.

Worker settings remain independent from primary effort. Astra may therefore run at a
higher configured worker effort than a Light or Medium Sol, Luna, or Astra primary. Before child
launch reuse unchanged effective settings,
or run `configure-effort.py --show --json` if they are not yet known. When an authorized
settings change is requested, preserve unspecified lanes and use `--reset` only if the
user asks for defaults. Never silently downgrade unsupported values.

A blocked primary stops dependent execution. Continue independent authorized work outside
that route where possible; never imply that the blocked mode completed.
