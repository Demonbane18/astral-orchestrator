#!/usr/bin/env python3
"""Validate and summarize local Astral Orchestrator benchmark trials."""

from __future__ import annotations

import argparse
import json
import math
import random
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any


SCHEMA_VERSION = 1
SCHEMA_V2_VERSION = 2
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
    "cached_input_tokens",
    "output_tokens",
    "reasoning_output_tokens",
    "quality_score",
    "quality_score_blinded",
}
REQUIRED_ROUTE_FIELDS = {"role", "model", "effort", "expected_effort", "task_id"}
V2_VARIANTS = ("single-sol-xhigh", "single-sol-max", "astral-guided")
V2_BASELINE_VARIANT = "single-sol-xhigh"
V2_REQUIRED_FIELDS = {
    "schema_version", "trial_id", "case_id", "case_fingerprint", "repetition",
    "strategy", "variant", "mode", "acceptance_checks", "check_results", "accepted",
    "first_pass_accepted", "rework_required", "wall_time_seconds", "model_calls",
    "aggregate_tokens", "process_metrics", "route_evidence", "route_correct",
    "opaque_artifact", "blind_judge", "disclosures",
}
V2_OPTIONAL_FIELDS = {"failure", "timeout"}
V2_TOKEN_FIELDS = {
    "input_tokens", "cached_input_tokens", "output_tokens", "reasoning_output_tokens",
    "total_tokens",
}
V2_ROUTE_FIELDS = {
    "role", "model", "effort", "expected_model", "expected_effort", "task_id",
    "sandbox", "expected_sandbox",
}
V2_PROCESS_FIELDS = {
    "role", "model", "effort", "session_id", "input_tokens", "cached_input_tokens",
    "output_tokens", "reasoning_output_tokens", "total_tokens", "duration_seconds",
    "sandbox", "expected_sandbox",
}
V2_EXPECTED_SANDBOXES = {
    "single-sol": "workspace-write",
    "orchestrator": "read-only",
    "luna": "workspace-write",
    "terra": "workspace-write",
    "reviewer": "read-only",
}
V2_SANDBOXES = {"read-only", "workspace-write"}
V2_HASH_RE = re.compile(r"^[0-9a-fA-F]{64}$")


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
    cached_input_tokens: float | None
    output_tokens: float | None
    reasoning_output_tokens: float | None
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


@dataclass(frozen=True)
class V2Trial:
    """A validated schema-v2 record kept as its JSON-shaped dictionary.

    The scorecard intentionally keeps the original fields available to callers.  The
    dataclass is only a marker used to distinguish v2 records from legacy ``Trial``
    objects when the CLI dispatches between the two report formats.
    """

    record: dict[str, Any]

    def __getitem__(self, key: str) -> Any:
        return self.record[key]

    def get(self, key: str, default: Any = None) -> Any:
        return self.record.get(key, default)


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

    if "cached_input_tokens" in value and "input_tokens" not in value:
        raise BenchmarkError(f"line {line_number}: cached_input_tokens requires input_tokens")
    if "reasoning_output_tokens" in value and "output_tokens" not in value:
        raise BenchmarkError(f"line {line_number}: reasoning_output_tokens requires output_tokens")
    if "cached_input_tokens" in value:
        cached_tokens = number(value["cached_input_tokens"], "cached_input_tokens", line_number)
        input_tokens = number(value["input_tokens"], "input_tokens", line_number)
        if cached_tokens > input_tokens:
            raise BenchmarkError(f"line {line_number}: cached_input_tokens cannot exceed input_tokens")

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
        cached_input_tokens=(
            number(value["cached_input_tokens"], "cached_input_tokens", line_number)
            if "cached_input_tokens" in value
            else None
        ),
        output_tokens=(
            number(value["output_tokens"], "output_tokens", line_number)
            if "output_tokens" in value
            else None
        ),
        reasoning_output_tokens=(
            number(value["reasoning_output_tokens"], "reasoning_output_tokens", line_number)
            if "reasoning_output_tokens" in value
            else None
        ),
        quality_score=quality_score,
        quality_score_blinded=quality_score_blinded,
    )


def _v2_number(value: Any, field: str, line_number: int) -> float:
    return number(value, field, line_number)


def _v2_token_usage(
    value: Any, field: str, line_number: int, *, allow_none: bool = False
) -> dict[str, float] | None:
    if value is None and allow_none:
        return None
    if not isinstance(value, dict):
        raise BenchmarkError(f"line {line_number}: {field} must be an object")
    missing = sorted(V2_TOKEN_FIELDS - set(value))
    unexpected = sorted(set(value) - V2_TOKEN_FIELDS)
    if missing:
        raise BenchmarkError(f"line {line_number}: {field} is missing {', '.join(missing)}")
    if unexpected:
        raise BenchmarkError(
            f"line {line_number}: {field} has unsupported field(s): {', '.join(unexpected)}"
        )
    parsed = {
        token: _v2_number(value[token], f"{field}.{token}", line_number)
        for token in V2_TOKEN_FIELDS
    }
    if parsed["cached_input_tokens"] > parsed["input_tokens"]:
        raise BenchmarkError(
            f"line {line_number}: {field}.cached_input_tokens cannot exceed input_tokens"
        )
    if not math.isclose(
        parsed["total_tokens"],
        parsed["input_tokens"] + parsed["output_tokens"],
        rel_tol=1e-12,
        abs_tol=1e-9,
    ):
        raise BenchmarkError(
            f"line {line_number}: {field}.total_tokens must equal input_tokens + output_tokens"
        )
    return parsed


def _v2_route(value: Any, line_number: int, position: int) -> dict[str, str]:
    if not isinstance(value, dict):
        raise BenchmarkError(f"line {line_number}: route_evidence[{position}] must be an object")
    missing = sorted(V2_ROUTE_FIELDS - set(value))
    unexpected = sorted(set(value) - V2_ROUTE_FIELDS)
    if missing:
        raise BenchmarkError(
            f"line {line_number}: route_evidence[{position}] is missing {', '.join(missing)}"
        )
    if unexpected:
        raise BenchmarkError(
            f"line {line_number}: route_evidence[{position}] has unsupported field(s): "
            f"{', '.join(unexpected)}"
        )
    route = {
        field: nonempty_string(value[field], f"route_evidence[{position}].{field}", line_number)
        for field in V2_ROUTE_FIELDS
    }
    if route["role"] not in ROLES:
        raise BenchmarkError(f"line {line_number}: route role is unsupported: {route['role']}")
    if route["effort"] not in ALLOWED_EFFORTS or route["expected_effort"] not in ALLOWED_EFFORTS:
        raise BenchmarkError(f"line {line_number}: route effort is unsupported")
    if route["sandbox"] not in V2_SANDBOXES or route["expected_sandbox"] not in V2_SANDBOXES:
        raise BenchmarkError(f"line {line_number}: route sandbox is unsupported")
    return route


def _v2_process_metrics(value: Any, line_number: int) -> tuple[list[dict[str, Any]] | None, list[str]]:
    """Validate process telemetry, preserving explicit gaps as disclosures."""
    if value is None:
        return None, ["process telemetry unavailable; aggregate tokens are strategy totals"]
    if not isinstance(value, list):
        raise BenchmarkError(f"line {line_number}: process_metrics must be a list or null")
    if not value:
        return [], ["process telemetry unavailable; aggregate tokens are strategy totals"]
    parsed: list[dict[str, Any]] = []
    disclosures: list[str] = []
    sessions: set[str] = set()
    complete = True
    for position, item in enumerate(value):
        if not isinstance(item, dict):
            raise BenchmarkError(f"line {line_number}: process_metrics[{position}] must be an object")
        missing = sorted(V2_PROCESS_FIELDS - set(item))
        unexpected = sorted(set(item) - V2_PROCESS_FIELDS)
        if unexpected:
            raise BenchmarkError(
                f"line {line_number}: process_metrics[{position}] has unsupported field(s): "
                f"{', '.join(unexpected)}"
            )
        if missing:
            complete = False
            disclosures.append(
                f"process telemetry missing {', '.join(missing)} at item {position}; no zero inferred"
            )
            parsed.append(dict(item))
            continue
        role = nonempty_string(item["role"], f"process_metrics[{position}].role", line_number)
        model = nonempty_string(item["model"], f"process_metrics[{position}].model", line_number)
        effort = nonempty_string(item["effort"], f"process_metrics[{position}].effort", line_number)
        sandbox = nonempty_string(item["sandbox"], f"process_metrics[{position}].sandbox", line_number)
        expected_sandbox = nonempty_string(
            item["expected_sandbox"], f"process_metrics[{position}].expected_sandbox", line_number
        )
        if role not in ROLES or effort not in ALLOWED_EFFORTS:
            raise BenchmarkError(f"line {line_number}: process_metrics[{position}] route is unsupported")
        if sandbox not in V2_SANDBOXES or expected_sandbox not in V2_SANDBOXES:
            raise BenchmarkError(f"line {line_number}: process_metrics[{position}] sandbox is unsupported")
        session_id = nonempty_string(item["session_id"], f"process_metrics[{position}].session_id", line_number)
        if session_id in sessions:
            raise BenchmarkError(f"line {line_number}: duplicate session_id: {session_id}")
        sessions.add(session_id)
        usage = _v2_token_usage(
            {field: item[field] for field in V2_TOKEN_FIELDS},
            f"process_metrics[{position}]",
            line_number,
        )
        assert usage is not None
        parsed.append({
            "role": role, "model": model, "effort": effort, "session_id": session_id,
            "sandbox": sandbox, "expected_sandbox": expected_sandbox, **usage,
            "duration_seconds": _v2_number(
                item["duration_seconds"], f"process_metrics[{position}].duration_seconds", line_number
            ),
        })
    if complete:
        return parsed, disclosures
    return parsed, disclosures


def _v2_check_results(value: Any, acceptance_checks: frozenset[str], line_number: int) -> list[dict[str, Any]]:
    if not isinstance(value, list) or not value:
        raise BenchmarkError(f"line {line_number}: check_results must be a non-empty list")
    results: list[dict[str, Any]] = []
    ids: set[str] = set()
    for position, item in enumerate(value):
        if not isinstance(item, dict):
            raise BenchmarkError(f"line {line_number}: check_results[{position}] must be an object")
        if "id" not in item:
            raise BenchmarkError(f"line {line_number}: check_results[{position}] is missing id")
        check_id = nonempty_string(item["id"], f"check_results[{position}].id", line_number)
        if check_id in ids:
            raise BenchmarkError(f"line {line_number}: duplicate check id: {check_id}")
        ids.add(check_id)
        result = dict(item)
        if not {"returncode", "passed", "accepted"} & set(item):
            raise BenchmarkError(
                f"line {line_number}: check_results[{position}] must include an explicit outcome"
            )
        if "returncode" in item:
            if isinstance(item["returncode"], bool) or not isinstance(item["returncode"], int):
                raise BenchmarkError(f"line {line_number}: check_results[{position}].returncode must be an integer")
        if "duration_seconds" in item:
            result["duration_seconds"] = _v2_number(
                item["duration_seconds"], f"check_results[{position}].duration_seconds", line_number
            )
        for flag in ("passed", "accepted"):
            if flag in item and not isinstance(item[flag], bool):
                raise BenchmarkError(f"line {line_number}: check_results[{position}].{flag} must be true or false")
        results.append(result)
    if ids != acceptance_checks:
        raise BenchmarkError(
            f"line {line_number}: check_results ids must match acceptance_checks"
        )
    return results


def _v2_blind_judge(
    value: Any, line_number: int, *, allow_null_usage: bool = False
) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise BenchmarkError(f"line {line_number}: blind_judge must be an object")
    rubric_key = "rubric" if "rubric" in value else "rubric_id" if "rubric_id" in value else None
    if rubric_key is None:
        raise BenchmarkError(f"line {line_number}: blind_judge is missing rubric id")
    required = {rubric_key, "score", "blinded", "usage"}
    missing = sorted(required - set(value))
    if missing:
        raise BenchmarkError(f"line {line_number}: blind_judge is missing {', '.join(missing)}")
    if not isinstance(value["blinded"], bool) or not value["blinded"]:
        raise BenchmarkError(f"line {line_number}: blind_judge.blinded must be true")
    score = value["score"]
    if score is not None:
        score = number(score, "blind_judge.score", line_number, maximum=100)
    usage = _v2_token_usage(
        value["usage"], "blind_judge.usage", line_number, allow_none=allow_null_usage
    )
    return {**value, "score": score, "usage": usage}


def _v2_route_is_correct(variant: str, routes: list[dict[str, str]]) -> bool:
    if any(
        route["model"] != ROLES[route["role"]]
        or route["expected_model"] != ROLES[route["role"]]
        or route["effort"] != route["expected_effort"]
        or route["sandbox"] != route["expected_sandbox"]
        or route["expected_sandbox"] != V2_EXPECTED_SANDBOXES[route["role"]]
        for route in routes
    ):
        return False
    roles = [route["role"] for route in routes]
    if variant in {"single-sol-xhigh", "single-sol-max"}:
        expected_effort = variant.removeprefix("single-sol-")
        return bool(routes) and all(
            route["role"] == "single-sol"
            and route["expected_effort"] == expected_effort
            for route in routes
        )
    if variant == "astral-guided":
        return (
            "orchestrator" in roles
            and "reviewer" in roles
            and bool({"luna", "terra"} & set(roles))
            and "single-sol" not in roles
            and len({route["task_id"] for route in routes}) == len(routes)
        )
    return False


def validate_v2_record(value: Any, line_number: int) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise BenchmarkError(f"line {line_number}: each JSONL record must be an object")
    validate_keys(value, V2_REQUIRED_FIELDS, V2_OPTIONAL_FIELDS, line_number, "schema-v2 trial")
    if value.get("schema_version") != SCHEMA_V2_VERSION or isinstance(value.get("schema_version"), bool):
        raise BenchmarkError(f"line {line_number}: schema_version must be {SCHEMA_V2_VERSION}")
    variant = nonempty_string(value["variant"], "variant", line_number)
    if variant not in V2_VARIANTS:
        raise BenchmarkError(f"line {line_number}: variant must be one of {', '.join(V2_VARIANTS)}")
    strategy = nonempty_string(value["strategy"], "strategy", line_number)
    if strategy not in {"single-sol", "astral"}:
        raise BenchmarkError(f"line {line_number}: strategy must be single-sol or astral")
    if variant.startswith("single-sol") and strategy != "single-sol":
        raise BenchmarkError(f"line {line_number}: single-Sol variant requires strategy single-sol")
    if variant == "astral-guided" and strategy != "astral":
        raise BenchmarkError(f"line {line_number}: astral-guided requires strategy astral")
    checks_value = value["acceptance_checks"]
    if not isinstance(checks_value, list) or not checks_value:
        raise BenchmarkError(f"line {line_number}: acceptance_checks must be a non-empty list")
    checks = frozenset(nonempty_string(item, "acceptance_checks entry", line_number) for item in checks_value)
    if len(checks) != len(checks_value):
        raise BenchmarkError(f"line {line_number}: acceptance_checks must not contain duplicates")
    results = _v2_check_results(value["check_results"], checks, line_number)
    accepted = boolean(value["accepted"], "accepted", line_number)
    first_pass = boolean(value["first_pass_accepted"], "first_pass_accepted", line_number)
    rework = boolean(value["rework_required"], "rework_required", line_number)
    if first_pass and not accepted:
        raise BenchmarkError(f"line {line_number}: first_pass_accepted cannot be true when accepted is false")
    if first_pass and rework:
        raise BenchmarkError(f"line {line_number}: first_pass_accepted cannot be true when rework_required is true")
    if accepted and not first_pass and not rework:
        raise BenchmarkError(f"line {line_number}: accepted is true after a failed first pass, so rework_required must be true")
    check_failed = any(
        result.get("returncode", 0) != 0
        or result.get("passed", True) is False
        or result.get("accepted", True) is False
        for result in results
    )
    if accepted and check_failed:
        raise BenchmarkError(f"line {line_number}: accepted cannot be true when an objective check failed")
    timeout = value.get("timeout", False)
    if not isinstance(timeout, bool):
        raise BenchmarkError(f"line {line_number}: timeout must be true or false")
    failure = value.get("failure")
    if failure is not None and not isinstance(failure, (str, dict)):
        raise BenchmarkError(f"line {line_number}: failure must be null, a string, or an object")
    if accepted and (failure is not None or timeout):
        raise BenchmarkError(f"line {line_number}: accepted cannot be true for a failed or timed-out trial")
    telemetry_may_be_null = failure is not None or timeout
    aggregate = _v2_token_usage(
        value["aggregate_tokens"], "aggregate_tokens", line_number,
        allow_none=telemetry_may_be_null,
    )
    process, process_disclosures = _v2_process_metrics(value["process_metrics"], line_number)
    if aggregate is not None and process and all(V2_TOKEN_FIELDS | {"duration_seconds"} <= set(item) for item in process):
        totals = {
            field: sum(float(item[field]) for item in process)
            for field in V2_TOKEN_FIELDS
        }
        for field in V2_TOKEN_FIELDS:
            if not math.isclose(aggregate[field], totals[field], rel_tol=1e-12, abs_tol=1e-9):
                raise BenchmarkError(
                    f"line {line_number}: aggregate_tokens.{field} must equal process_metrics totals"
                )
    routes_value = value["route_evidence"]
    if not isinstance(routes_value, list):
        raise BenchmarkError(f"line {line_number}: route_evidence must be a list")
    routes = [_v2_route(route, line_number, position) for position, route in enumerate(routes_value)]
    if len({route["task_id"] for route in routes}) != len(routes):
        raise BenchmarkError(f"line {line_number}: route_evidence task_ids must be unique")
    route_correct = boolean(value["route_correct"], "route_correct", line_number)
    computed_route_correct = _v2_route_is_correct(variant, routes)
    if route_correct != computed_route_correct:
        raise BenchmarkError(f"line {line_number}: route_correct is inconsistent with route_evidence")
    if value["model_calls"] is None and telemetry_may_be_null:
        model_calls = None
    else:
        model_calls = integer(value["model_calls"], "model_calls", line_number, minimum=0)
    if model_calls is not None and model_calls < len(routes):
        raise BenchmarkError(f"line {line_number}: model_calls must be at least the number of route_evidence entries")
    artifact = value["opaque_artifact"]
    if not isinstance(artifact, dict):
        raise BenchmarkError(f"line {line_number}: opaque_artifact must be an object")
    for field in ("id", "diff_path", "diff_sha256"):
        if field not in artifact:
            raise BenchmarkError(f"line {line_number}: opaque_artifact is missing {field}")
        nonempty_string(artifact[field], f"opaque_artifact.{field}", line_number)
    if not V2_HASH_RE.fullmatch(artifact["diff_sha256"]):
        raise BenchmarkError(f"line {line_number}: opaque_artifact.diff_sha256 must be a SHA-256 hex digest")
    # Objective checks determine acceptance. Judge telemetry is useful secondary
    # evidence, but its absence must not invalidate an otherwise complete trial.
    judge = _v2_blind_judge(value["blind_judge"], line_number, allow_null_usage=True)
    disclosures = value["disclosures"]
    if not isinstance(disclosures, list) or any(not isinstance(item, str) or not item.strip() for item in disclosures):
        raise BenchmarkError(f"line {line_number}: disclosures must be a list of non-empty strings")
    normalized = dict(value)
    normalized.update({
        "trial_id": nonempty_string(value["trial_id"], "trial_id", line_number),
        "case_id": nonempty_string(value["case_id"], "case_id", line_number),
        "case_fingerprint": nonempty_string(value["case_fingerprint"], "case_fingerprint", line_number),
        "repetition": integer(value["repetition"], "repetition", line_number, minimum=1),
        "mode": nonempty_string(value["mode"], "mode", line_number),
        "wall_time_seconds": (
            None if value["wall_time_seconds"] is None and telemetry_may_be_null
            else _v2_number(value["wall_time_seconds"], "wall_time_seconds", line_number)
        ),
        "model_calls": model_calls,
        "acceptance_checks": sorted(checks), "check_results": results,
        "aggregate_tokens": aggregate, "process_metrics": process,
        "process_disclosures": process_disclosures, "route_evidence": routes,
        "opaque_artifact": artifact, "blind_judge": judge,
        "failure": failure, "timeout": timeout,
        "disclosures": [item.strip() for item in disclosures],
    })
    return normalized


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


def load_records(path: Path) -> list[Any]:
    """Load one schema version and reject a mixed-version JSONL file."""
    if not path.is_file():
        raise BenchmarkError(f"trial file must be a readable regular file: {path}")
    try:
        contents = path.read_text(encoding="utf-8")
    except OSError as error:
        raise BenchmarkError(f"could not read trial file: {error}") from error
    if not contents:
        raise BenchmarkError("trial file is empty")
    raw_records: list[tuple[int, Any]] = []
    versions: set[int] = set()
    for line_number, line in enumerate(contents.splitlines(), start=1):
        if not line.strip():
            raise BenchmarkError(f"line {line_number}: blank lines are not valid JSONL records")
        try:
            value = json.loads(line)
        except json.JSONDecodeError as error:
            raise BenchmarkError(f"line {line_number}: invalid JSON: {error.msg}") from error
        if not isinstance(value, dict):
            raise BenchmarkError(f"line {line_number}: each JSONL record must be an object")
        version = value.get("schema_version")
        if isinstance(version, bool) or not isinstance(version, int):
            raise BenchmarkError(f"line {line_number}: schema_version must be an integer")
        versions.add(version)
        raw_records.append((line_number, value))
    if len(versions) != 1:
        found = ", ".join(str(version) for version in sorted(versions))
        raise BenchmarkError(f"mixed schema versions are not comparable (found: {found})")
    version = versions.pop()
    if version == SCHEMA_VERSION:
        return [parse_trial(value, line_number) for line_number, value in raw_records]
    if version == SCHEMA_V2_VERSION:
        return [validate_v2_record(value, line_number) for line_number, value in raw_records]
    raise BenchmarkError(f"schema_version must be {SCHEMA_VERSION} or {SCHEMA_V2_VERSION}")


def validate_v2_records(records: list[dict[str, Any]], minimum_trials: int) -> dict[str, dict[int, dict[str, dict[str, Any]]]]:
    if not records:
        raise BenchmarkError("trial file is empty")
    parsed = [
        validate_v2_record(
            {
                key: value
                for key, value in record.items()
                if key != "process_disclosures"
            }
            if isinstance(record, dict)
            else record,
            position,
        )
        for position, record in enumerate(records, start=1)
    ]
    trial_ids: set[str] = set()
    session_ids: set[str] = set()
    route_task_ids: set[str] = set()
    grouped: dict[str, dict[int, dict[str, dict[str, Any]]]] = {}
    for record in parsed:
        trial_id = record["trial_id"]
        if trial_id in trial_ids:
            raise BenchmarkError(f"duplicate trial_id: {trial_id}")
        trial_ids.add(trial_id)
        for item in record.get("process_metrics") or []:
            session_id = item.get("session_id")
            if session_id:
                if session_id in session_ids:
                    raise BenchmarkError(f"duplicate session_id: {session_id}")
                session_ids.add(session_id)
        for route in record.get("route_evidence") or []:
            task_id = route.get("task_id")
            if task_id:
                if task_id in route_task_ids:
                    raise BenchmarkError(f"duplicate route task_id: {task_id}")
                route_task_ids.add(task_id)
        case = grouped.setdefault(record["case_id"], {})
        repetition = case.setdefault(record["repetition"], {})
        variant = record["variant"]
        if variant in repetition:
            raise BenchmarkError(
                f"case {record['case_id']!r} repetition {record['repetition']} has duplicate {variant} trial"
            )
        repetition[variant] = record
    for case_id, repetitions in sorted(grouped.items()):
        if len(repetitions) < minimum_trials:
            raise BenchmarkError(f"case {case_id!r} needs at least {minimum_trials} repeated trials")
        fingerprints = {record["case_fingerprint"] for repetition in repetitions.values() for record in repetition.values()}
        if len(fingerprints) != 1:
            raise BenchmarkError(f"incomparable case {case_id!r}: case_fingerprint changes across trials")
        checks = {tuple(record["acceptance_checks"]) for repetition in repetitions.values() for record in repetition.values()}
        if len(checks) != 1:
            raise BenchmarkError(f"incomparable case {case_id!r}: acceptance checks differ across variants or repetitions")
        for repetition_number, variants in sorted(repetitions.items()):
            if V2_BASELINE_VARIANT not in variants or "astral-guided" not in variants:
                missing = [variant for variant in (V2_BASELINE_VARIANT, "astral-guided") if variant not in variants]
                raise BenchmarkError(
                    f"incomparable case {case_id!r} repetition {repetition_number}: missing {', '.join(missing)}"
                )
        present_variants = {variant for repetition in repetitions.values() for variant in repetition}
        for variant in present_variants:
            variant_records = [repetition[variant] for repetition in repetitions.values() if variant in repetition]
            if len(variant_records) != len(repetitions):
                raise BenchmarkError(f"incomparable {variant} trials for case {case_id!r}: repeated trial numbers differ")
            route_configs = {
                tuple(sorted({(
                    item["role"], item["model"], item["expected_model"],
                    item["expected_effort"], item["expected_sandbox"],
                ) for item in record["route_evidence"]}))
                for record in variant_records
            }
            observed = {
                tuple(sorted({(
                    item["role"], item["model"], item["expected_model"],
                    item["expected_effort"], item["effort"], item["sandbox"],
                ) for item in record["route_evidence"]}))
                for record in variant_records
            }
            if len(route_configs) != 1:
                raise BenchmarkError(f"incomparable {variant} trials for case {case_id!r}: route configuration changes across repetitions")
            if len(observed) != 1:
                raise BenchmarkError(f"incomparable {variant} trials for case {case_id!r}: observed route effort changes across repetitions")
    return grouped


def ensure_optional_metric_availability(trials: list[Trial]) -> None:
    for field in (
        "input_tokens",
        "cached_input_tokens",
        "output_tokens",
        "reasoning_output_tokens",
        "quality_score",
    ):
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
    cached_input_tokens = optional_mean(trials, "cached_input_tokens")
    output_tokens = optional_mean(trials, "output_tokens")
    reasoning_output_tokens = optional_mean(trials, "reasoning_output_tokens")
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
        "mean_cached_input_tokens": cached_input_tokens,
        "mean_output_tokens": output_tokens,
        "mean_reasoning_output_tokens": reasoning_output_tokens,
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
        "mean_cached_input_tokens": difference(
            astral["mean_cached_input_tokens"], control["mean_cached_input_tokens"]
        ),
        "mean_output_tokens": difference(
            astral["mean_output_tokens"], control["mean_output_tokens"]
        ),
        "mean_reasoning_output_tokens": difference(
            astral["mean_reasoning_output_tokens"], control["mean_reasoning_output_tokens"]
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


V2_NUMERIC_METRICS = (
    "success_rate", "first_pass_acceptance_rate", "rework_rate", "route_correct_rate",
    "mean_wall_time_seconds", "mean_model_calls", "mean_input_tokens",
    "mean_cached_input_tokens", "mean_output_tokens", "mean_reasoning_output_tokens",
    "mean_total_tokens", "mean_judge_score", "quality_per_10000_strategy_tokens",
    "quality_per_elapsed_minute",
)
V2_BOOTSTRAP_SEED = 20260804
V2_BOOTSTRAP_SAMPLES = 4000


def _v2_mean(values: list[float | int]) -> float:
    return sum(float(value) for value in values) / len(values)


def _v2_optional_mean(values: list[float | int | None]) -> float | None:
    if not values or any(value is None for value in values):
        return None
    return _v2_mean([value for value in values if value is not None])


def _v2_trial_summary(records: list[dict[str, Any]]) -> dict[str, Any]:
    tokens = [record["aggregate_tokens"] for record in records]
    scores = [record["blind_judge"]["score"] for record in records]
    mean_wall = _v2_optional_mean([record["wall_time_seconds"] for record in records])
    mean_model_calls = _v2_optional_mean([record["model_calls"] for record in records])
    token_means = {
        field: _v2_optional_mean([
            item[field] if item is not None else None for item in tokens
        ])
        for field in V2_TOKEN_FIELDS
    }
    mean_total = token_means["total_tokens"]
    mean_score = _v2_optional_mean(scores)
    process_values: dict[str, float | None] = {}
    telemetry_complete = all(
        record.get("process_metrics")
        and all(V2_TOKEN_FIELDS | {"duration_seconds"} <= set(item) for item in record["process_metrics"])
        for record in records
    )
    for field in V2_TOKEN_FIELDS:
        process_values[field] = (
            _v2_mean([sum(float(item[field]) for item in record["process_metrics"]) for record in records])
            if telemetry_complete else None
        )
    quality_per_tokens = mean_score / mean_total * 10000 if mean_score is not None and mean_total is not None and mean_total > 0 else None
    quality_per_minute = mean_score / (mean_wall / 60) if mean_score is not None and mean_wall is not None and mean_wall > 0 else None
    summary: dict[str, Any] = {
        "trial_count": len(records),
        "success_rate": _v2_mean([float(record["accepted"]) for record in records]),
        "first_pass_acceptance_rate": _v2_mean([float(record["first_pass_accepted"]) for record in records]),
        "rework_rate": _v2_mean([float(record["rework_required"]) for record in records]),
        "route_correct_rate": _v2_mean([float(record["route_correct"]) for record in records]),
        "mean_wall_time_seconds": mean_wall,
        "mean_model_calls": mean_model_calls,
        "mean_input_tokens": token_means["input_tokens"],
        "mean_cached_input_tokens": token_means["cached_input_tokens"],
        "mean_output_tokens": token_means["output_tokens"],
        "mean_reasoning_output_tokens": token_means["reasoning_output_tokens"],
        "mean_total_tokens": mean_total,
        "mean_judge_score": mean_score,
        "mean_quality_score": mean_score,
        "judge_quality_blinded_rate": _v2_mean([float(record["blind_judge"]["blinded"]) for record in records]),
        "quality_score_blinded_rate": _v2_mean([float(record["blind_judge"]["blinded"]) for record in records]),
        "quality_per_10000_strategy_tokens": quality_per_tokens,
        "quality_per_elapsed_minute": quality_per_minute,
        "failure_count": sum(record["failure"] is not None for record in records),
        "timeout_count": sum(bool(record["timeout"]) for record in records),
        "disclosure_count": sum(len(record.get("disclosures", [])) + len(record.get("process_disclosures", [])) for record in records),
        "disclosures": sorted({
            disclosure
            for record in records
            for disclosure in [*record.get("disclosures", []), *record.get("process_disclosures", [])]
        }),
        "mean_process_input_tokens": process_values["input_tokens"],
        "mean_process_cached_input_tokens": process_values["cached_input_tokens"],
        "mean_process_output_tokens": process_values["output_tokens"],
        "mean_process_reasoning_output_tokens": process_values["reasoning_output_tokens"],
        "mean_process_total_tokens": process_values["total_tokens"],
    }
    return summary


def _paired_bootstrap_ci(deltas: list[float], *, seed: int = V2_BOOTSTRAP_SEED, samples: int = V2_BOOTSTRAP_SAMPLES) -> dict[str, float] | None:
    if not deltas:
        return None
    if len(deltas) == 1:
        return {"lower": deltas[0], "upper": deltas[0]}
    rng = random.Random(seed)
    means: list[float] = []
    count = len(deltas)
    for _ in range(samples):
        means.append(sum(deltas[rng.randrange(count)] for _ in range(count)) / count)
    means.sort()
    def percentile(fraction: float) -> float:
        index = (len(means) - 1) * fraction
        lower = math.floor(index)
        upper = math.ceil(index)
        if lower == upper:
            return means[lower]
        return means[lower] + (means[upper] - means[lower]) * (index - lower)
    return {"lower": percentile(0.025), "upper": percentile(0.975)}


def _v2_ratio_of_means_comparison(
    pairs: list[tuple[dict[str, Any], dict[str, Any]]], metric: str,
) -> tuple[float | None, dict[str, float] | None]:
    variant_records = [pair[0] for pair in pairs]
    baseline_records = [pair[1] for pair in pairs]
    variant_value = _v2_trial_summary(variant_records).get(metric)
    baseline_value = _v2_trial_summary(baseline_records).get(metric)
    if variant_value is None or baseline_value is None:
        return None, None
    point = float(variant_value) - float(baseline_value)
    if len(pairs) == 1:
        return point, {"lower": point, "upper": point}
    rng = random.Random(V2_BOOTSTRAP_SEED)
    estimates: list[float] = []
    for _ in range(V2_BOOTSTRAP_SAMPLES):
        sample = [pairs[rng.randrange(len(pairs))] for _ in pairs]
        sample_variant = _v2_trial_summary([pair[0] for pair in sample]).get(metric)
        sample_baseline = _v2_trial_summary([pair[1] for pair in sample]).get(metric)
        if sample_variant is None or sample_baseline is None:
            return point, None
        estimates.append(float(sample_variant) - float(sample_baseline))
    estimates.sort()

    def percentile(fraction: float) -> float:
        index = (len(estimates) - 1) * fraction
        lower = math.floor(index)
        upper = math.ceil(index)
        if lower == upper:
            return estimates[lower]
        return estimates[lower] + (estimates[upper] - estimates[lower]) * (index - lower)

    return point, {"lower": percentile(0.025), "upper": percentile(0.975)}


def _v2_compare(variant_records: list[dict[str, Any]], baseline_records: list[dict[str, Any]]) -> dict[str, Any]:
    pairs = sorted(
        zip(variant_records, baseline_records),
        key=lambda pair: (pair[0]["case_id"], pair[0]["repetition"]),
    )
    deltas: dict[str, float | None] = {}
    comparison: dict[str, Any] = {}
    for metric in V2_NUMERIC_METRICS:
        if metric in {"quality_per_10000_strategy_tokens", "quality_per_elapsed_minute"}:
            delta, ci = _v2_ratio_of_means_comparison(pairs, metric)
            deltas[metric] = delta
            comparison[metric] = {"delta": delta, "ci95": ci}
            continue
        values: list[float] = []
        for variant, baseline in pairs:
            variant_summary = _v2_trial_summary([variant])
            baseline_summary = _v2_trial_summary([baseline])
            variant_value = variant_summary.get(metric)
            baseline_value = baseline_summary.get(metric)
            if variant_value is None or baseline_value is None:
                values = []
                break
            values.append(float(variant_value) - float(baseline_value))
        delta = _v2_mean(values) if values else None
        ci = _paired_bootstrap_ci(values)
        deltas[metric] = delta
        comparison[metric] = {"delta": delta, "ci95": ci}
    comparison["deltas"] = deltas
    comparison["paired_trial_count"] = len(pairs)
    comparison["bootstrap_seed"] = V2_BOOTSTRAP_SEED
    comparison["bootstrap_samples"] = V2_BOOTSTRAP_SAMPLES
    return comparison


def build_v2_report(grouped: dict[str, dict[int, dict[str, dict[str, Any]]]], minimum_trials: int) -> dict[str, Any]:
    if isinstance(grouped, list):
        grouped = validate_v2_records(grouped, minimum_trials)
    by_variant: dict[str, list[dict[str, Any]]] = {}
    for repetitions in grouped.values():
        for variants in repetitions.values():
            for variant, record in variants.items():
                by_variant.setdefault(variant, []).append(record)
    summaries = {variant: _v2_trial_summary(records) for variant, records in sorted(by_variant.items())}
    all_disclosures = sorted({
        disclosure
        for summary in summaries.values()
        for disclosure in summary["disclosures"]
    })
    if "single-sol-max" not in summaries:
        all_disclosures.append("single-sol-max absent; no unsupported variant was inferred")
    comparisons: dict[str, Any] = {}
    for variant in sorted(summaries):
        if variant == V2_BASELINE_VARIANT:
            continue
        paired_variant: list[dict[str, Any]] = []
        paired_baseline: list[dict[str, Any]] = []
        for case_id, repetitions in sorted(grouped.items()):
            for repetition, variants in sorted(repetitions.items()):
                if variant in variants and V2_BASELINE_VARIANT in variants:
                    paired_variant.append(variants[variant])
                    paired_baseline.append(variants[V2_BASELINE_VARIANT])
        comparisons[f"{variant}_vs_{V2_BASELINE_VARIANT}"] = _v2_compare(paired_variant, paired_baseline)
    cases: dict[str, Any] = {}
    for case_id, repetitions in sorted(grouped.items()):
        case_variants: dict[str, Any] = {}
        for variant in sorted({variant for variants in repetitions.values() for variant in variants}):
            case_records = [variants[variant] for variants in repetitions.values() if variant in variants]
            case_variants[variant] = _v2_trial_summary(case_records)
        case_comparisons: dict[str, Any] = {}
        baseline_case = [
            variants[V2_BASELINE_VARIANT]
            for variants in repetitions.values()
            if V2_BASELINE_VARIANT in variants
        ]
        for variant in sorted(case_variants):
            if variant == V2_BASELINE_VARIANT:
                continue
            variant_case = [
                variants[variant]
                for variants in repetitions.values()
                if variant in variants and V2_BASELINE_VARIANT in variants
            ]
            case_comparisons[f"{variant}_vs_{V2_BASELINE_VARIANT}"] = _v2_compare(
                variant_case, baseline_case
            )
        cases[case_id] = {
            "case_fingerprint": next(iter({record["case_fingerprint"] for variants in repetitions.values() for record in variants.values()})),
            "repetition_count": len(repetitions),
            "variants": case_variants,
            "comparisons": case_comparisons,
        }
    warnings: list[str] = []
    for variant, summary in summaries.items():
        if summary["route_correct_rate"] < 1:
            warnings.append(f"{variant} route correctness is below 100%; investigate route deviations")
        if summary["failure_count"] or summary["timeout_count"]:
            warnings.append(f"{variant} includes failed or timed-out trials")
    comparability = {
        "baseline_variant": V2_BASELINE_VARIANT,
        "case_count": len(grouped),
        "paired_trial_count": sum(1 for repetitions in grouped.values() for variants in repetitions.values() if V2_BASELINE_VARIANT in variants),
        "minimum_trials_required": minimum_trials,
        "variants_present": sorted(summaries),
        "repetitions_by_case": {case_id: len(repetitions) for case_id, repetitions in sorted(grouped.items())},
        "bootstrap_seed": V2_BOOTSTRAP_SEED,
        "bootstrap_samples": V2_BOOTSTRAP_SAMPLES,
    }
    return {
        "schema_version": SCHEMA_V2_VERSION,
        "comparability": comparability,
        "cases": cases,
        "variants": summaries,
        "strategies": summaries,
        "comparisons": comparisons,
        "disclosures": sorted(set(all_disclosures)),
        "warnings": warnings,
    }


def text_report_v2(report: dict[str, Any]) -> str:
    lines = [
        "Astral Orchestrator benchmark scorecard (schema v2)",
        f"Comparable cases: {report['comparability']['case_count']} | paired trials: {report['comparability']['paired_trial_count']}",
        "",
        "Variant             Success   First pass   Rework   Route   Wall time   Tokens   Judge",
        "------------------  --------  -----------  -------  ------  ----------  -------  ------",
    ]
    for variant, summary in report["variants"].items():
        lines.append(
            f"{variant:<18}  {100 * summary['success_rate']:>7.1f}%  {100 * summary['first_pass_acceptance_rate']:>10.1f}%  "
            f"{100 * summary['rework_rate']:>6.1f}%  {100 * summary['route_correct_rate']:>5.1f}%  "
            f"{format_value(summary['mean_wall_time_seconds'], suffix='s'):>10}  "
            f"{format_value(summary['mean_total_tokens']):>7}  "
            f"{format_value(summary['mean_judge_score']):>6}"
        )
    if report["warnings"] or report["disclosures"]:
        lines.append("")
        lines.extend(f"WARNING: {item}" for item in [*report["warnings"], *report["disclosures"]])
    return "\n".join(lines)


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
        records = load_records(args.trials)
        if records and isinstance(records[0], Trial):
            grouped = validate_comparability(records, args.min_trials)
            report = build_report(grouped, args.min_trials)
        else:
            grouped = validate_v2_records(records, args.min_trials)
            report = build_v2_report(grouped, args.min_trials)
    except BenchmarkError as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 2

    if args.format == "json":
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(text_report_v2(report) if report["schema_version"] == SCHEMA_V2_VERSION else text_report(report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
