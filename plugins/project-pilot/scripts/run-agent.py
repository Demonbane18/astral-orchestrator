#!/usr/bin/env python3
"""Launch one exact Project Pilot lane as a separate Codex process."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import stat
import subprocess
import sys
import tomllib
from pathlib import Path
from typing import NoReturn


ROLE_CONTRACTS = {
    "luna": {
        "filename": "project-pilot-luna-implementer.toml",
        "agent_name": "project_pilot_luna_implementer",
        "model": "gpt-5.6-luna",
        "effort": "xhigh",
        "sandbox": "workspace-write",
    },
    "terra": {
        "filename": "project-pilot-terra-implementer.toml",
        "agent_name": "project_pilot_terra_implementer",
        "model": "gpt-5.6-terra",
        "effort": "xhigh",
        "sandbox": "workspace-write",
    },
    "reviewer": {
        "filename": "project-pilot-sol-reviewer.toml",
        "agent_name": "project_pilot_sol_reviewer",
        "model": "gpt-5.6-sol",
        "effort": "high",
        "sandbox": "read-only",
    },
}
MAX_PROMPT_BYTES = 1_048_576


def fail(message: str) -> NoReturn:
    print(f"ERROR: {message}", file=sys.stderr)
    raise SystemExit(1)


def regular_file(path: Path, label: str) -> Path:
    if path.is_symlink() or not path.is_file():
        fail(f"{label} must be a real regular file: {path}")
    return path


def read_prompt(path: Path) -> bytes:
    flags = os.O_RDONLY
    if hasattr(os, "O_CLOEXEC"):
        flags |= os.O_CLOEXEC
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW

    try:
        descriptor = os.open(path, flags)
    except OSError:
        fail(f"prompt file must be a readable regular file: {path}")

    try:
        try:
            details = os.fstat(descriptor)
            if not stat.S_ISREG(details.st_mode):
                fail(f"prompt file must be a real regular file: {path}")
            if details.st_size == 0 or details.st_size > MAX_PROMPT_BYTES:
                fail(f"prompt file must contain 1 to {MAX_PROMPT_BYTES} bytes")

            chunks = []
            remaining = MAX_PROMPT_BYTES + 1
            while remaining:
                chunk = os.read(descriptor, min(65_536, remaining))
                if not chunk:
                    break
                chunks.append(chunk)
                remaining -= len(chunk)
            prompt = b"".join(chunks)
        except OSError:
            fail(f"prompt file could not be read safely: {path}")
    finally:
        os.close(descriptor)

    if not prompt or len(prompt) > MAX_PROMPT_BYTES:
        fail(f"prompt file must contain 1 to {MAX_PROMPT_BYTES} bytes")
    return prompt


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run one model-pinned Project Pilot worker or reviewer."
    )
    parser.add_argument("--role", required=True, choices=sorted(ROLE_CONTRACTS))
    parser.add_argument("--workdir", required=True)
    parser.add_argument("--prompt-file", required=True)
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate and print allowlisted route settings without starting Codex.",
    )
    return parser.parse_args()


def main() -> int:
    if sys.version_info < (3, 11):
        fail("Python 3.11 or newer is required.")

    args = parse_args()
    script_dir = Path(__file__).resolve().parent
    profile_dir = script_dir.parent / "agents"
    contract = ROLE_CONTRACTS[args.role]
    profile_path = regular_file(profile_dir / contract["filename"], "agent profile")

    with profile_path.open("rb") as handle:
        profile = tomllib.load(handle)
    for field in ("agent_name", "model", "effort"):
        profile_field = "name" if field == "agent_name" else (
            "model_reasoning_effort" if field == "effort" else field
        )
        if profile.get(profile_field) != contract[field]:
            fail(
                f"{profile_path.name} must set {profile_field} to {contract[field]}"
            )
    if args.role == "reviewer" and profile.get("sandbox_mode") != "read-only":
        fail("the reviewer profile must request a read-only sandbox")

    instructions = profile.get("developer_instructions")
    if not isinstance(instructions, str) or not instructions.strip():
        fail(f"{profile_path.name} has no developer instructions")

    prompt_path = Path(args.prompt_file).expanduser()
    prompt = read_prompt(prompt_path)
    prompt_bytes = len(prompt)

    workdir = Path(args.workdir).expanduser().resolve()
    if not workdir.is_dir():
        fail(f"workdir must be an existing directory: {workdir}")

    evidence = {
        "role": args.role,
        "agent_name": contract["agent_name"],
        "model": contract["model"],
        "effort": contract["effort"],
        "sandbox": contract["sandbox"],
        "workdir": str(workdir),
        "prompt_bytes": prompt_bytes,
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
        contract["model"],
        "-c",
        f"model_reasoning_effort={json.dumps(contract['effort'])}",
        "-c",
        f"developer_instructions={json.dumps(instructions)}",
        "--sandbox",
        contract["sandbox"],
        "--skip-git-repo-check",
        "--cd",
        str(workdir),
        "-",
    ]

    print(
        "PROJECT_PILOT_ROUTE "
        + json.dumps(evidence, separators=(",", ":"), sort_keys=True),
        flush=True,
    )
    result = subprocess.run(command, input=prompt, check=False)
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
