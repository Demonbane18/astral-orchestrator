---
name: run-astral-benchmark
description: Run and interpret this repository's unattended Astral Orchestrator comparison harness. Use when a user asks to benchmark Astral against single-Sol, measure token, time, or quality efficiency, run the quick benchmark, or explicitly run the full benchmark.
---

# Run Astral Benchmark

Use `benchmarks/run_pilot.py` to compare single-Sol with Astral Guided under frozen task instructions, isolated worktrees, objective checks, and blinded scoring. Default to the quick profile so an exploratory comparison cannot accidentally launch the expensive full study.

## Choose the profile

- Use `quick` unless the user explicitly asks for the full or decision-grade benchmark. Quick uses one frozen case, one repetition, single-Sol XHigh and Astral Guided: two strategy trials with a 30-minute cap. It deliberately omits Max and provides directional evidence only.
- Use `full` only after explicit user authorization. Full uses four frozen cases, two randomized repetitions, and attempts exact single-Sol Max after preflight. It is capped at 24 strategy trials and two hours.
- Never silently upgrade quick to full, add repetitions, or retry a costly failed run.

## Preflight

1. Run the repository tests and package verification if the harness changed.
2. Resolve a full commit ID for `--base-ref`. Do not benchmark a moving worktree.
3. Choose a new, empty output directory. The runner refuses a non-empty directory so evidence from separate runs cannot be mixed.
4. Do not change global Codex configuration, push, publish, or access production systems.

Preview either plan without model calls:

```sh
python3 benchmarks/run_pilot.py --profile quick --dry-run --output-dir /tmp/astral-quick-preview
python3 benchmarks/run_pilot.py --profile full --dry-run --output-dir /tmp/astral-full-preview
```

## Run

Quick:

```sh
python3 benchmarks/run_pilot.py \
  --profile quick \
  --base-ref <full-commit-id> \
  --output-dir <new-output-directory>
```

Full, only when explicitly requested:

```sh
python3 benchmarks/run_pilot.py \
  --profile full \
  --base-ref <full-commit-id> \
  --output-dir <new-output-directory>
```

If one trial fails, keep its failure record and continue safely. If the run-level cap is reached, stop. Do not fabricate telemetry, replace missing values with zero, or substitute a different model or effort.

## Interpret and report

Verify that the output directory contains:

- `run-manifest.json`
- `trials.jsonl`
- `scorecard.json`
- `preview.html`
- opaque patch artifacts for completed trials

Report objective acceptance before blind judge scores. Include route correctness, observed tokens, elapsed time, confidence intervals, quality per 10,000 strategy tokens, quality per elapsed minute, failures, and limitations. Keep missing telemetry as `null`/`n/a`.

The quick profile is a smoke comparison, not proof of superiority. The full profile is still a local repository study and is not automatically product-wide evidence.

If a reviewer verdict is `fix-first` or `rethink`, label the evidence invalid or exploratory and return control to the user. Never automatically launch another costly benchmark to replace it.
