#!/usr/bin/env python3
"""Launch one explicit Morph worker through the user's existing Codex route."""

from __future__ import annotations

import argparse
import importlib.util
import json
import shutil
import subprocess
import sys
from pathlib import Path
from typing import NoReturn

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from effort_settings import ALLOWED_EFFORTS  # noqa: E402


MODEL_CHARACTERS = frozenset(
    "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789._:/-"
)
MAX_MODEL_LENGTH = 256
MORPH_DEVELOPER_INSTRUCTIONS = """\
You are an Astral Orchestrator Morph implementation worker. Execute only the bounded
work card provided on standard input. Preserve unrelated and concurrent edits, surface
material ambiguity instead of redesigning requirements or architecture, and report
the actual changes and checks. Perform the work directly; you must not spawn or delegate
to another agent.
"""


def fail(message: str) -> NoReturn:
    print(f"ERROR: {message}", file=sys.stderr)
    raise SystemExit(1)


def load_shared_prompt_reader():
    """Load the established private-packet checks without importing a new dependency."""
    specification = importlib.util.spec_from_file_location(
        "astral_orchestrator_run_agent_shared", SCRIPT_DIR / "run-agent.py"
    )
    if specification is None or specification.loader is None:
        fail("the bundled private-packet validator is unavailable")
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    reader = getattr(module, "read_prompt", None)
    if not callable(reader):
        fail("the bundled private-packet validator is invalid")
    return reader


def valid_model(value: str) -> str:
    parts = value.split("/")
    if (
        not value
        or len(value) > MAX_MODEL_LENGTH
        or value[0] in ".:/-"
        or any(not part for part in parts)
        or any(character not in MODEL_CHARACTERS for character in value)
    ):
        raise argparse.ArgumentTypeError(
            "model must be a non-secret provider/model or native model identifier"
        )
    return value


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run one explicit, user-selected Astral Morph worker."
    )
    parser.add_argument("--model", required=True, type=valid_model)
    parser.add_argument("--effort", required=True, choices=ALLOWED_EFFORTS)
    parser.add_argument("--workdir", required=True)
    parser.add_argument("--prompt-file", required=True)
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate and print allowlisted Morph route settings without starting Codex.",
    )
    return parser.parse_args()


def main() -> int:
    if sys.version_info < (3, 11):
        fail("Python 3.11 or newer is required.")

    args = parse_args()
    prompt_reader = load_shared_prompt_reader()
    prompt = prompt_reader(Path(args.prompt_file).expanduser())

    workdir = Path(args.workdir).expanduser().resolve()
    if not workdir.is_dir():
        fail(f"workdir must be an existing directory: {workdir}")

    evidence = {
        "effort_semantics": "requested-only",
        "model": args.model,
        "prompt_bytes": len(prompt),
        "requested_effort": args.effort,
        "route": "morph",
        "sandbox": "workspace-write",
        "verified_upstream_native_effort": "unverified",
        "workdir": str(workdir),
    }
    if args.dry_run:
        print(json.dumps(evidence, separators=(",", ":"), sort_keys=True))
        return 0

    codex = shutil.which("codex")
    if codex is None:
        fail("the codex command is unavailable")

    command = [
        codex,
        "exec",
        "--model",
        args.model,
        "-c",
        f"model_reasoning_effort={json.dumps(args.effort)}",
        "-c",
        f"developer_instructions={json.dumps(MORPH_DEVELOPER_INSTRUCTIONS)}",
        "--sandbox",
        "workspace-write",
        "--skip-git-repo-check",
        "--cd",
        str(workdir),
        "-",
    ]
    print(
        "ASTRAL_ORCHESTRATOR_ROUTE "
        + json.dumps(evidence, separators=(",", ":"), sort_keys=True),
        flush=True,
    )
    result = subprocess.run(command, input=prompt, check=False)
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
