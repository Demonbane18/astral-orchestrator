# Benchmarks

Astral publishes two deliberately separate kinds of evidence. The
[instruction-context footprint](context-footprint-2026-08-04.json) measures the static
instruction files loaded for named paths. The local outcome scorecard below compares
recorded runs. Neither substitutes for the other.

## Instruction-context footprint

The committed v3.2.0 measurement used `tiktoken` 0.13.0 and its `o200k_base` encoding
on 2026-08-04. It preserves the legacy core, Quick, full, and quick-vs-full fields, and
adds Guided (the same four-file full bundle) and explicit Measured (which adds its own
reference). Historical 2026-08-03 evidence remains unchanged.

This is an instruction-context loading measurement only. It does not measure task
quality, latency, price, or total token usage for a complete run, so it does not prove
that every multi-agent run uses fewer total tokens than single Sol.

`tiktoken` is optional contributor tooling, not a plugin or runtime dependency. With
[`uv`](https://docs.astral.sh/uv/), regenerate and verify the exact evidence from the
repository root:

```sh
uv run --no-project --with tiktoken==0.13.0 python benchmarks/measure_instruction_context.py --check benchmarks/context-footprint-2026-08-04.json
```

The command exits non-zero if the tokenizer version, measured instruction files, hashes,
or recorded counts no longer match. Run the same command without `--check` to print a
fresh JSON measurement for review.

## Local outcome scorecard

Use this guide to compare an Astral multi-agent run with a single-Sol control for the
same task cases. The scorecard is local: it reads the JSONL file you create, uses only
Python's standard library, and never starts Codex, sends data, or collects analytics.

## Design a fair comparison

For each task case, freeze the task packet and acceptance definition before running
either strategy. Give the control and Astral run the same `case_id`,
`case_fingerprint`, trial number, and acceptance-check identifiers. The fingerprint can
be a SHA-256 digest of the frozen task packet or another stable revision label; it lets
you compare private tasks without placing their contents in the report.

Run every case repeatedly. The command requires at least two trials per strategy and
case by default; use more for results you intend to rely on. Alternate or randomize run
order when possible, keep the environment as similar as you can, and evaluate both
outputs with identical acceptance checks. When people assign an optional quality score,
hide the strategy name from them where practical and record whether the score was
blinded.

Freeze route settings within each case and strategy across its repetitions: the same
route roles, models, expected efforts, and observed efforts are required. The
single-Sol control and Astral treatment may intentionally use different route settings;
the scorecard compares their outcomes, not identical model configurations.

The control is `single-sol`: one Sol route. The treatment is `astral`: an orchestrator,
at least one Luna or Terra worker, and a fresh Sol reviewer. Record observed route facts
for every lane rather than assuming that a task label proves its model or effort.

## Record schema

The input is UTF-8 JSON Lines (JSONL): one complete JSON object per line. Schema version
`1` has these required fields:

| Field | Meaning |
|---|---|
| `schema_version` | Always `1`. |
| `trial_id` | Globally unique identifier for this attempt. |
| `case_id` / `case_fingerprint` | The stable task-case name and its frozen revision identifier. |
| `trial` | Positive repeated-trial number, matched between the two strategies. |
| `strategy` | Exactly `single-sol` or `astral`. |
| `acceptance_checks` | Non-empty, unique identifiers for checks run for this case. The same set is required for its paired control and Astral record. |
| `accepted` | Whether the final output passed those checks. |
| `first_pass_accepted` | Whether it passed before any rework. It cannot be true when `accepted` is false. |
| `rework_required` | Whether the first output needed rework. It cannot be true with first-pass acceptance. |
| `wall_time_seconds` | Non-negative wall-clock duration for the full strategy run. |
| `model_calls` | Number of model calls used by the run (at least one and never fewer than its route-evidence entries). It may be higher when a recorded lane made multiple calls. |
| `route_evidence` | One or more route-evidence objects, described below. |

Optional fields are `input_tokens`, `output_tokens`, `quality_score`, and
`quality_score_blinded`. Token fields must be non-negative numbers. `quality_score` is
a 0–100 number and requires the boolean `quality_score_blinded`. For a fair aggregate,
the scorecard accepts an optional metric only when it is recorded for every trial; omit
it from every line if you cannot collect it consistently.

Each `route_evidence` object has exactly these fields:

```json
{
  "role": "terra",
  "model": "gpt-5.6-terra",
  "effort": "xhigh",
  "expected_effort": "xhigh",
  "task_id": "observed-task-or-session-id"
}
```

`role` is one of `single-sol`, `orchestrator`, `luna`, `terra`, or `reviewer`.
`effort` is the observed value and `expected_effort` is the per-lane setting used for
that run. The scorecard marks a route correct only when its observed model matches the
role and its effort matches the expected value. A single-Sol record needs exactly one
`single-sol` route. An Astral record needs an orchestrator, a Luna or Terra worker, and
a reviewer, with distinct task or session IDs. This detects route deviations without
claiming to prove fields that were never recorded. Every task or session ID must also be
globally unique across the complete JSONL file, not only within an Astral trial.

## Minimal valid example

This one-case example has the required two repetitions. Use more cases and repetitions
before treating a result as decision-grade evidence.

```jsonl
{"schema_version":1,"trial_id":"search-sol-1","case_id":"search","case_fingerprint":"search-v1","trial":1,"strategy":"single-sol","acceptance_checks":["unit-tests","manual-review"],"accepted":true,"first_pass_accepted":true,"rework_required":false,"wall_time_seconds":42,"model_calls":1,"route_evidence":[{"role":"single-sol","model":"gpt-5.6-sol","effort":"high","expected_effort":"high","task_id":"sol-1"}]}
{"schema_version":1,"trial_id":"search-astral-1","case_id":"search","case_fingerprint":"search-v1","trial":1,"strategy":"astral","acceptance_checks":["manual-review","unit-tests"],"accepted":true,"first_pass_accepted":true,"rework_required":false,"wall_time_seconds":61,"model_calls":3,"route_evidence":[{"role":"orchestrator","model":"gpt-5.6-sol","effort":"high","expected_effort":"high","task_id":"lead-1"},{"role":"terra","model":"gpt-5.6-terra","effort":"xhigh","expected_effort":"xhigh","task_id":"worker-1"},{"role":"reviewer","model":"gpt-5.6-sol","effort":"high","expected_effort":"high","task_id":"review-1"}]}
{"schema_version":1,"trial_id":"search-sol-2","case_id":"search","case_fingerprint":"search-v1","trial":2,"strategy":"single-sol","acceptance_checks":["unit-tests","manual-review"],"accepted":true,"first_pass_accepted":true,"rework_required":false,"wall_time_seconds":40,"model_calls":1,"route_evidence":[{"role":"single-sol","model":"gpt-5.6-sol","effort":"high","expected_effort":"high","task_id":"sol-2"}]}
{"schema_version":1,"trial_id":"search-astral-2","case_id":"search","case_fingerprint":"search-v1","trial":2,"strategy":"astral","acceptance_checks":["unit-tests","manual-review"],"accepted":true,"first_pass_accepted":true,"rework_required":false,"wall_time_seconds":59,"model_calls":3,"route_evidence":[{"role":"orchestrator","model":"gpt-5.6-sol","effort":"high","expected_effort":"high","task_id":"lead-2"},{"role":"terra","model":"gpt-5.6-terra","effort":"xhigh","expected_effort":"xhigh","task_id":"worker-2"},{"role":"reviewer","model":"gpt-5.6-sol","effort":"high","expected_effort":"high","task_id":"review-2"}]}
```

Save it as `benchmarks/trials.jsonl` and run:

```sh
python3 plugins/astral-orchestrator/scripts/benchmark-scorecard.py benchmarks/trials.jsonl
python3 plugins/astral-orchestrator/scripts/benchmark-scorecard.py --format json benchmarks/trials.jsonl
```

Use `--min-trials 3` (or a higher number) to require additional repetitions.

## Read the scorecard carefully

The report aggregates every paired run equally and shows Astral minus the single-Sol
control. A positive success or first-pass percentage-point difference is better for
Astral; a negative rework difference is better; a negative time, model-call, or token
difference is more efficient. It reports route correctness separately so an apparent
outcome improvement cannot hide a run that used the wrong model or effort.

The scorecard fails with a plain error for malformed JSONL, missing fields, duplicate
trials, missing strategies, unequal repeated-trial numbers, differing task fingerprints,
differing acceptance checks, changed route settings within a strategy, reused route task
or session IDs, model-call undercounts, or optional metrics recorded for only part of the
data.

It summarizes the trials you supplied. It does not establish general model superiority,
causation, cost outside the recorded measures, or statistical significance. Do not quote
its result as a product-wide claim without a representative task set, enough repetitions,
consistent conditions, and appropriate independent review.
