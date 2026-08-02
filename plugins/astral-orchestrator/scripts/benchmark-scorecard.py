#!/usr/bin/env python3
"""Validate and summarize local Astral Orchestrator benchmark trials."""

from __future__ import annotations

import argparse
import json
import math
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any


SCHEMA_VERSION = 1
STRATEGIES = ("single-sol", "astral")
ALLOWED_EFFORTS = {"minimal", "low", "medium", "high", "xhigh", "max", "ultra"}
ROLES = {
    "single-sol": "gpt-5.6-sol",
    "orchestrator": "gpt-5.6-sol",
    "luna": "gpt-5.6-luna",
    "terra": "gpt-5.6-terra",
    "reviewer": "gpt-5.6-sol",
}
REQUIRED_TRIAL_FIELDS = {
    "schema_version",
    "trial_id",
    "case_id",
    "case_fingerprint",
    "trial",
    "strategy",
    "acceptance_checks",
    "accepted",
    "first_pass_accepted",
    "rework_required",
    "wall_time_seconds",
    "model_calls",
    "route_evidence",
}
OPTIONAL_TRIAL_FIELDS = {
    "input_tokens",
    "output_tokens",
    "quality_score",
    "quality_score_blinded",
}
REQUIRED_ROUTE_FIELDS = {"role", "model", "effort", "expected_effort", "task_id"}


class BenchmarkError(ValueError):
    """Raised for an invalid or incomparable local benchmark data set."""


@dataclass(frozen=True)
class RouteEvidence:
    role: str
    model: str
    effort: str
    expected_effort: str
    task_id: str


@dataclass(frozen=True)
class Trial:
    trial_id: str
    case_id: str
    case_fingerprint: str
    repetition: int
    strategy: str
    acceptance_checks: frozenset[str]
    accepted: bool
    first_pass_accepted: bool
    rework_required: bool
    wall_time_seconds: float
    model_calls: int
    route_evidence: tuple[RouteEvidence, ...]
    input_tokens: float | None
    output_tokens: float | None
    quality_score: float | None
    quality_score_blinded: bool | None

    @property
    def route_correct(self) -> bool:
        if any(
            route.model != ROLES[route.role]
            or route.effort != route.expected_effort
            for route in self.route_evidence
        ):
            return False

        if self.strategy == "single-sol":
            return len(self.route_evidence) == 1 and self.route_evidence[0].role == "single-sol"

        roles = {route.role for route in self.route_evidence}
        task_ids = [route.task_id for route in self.route_evidence]
        return (
            "orchestrator" in roles
            and "reviewer" in roles
            and bool({"luna", "terra"} & roles)
            and "single-sol" not in roles
            and len(task_ids) == len(set(task_ids))
        )


def positive_integer(value: str) -> int:
    try:
        parsed = int(value)
    except ValueError as error:
        raise argparse.ArgumentTypeError("must be a positive integer") from error
    if parsed < 1:
        raise argparse.ArgumentTypeError("must be a positive integer")
    return parsed


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Validate comparable JSONL trials and report an Astral-versus-single-Sol scorecard."
        )
    )
    parser.add_argument(
        "trials",
        type=Path,
        help="JSONL file containing one benchmark trial record per line.",
    )
    parser.add_argument(
        "--min-trials",
        type=positive_integer,
        default=2,
        help="Minimum repeated trials required for every case and strategy (default: 2).",
    )
    parser.add_argument(
        "--format",
        choices=("text", "json"),
        default="text",
        help="Report format (default: text).",
    )
    return parser.parse_args()


def nonempty_string(value: Any, field: str, line_number: int) -> str:
    if not isinstance(value, str) or not value.strip():
        raise BenchmarkError(f"line {line_number}: {field} must be a non-empty string")
    return value.strip()


def integer(value: Any, field: str, line_number: int, *, minimum: int) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < minimum:
        raise BenchmarkError(f"line {line_number}: {field} must be an integer >= {minimum}")
    return value


def number(value: Any, field: str, line_number: int, *, maximum: float | None = None) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise BenchmarkError(f"line {line_number}: {field} must be a number")
    parsed = float(value)
    if not math.isfinite(parsed) or parsed < 0 or (maximum is not None and parsed > maximum):
        limit = f" between 0 and {maximum:g}" if maximum is not None else " >= 0"
        raise BenchmarkError(f"line {line_number}: {field} must be finite and{limit}")
    return parsed


def boolean(value: Any, field: str, line_number: int) -> bool:
    if not isinstance(value, bool):
        raise BenchmarkError(f"line {line_number}: {field} must be true or false")
    return value


def validate_keys(
    record: dict[str, Any],
    required: set[str],
    optional: set[str],
    line_number: int,
    label: str,
) -> None:
    missing = sorted(required - set(record))
    unexpected = sorted(set(record) - required - optional)
    if missing:
        raise BenchmarkError(f"line {line_number}: {label} is missing {', '.join(missing)}")
    if unexpected:
        raise BenchmarkError(
            f"line {line_number}: {label} has unsupported field(s): {', '.join(unexpected)}"
        )


def parse_route(value: Any, line_number: int, position: int) -> RouteEvidence:
    if not isinstance(value, dict):
        raise BenchmarkError(f"line {line_number}: route_evidence[{position}] must be an object")
    validate_keys(value, REQUIRED_ROUTE_FIELDS, set(), line_number, "route evidence")

    role = nonempty_string(value["role"], "route role", line_number)
    if role not in ROLES:
        raise BenchmarkError(
            f"line {line_number}: route role must be one of {', '.join(sorted(ROLES))}"
        )
    effort = nonempty_string(value["effort"], "route effort", line_number)
    expected_effort = nonempty_string(
        value["expected_effort"], "route expected_effort", line_number
    )
    if effort not in ALLOWED_EFFORTS or expected_effort not in ALLOWED_EFFORTS:
        raise BenchmarkError(
            f"line {line_number}: route effort and expected_effort must be supported levels"
        )
    return RouteEvidence(
        role=role,
        model=nonempty_string(value["model"], "route model", line_number),
        effort=effort,
        expected_effort=expected_effort,
        task_id=nonempty_string(value["task_id"], "route task_id", line_number),
    )


def parse_trial(value: Any, line_number: int) -> Trial:
    if not isinstance(value, dict):
        raise BenchmarkError(f"line {line_number}: each JSONL record must be an object")
    validate_keys(value, REQUIRED_TRIAL_FIELDS, OPTIONAL_TRIAL_FIELDS, line_number, "trial")
    if (
        isinstance(value["schema_version"], bool)
        or not isinstance(value["schema_version"], int)
        or value["schema_version"] != SCHEMA_VERSION
    ):
        raise BenchmarkError(
            f"line {line_number}: schema_version must be {SCHEMA_VERSION}"
        )

    strategy = nonempty_string(value["strategy"], "strategy", line_number)
    if strategy not in STRATEGIES:
        raise BenchmarkError(
            f"line {line_number}: strategy must be one of {', '.join(STRATEGIES)}"
        )

    checks_value = value["acceptance_checks"]
    if not isinstance(checks_value, list) or not checks_value:
        raise BenchmarkError(
            f"line {line_number}: acceptance_checks must be a non-empty list of identifiers"
        )
    checks = frozenset(
        nonempty_string(check, "acceptance_checks entry", line_number)
        for check in checks_value
    )
    if len(checks) != len(checks_value):
        raise BenchmarkError(f"line {line_number}: acceptance_checks must not contain duplicates")

    route_value = value["route_evidence"]
    if not isinstance(route_value, list) or not route_value:
        raise BenchmarkError(f"line {line_number}: route_evidence must be a non-empty list")
    route_evidence = tuple(
        parse_route(route, line_number, position)
        for position, route in enumerate(route_value)
    )

    accepted = boolean(value["accepted"], "accepted", line_number)
    first_pass_accepted = boolean(
        value["first_pass_accepted"], "first_pass_accepted", line_number
    )
    rework_required = boolean(value["rework_required"], "rework_required", line_number)
    if first_pass_accepted and not accepted:
        raise BenchmarkError(
            f"line {line_number}: first_pass_accepted cannot be true when accepted is false"
        )
    if first_pass_accepted and rework_required:
        raise BenchmarkError(
            f"line {line_number}: first_pass_accepted cannot be true when rework_required is true"
        )
    if accepted and not first_pass_accepted and not rework_required:
        raise BenchmarkError(
            f"line {line_number}: accepted is true after a failed first pass, so rework_required must be true"
        )

    quality_score = None
    quality_score_blinded = None
    if "quality_score" in value:
        quality_score = number(value["quality_score"], "quality_score", line_number, maximum=100)
        if "quality_score_blinded" not in value:
            raise BenchmarkError(
                f"line {line_number}: quality_score requires quality_score_blinded"
            )
        quality_score_blinded = boolean(
            value["quality_score_blinded"], "quality_score_blinded", line_number
        )
    elif "quality_score_blinded" in value:
        raise BenchmarkError(
            f"line {line_number}: quality_score_blinded requires quality_score"
        )

    model_calls = integer(value["model_calls"], "model_calls", line_number, minimum=1)
    if model_calls < len(route_evidence):
        raise BenchmarkError(
            f"line {line_number}: model_calls must be at least the number of route_evidence entries"
        )

    return Trial(
        trial_id=nonempty_string(value["trial_id"], "trial_id", line_number),
        case_id=nonempty_string(value["case_id"], "case_id", line_number),
        case_fingerprint=nonempty_string(
            value["case_fingerprint"], "case_fingerprint", line_number
        ),
        repetition=integer(value["trial"], "trial", line_number, minimum=1),
        strategy=strategy,
        acceptance_checks=checks,
        accepted=accepted,
        first_pass_accepted=first_pass_accepted,
        rework_required=rework_required,
        wall_time_seconds=number(value["wall_time_seconds"], "wall_time_seconds", line_number),
        model_calls=model_calls,
        route_evidence=route_evidence,
        input_tokens=(
            number(value["input_tokens"], "input_tokens", line_number)
            if "input_tokens" in value
            else None
        ),
        output_tokens=(
            number(value["output_tokens"], "output_tokens", line_number)
            if "output_tokens" in value
            else None
        ),
        quality_score=quality_score,
        quality_score_blinded=quality_score_blinded,
    )


def load_trials(path: Path) -> list[Trial]:
    if not path.is_file():
        raise BenchmarkError(f"trial file must be a readable regular file: {path}")
    try:
        contents = path.read_text(encoding="utf-8")
    except OSError as error:
        raise BenchmarkError(f"could not read trial file: {error}") from error
    if not contents:
        raise BenchmarkError("trial file is empty")

    trials = []
    for line_number, line in enumerate(contents.splitlines(), start=1):
        if not line.strip():
            raise BenchmarkError(f"line {line_number}: blank lines are not valid JSONL records")
        try:
            value = json.loads(line)
        except json.JSONDecodeError as error:
            raise BenchmarkError(f"line {line_number}: invalid JSON: {error.msg}") from error
        trials.append(parse_trial(value, line_number))
    if not trials:
        raise BenchmarkError("trial file is empty")
    return trials


def ensure_optional_metric_availability(trials: list[Trial]) -> None:
    for field in ("input_tokens", "output_tokens", "quality_score"):
        present = [getattr(trial, field) is not None for trial in trials]
        if any(present) and not all(present):
            raise BenchmarkError(
                f"incomparable optional metric {field}: record it for every trial or omit it for every trial"
            )


def validate_comparability(trials: list[Trial], minimum_trials: int) -> dict[str, dict[str, dict[int, Trial]]]:
    ensure_optional_metric_availability(trials)
    trial_ids: set[str] = set()
    route_task_ids: set[str] = set()
    grouped: dict[str, dict[str, dict[int, Trial]]] = {}
    for trial in trials:
        if trial.trial_id in trial_ids:
            raise BenchmarkError(f"duplicate trial_id: {trial.trial_id}")
        trial_ids.add(trial.trial_id)
        for route in trial.route_evidence:
            if route.task_id in route_task_ids:
                raise BenchmarkError(f"duplicate route task_id: {route.task_id}")
            route_task_ids.add(route.task_id)
        by_strategy = grouped.setdefault(trial.case_id, {})
        by_repetition = by_strategy.setdefault(trial.strategy, {})
        if trial.repetition in by_repetition:
            raise BenchmarkError(
                f"case {trial.case_id!r} has duplicate {trial.strategy} trial {trial.repetition}"
            )
        by_repetition[trial.repetition] = trial

    for case_id, by_strategy in sorted(grouped.items()):
        if set(by_strategy) != set(STRATEGIES):
            missing = sorted(set(STRATEGIES) - set(by_strategy))
            raise BenchmarkError(
                f"incomparable strategies for case {case_id!r}: missing {', '.join(missing)}"
            )
        control = by_strategy["single-sol"]
        astral = by_strategy["astral"]
        if set(control) != set(astral):
            raise BenchmarkError(
                f"incomparable strategies for case {case_id!r}: repeated trial numbers differ"
            )
        if len(control) < minimum_trials:
            raise BenchmarkError(
                f"case {case_id!r} needs at least {minimum_trials} repeated trials per strategy"
            )
        all_case_trials = [*control.values(), *astral.values()]
        if len({trial.case_fingerprint for trial in all_case_trials}) != 1:
            raise BenchmarkError(
                f"incomparable strategies for case {case_id!r}: case_fingerprint changes across repeated trials"
            )
        if len({trial.acceptance_checks for trial in all_case_trials}) != 1:
            raise BenchmarkError(
                f"incomparable strategies for case {case_id!r}: acceptance checks differ across repeated trials"
            )
        for strategy, strategy_trials in by_strategy.items():
            route_configurations = {
                tuple(
                    sorted(
                        (route.role, route.model, route.expected_effort)
                        for route in trial.route_evidence
                    )
                )
                for trial in strategy_trials.values()
            }
            if len(route_configurations) != 1:
                raise BenchmarkError(
                    f"incomparable {strategy} trials for case {case_id!r}: "
                    "route role/model/expected_effort configuration changes across repetitions"
                )
            observed_route_efforts = {
                tuple(
                    sorted(
                        (
                            route.role,
                            route.model,
                            route.expected_effort,
                            route.effort,
                        )
                        for route in trial.route_evidence
                    )
                )
                for trial in strategy_trials.values()
            }
            if len(observed_route_efforts) != 1:
                raise BenchmarkError(
                    f"incomparable {strategy} trials for case {case_id!r}: "
                    "observed route effort changes across repetitions"
                )
    return grouped


def mean(values: list[float]) -> float:
    return sum(values) / len(values)


def optional_mean(trials: list[Trial], field: str) -> float | None:
    values = [getattr(trial, field) for trial in trials]
    if values[0] is None:
        return None
    return mean([float(value) for value in values])


def strategy_summary(trials: list[Trial]) -> dict[str, Any]:
    input_tokens = optional_mean(trials, "input_tokens")
    output_tokens = optional_mean(trials, "output_tokens")
    quality_score = optional_mean(trials, "quality_score")
    return {
        "trial_count": len(trials),
        "success_rate": mean([float(trial.accepted) for trial in trials]),
        "first_pass_acceptance_rate": mean(
            [float(trial.first_pass_accepted) for trial in trials]
        ),
        "rework_rate": mean([float(trial.rework_required) for trial in trials]),
        "route_correct_rate": mean([float(trial.route_correct) for trial in trials]),
        "mean_wall_time_seconds": mean([trial.wall_time_seconds for trial in trials]),
        "mean_model_calls": mean([float(trial.model_calls) for trial in trials]),
        "mean_input_tokens": input_tokens,
        "mean_output_tokens": output_tokens,
        "mean_total_tokens": (
            input_tokens + output_tokens
            if input_tokens is not None and output_tokens is not None
            else None
        ),
        "mean_quality_score": quality_score,
        "quality_score_blinded_rate": (
            mean([float(trial.quality_score_blinded) for trial in trials])
            if quality_score is not None
            else None
        ),
    }


def difference(astral: float | None, control: float | None) -> float | None:
    if astral is None or control is None:
        return None
    return astral - control


def build_report(grouped: dict[str, dict[str, dict[int, Trial]]], minimum_trials: int) -> dict[str, Any]:
    control_trials = [
        trial
        for by_strategy in grouped.values()
        for trial in by_strategy["single-sol"].values()
    ]
    astral_trials = [
        trial
        for by_strategy in grouped.values()
        for trial in by_strategy["astral"].values()
    ]
    control = strategy_summary(control_trials)
    astral = strategy_summary(astral_trials)
    comparison = {
        "success_rate_percentage_points": 100
        * difference(astral["success_rate"], control["success_rate"]),
        "first_pass_acceptance_rate_percentage_points": 100
        * difference(
            astral["first_pass_acceptance_rate"],
            control["first_pass_acceptance_rate"],
        ),
        "rework_rate_percentage_points": 100
        * difference(astral["rework_rate"], control["rework_rate"]),
        "route_correct_rate_percentage_points": 100
        * difference(astral["route_correct_rate"], control["route_correct_rate"]),
        "mean_wall_time_seconds": difference(
            astral["mean_wall_time_seconds"], control["mean_wall_time_seconds"]
        ),
        "mean_model_calls": difference(
            astral["mean_model_calls"], control["mean_model_calls"]
        ),
        "mean_input_tokens": difference(
            astral["mean_input_tokens"], control["mean_input_tokens"]
        ),
        "mean_output_tokens": difference(
            astral["mean_output_tokens"], control["mean_output_tokens"]
        ),
        "mean_total_tokens": difference(
            astral["mean_total_tokens"], control["mean_total_tokens"]
        ),
        "mean_quality_score": difference(
            astral["mean_quality_score"], control["mean_quality_score"]
        ),
        "quality_score_blinded_rate_percentage_points": (
            100
            * difference(
                astral["quality_score_blinded_rate"],
                control["quality_score_blinded_rate"],
            )
            if astral["quality_score_blinded_rate"] is not None
            and control["quality_score_blinded_rate"] is not None
            else None
        ),
    }
    warnings = []
    if control["route_correct_rate"] < 1 or astral["route_correct_rate"] < 1:
        warnings.append(
            "Route correctness is below 100%; investigate the route deviation before drawing a performance conclusion."
        )
    if astral["quality_score_blinded_rate"] not in (None, 1):
        warnings.append(
            "Some Astral quality scores were not blinded; treat that comparison as potentially biased."
        )
    if control["quality_score_blinded_rate"] not in (None, 1):
        warnings.append(
            "Some single-Sol quality scores were not blinded; treat that comparison as potentially biased."
        )
    return {
        "schema_version": SCHEMA_VERSION,
        "comparability": {
            "control_strategy": "single-sol",
            "treatment_strategy": "astral",
            "case_count": len(grouped),
            "paired_trial_count": len(control_trials),
            "minimum_trials_required": minimum_trials,
            "repetitions_by_case": {
                case_id: len(by_strategy["single-sol"])
                for case_id, by_strategy in sorted(grouped.items())
            },
        },
        "strategies": {"single-sol": control, "astral": astral},
        "comparison": {"astral_minus_single_sol": comparison},
        "warnings": warnings,
    }


def format_value(value: float | None, *, suffix: str = "", decimals: int = 1) -> str:
    if value is None:
        return "n/a"
    return f"{value:.{decimals}f}{suffix}"


def format_difference(value: float | None, *, suffix: str = "", decimals: int = 1) -> str:
    if value is None:
        return "n/a"
    return f"{value:+.{decimals}f}{suffix}"


def text_report(report: dict[str, Any]) -> str:
    comparability = report["comparability"]
    control = report["strategies"]["single-sol"]
    astral = report["strategies"]["astral"]
    comparison = report["comparison"]["astral_minus_single_sol"]
    rows = [
        (
            "Success rate",
            format_value(100 * control["success_rate"], suffix="%"),
            format_value(100 * astral["success_rate"], suffix="%"),
            format_difference(comparison["success_rate_percentage_points"], suffix=" pp"),
        ),
        (
            "First-pass acceptance",
            format_value(100 * control["first_pass_acceptance_rate"], suffix="%"),
            format_value(100 * astral["first_pass_acceptance_rate"], suffix="%"),
            format_difference(
                comparison["first_pass_acceptance_rate_percentage_points"], suffix=" pp"
            ),
        ),
        (
            "Rework required",
            format_value(100 * control["rework_rate"], suffix="%"),
            format_value(100 * astral["rework_rate"], suffix="%"),
            format_difference(comparison["rework_rate_percentage_points"], suffix=" pp"),
        ),
        (
            "Route correct",
            format_value(100 * control["route_correct_rate"], suffix="%"),
            format_value(100 * astral["route_correct_rate"], suffix="%"),
            format_difference(
                comparison["route_correct_rate_percentage_points"], suffix=" pp"
            ),
        ),
        (
            "Mean wall time",
            format_value(control["mean_wall_time_seconds"], suffix=" s"),
            format_value(astral["mean_wall_time_seconds"], suffix=" s"),
            format_difference(comparison["mean_wall_time_seconds"], suffix=" s"),
        ),
        (
            "Mean model calls",
            format_value(control["mean_model_calls"]),
            format_value(astral["mean_model_calls"]),
            format_difference(comparison["mean_model_calls"]),
        ),
        (
            "Mean total tokens",
            format_value(control["mean_total_tokens"]),
            format_value(astral["mean_total_tokens"]),
            format_difference(comparison["mean_total_tokens"]),
        ),
        (
            "Mean quality score",
            format_value(control["mean_quality_score"]),
            format_value(astral["mean_quality_score"]),
            format_difference(comparison["mean_quality_score"]),
        ),
        (
            "Blinded quality scores",
            format_value(100 * control["quality_score_blinded_rate"], suffix="%")
            if control["quality_score_blinded_rate"] is not None
            else "n/a",
            format_value(100 * astral["quality_score_blinded_rate"], suffix="%")
            if astral["quality_score_blinded_rate"] is not None
            else "n/a",
            format_difference(
                comparison["quality_score_blinded_rate_percentage_points"], suffix=" pp"
            ),
        ),
    ]
    widths = [
        max(len(row[index]) for row in rows + [("Metric", "Single-Sol", "Astral", "Astral - control")])
        for index in range(4)
    ]
    header = ("Metric", "Single-Sol", "Astral", "Astral - control")
    lines = [
        "Astral Orchestrator benchmark scorecard",
        (
            f"Comparable cases: {comparability['case_count']} | "
            f"paired trials: {comparability['paired_trial_count']} | "
            f"minimum repetitions: {comparability['minimum_trials_required']}"
        ),
        "",
        "  ".join(header[index].ljust(widths[index]) for index in range(4)),
        "  ".join("-" * width for width in widths),
    ]
    lines.extend(
        "  ".join(row[index].ljust(widths[index]) for index in range(4)) for row in rows
    )
    if report["warnings"]:
        lines.append("")
        lines.extend(f"WARNING: {warning}" for warning in report["warnings"])
    return "\n".join(lines)


def main() -> int:
    args = parse_args()
    try:
        trials = load_trials(args.trials)
        grouped = validate_comparability(trials, args.min_trials)
        report = build_report(grouped, args.min_trials)
    except BenchmarkError as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 2

    if args.format == "json":
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(text_report(report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
