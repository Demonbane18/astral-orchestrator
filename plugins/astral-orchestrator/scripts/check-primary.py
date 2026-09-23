#!/usr/bin/env python3
"""Verify the current primary route from allowlisted local runtime evidence."""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import NoReturn

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from effort_settings import ALLOWED_EFFORTS  # noqa: E402


SUPPORTED_PRIMARY_MODELS = {
    "gpt-6-sol": "Sol",
    "gpt-6-luna": "Luna",
    "gpt-6-astra": "Astra",
    "gpt-5.6-sol": "Legacy Sol",
}
PRIMARY_EFFORTS = ("none", "light", *ALLOWED_EFFORTS)
THREAD_ID_PATTERN = re.compile(
    r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}"
)
MODEL_PATTERN = re.compile(r"[A-Za-z0-9][A-Za-z0-9._:/-]{0,255}")
ALLOWED_STATUSES = {"match", "mismatch", "invalid", "unavailable"}
ALLOWED_REASONS = {
    "primary-route-match",
    "primary-route-mismatch",
    "thread-id-invalid",
    "thread-id-unavailable",
    "sessions-directory-unavailable",
    "rollout-unavailable",
    "rollout-ambiguous",
    "runtime-evidence-invalid",
}


def fail(message: str) -> NoReturn:
    print(f"ERROR: {message}", file=sys.stderr)
    raise SystemExit(1)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Detect the supported model and effort of the current Astral primary."
    )
    parser.add_argument(
        "--thread-id",
        default=os.environ.get("CODEX_THREAD_ID"),
        help="Codex thread id; defaults to CODEX_THREAD_ID.",
    )
    parser.add_argument(
        "--sessions-dir",
        type=Path,
        help="Override the Codex sessions directory (intended for local inspection).",
    )
    parser.add_argument(
        "--settings-file",
        type=Path,
        help=argparse.SUPPRESS,
    )
    strict = parser.add_mutually_exclusive_group()
    strict.add_argument(
        "--require-sol-ultra",
        action="store_true",
        help="Optionally require a Sol Ultra primary. No mode requires this flag.",
    )
    strict.add_argument(
        "--require-astra-ultra",
        action="store_true",
        help="Optionally require an Astra Ultra primary. No mode requires this flag.",
    )
    return parser.parse_args()


def resolve_sessions_dir(configured: Path | None) -> Path:
    """Match the bundled inspector's default session location without reading rollouts."""
    if configured is not None:
        return configured
    codex_home = os.environ.get("CODEX_HOME")
    if codex_home:
        return Path(codex_home).expanduser() / "sessions"
    return Path.home() / ".codex" / "sessions"


def find_rollouts(sessions_dir: Path, thread_id: str) -> list[Path] | None:
    """Count only matching rollout filenames; rollout contents stay inspector-owned."""
    try:
        if not sessions_dir.is_dir():
            return None
        return [
            path
            for path in sessions_dir.rglob(f"rollout-*-{thread_id}.jsonl")
            if path.is_file()
        ]
    except OSError:
        return None


def emit(
    status: str,
    reason: str,
    expected_effort: str,
    expected_model: str,
    *,
    thread_id: str | None = None,
    observed_model: str | None = None,
    observed_effort: str | None = None,
) -> None:
    if status not in ALLOWED_STATUSES or reason not in ALLOWED_REASONS:
        fail("internal primary-evidence contract error")

    evidence: dict[str, str] = {
        "expected_effort": expected_effort,
        "expected_model": expected_model,
        "reason": reason,
        "status": status,
    }
    if thread_id is not None:
        evidence["thread_id"] = thread_id
    if observed_model is not None:
        evidence["observed_model"] = observed_model
    if observed_effort is not None:
        evidence["observed_effort"] = observed_effort
    print(json.dumps(evidence, separators=(",", ":"), sort_keys=True))


def main() -> int:
    if sys.version_info < (3, 11):
        fail("Python 3.11 or newer is required.")

    args = parse_args()
    strict_model = None
    if args.require_sol_ultra:
        strict_model = "gpt-5.6-sol"
    elif args.require_astra_ultra:
        strict_model = "gpt-6-astra"
    expected_model = strict_model or "|".join(SUPPORTED_PRIMARY_MODELS)
    expected_effort = "ultra" if strict_model else "any-supported"

    thread_id = args.thread_id
    if thread_id is None:
        emit("unavailable", "thread-id-unavailable", expected_effort, expected_model)
        return 1
    if not isinstance(thread_id, str) or not THREAD_ID_PATTERN.fullmatch(thread_id):
        emit("invalid", "thread-id-invalid", expected_effort, expected_model)
        return 1

    sessions_dir = resolve_sessions_dir(args.sessions_dir)
    rollouts = find_rollouts(sessions_dir, thread_id)
    if rollouts is None:
        emit(
            "unavailable",
            "sessions-directory-unavailable",
            expected_effort,
            expected_model,
            thread_id=thread_id,
        )
        return 1
    if not rollouts:
        emit("unavailable", "rollout-unavailable", expected_effort, expected_model, thread_id=thread_id)
        return 1
    if len(rollouts) != 1:
        emit("invalid", "rollout-ambiguous", expected_effort, expected_model, thread_id=thread_id)
        return 1

    command = [
        "sh",
        str(SCRIPT_DIR / "inspect-agent-runtime.sh"),
        "--sessions-dir",
        str(sessions_dir),
        "--thread-id",
        thread_id,
    ]
    inspected = subprocess.run(command, check=False, capture_output=True, text=True)
    if inspected.returncode != 0:
        emit(
            "invalid",
            "runtime-evidence-invalid",
            expected_effort,
            expected_model,
            thread_id=thread_id,
        )
        return 1

    try:
        observed = json.loads(inspected.stdout)
    except json.JSONDecodeError:
        emit(
            "invalid",
            "runtime-evidence-invalid",
            expected_effort,
            expected_model,
            thread_id=thread_id,
        )
        return 1

    if not isinstance(observed, dict):
        emit(
            "invalid",
            "runtime-evidence-invalid",
            expected_effort,
            expected_model,
            thread_id=thread_id,
        )
        return 1

    observed_thread_id = observed.get("thread_id")
    observed_model = observed.get("model")
    observed_effort = observed.get("effort")
    if (
        observed_thread_id != thread_id
        or not isinstance(observed_model, str)
        or not MODEL_PATTERN.fullmatch(observed_model)
        or not isinstance(observed_effort, str)
        or observed_effort not in PRIMARY_EFFORTS
    ):
        emit(
            "invalid",
            "runtime-evidence-invalid",
            expected_effort,
            expected_model,
            thread_id=thread_id,
        )
        return 1

    if strict_model is None:
        expected_effort = observed_effort
    matches_model = observed_model in SUPPORTED_PRIMARY_MODELS
    if strict_model is not None:
        matches_model = observed_model == strict_model
    matches = matches_model and observed_effort == expected_effort
    emit(
        "match" if matches else "mismatch",
        "primary-route-match" if matches else "primary-route-mismatch",
        expected_effort,
        expected_model,
        thread_id=thread_id,
        observed_model=observed_model,
        observed_effort=observed_effort,
    )
    return 0 if matches else 1


if __name__ == "__main__":
    raise SystemExit(main())
