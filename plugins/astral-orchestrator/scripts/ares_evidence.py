"""Read only confirmed Ares checkpoint fields for the current Codex turn."""

from __future__ import annotations

import json
import os
import stat
from pathlib import Path

SELECTIONS = {"Astra-Jev": "gpt-6-astra", "Sol-Jev": "gpt-6-sol", "Luna-Jev": "gpt-6-luna"}
EFFORTS = {"low", "medium", "high", "xhigh", "max", "ultra"}


def private_socket(path: str | None) -> bool:
    if not path:
        return False
    socket = Path(path)
    if not socket.is_absolute() or socket.is_symlink():
        return False
    try:
        info = socket.stat()
    except OSError:
        return False
    return stat.S_ISSOCK(info.st_mode) and not stat.S_IMODE(info.st_mode) & 0o077 and (
        not hasattr(os, "getuid") or info.st_uid == os.getuid()
    )


def _private_file(path: Path) -> bool:
    if path.is_symlink():
        return False
    try:
        info = path.stat()
    except OSError:
        return False
    return stat.S_ISREG(info.st_mode) and info.st_size <= 2_000_000 and not stat.S_IMODE(info.st_mode) & 0o077 and (
        not hasattr(os, "getuid") or info.st_uid == os.getuid()
    )


def observed_ares_primary(thread_id: str, rollout: Path, runs_dir: Path,
                          socket_path: str | None) -> dict[str, str] | None:
    """Return a route only when rollout identity and native application agree."""
    if not private_socket(socket_path) or not rollout.is_file() or rollout.is_symlink():
        return None
    session_id = None
    turn = None
    try:
        with rollout.open(encoding="utf-8") as handle:
            for line in handle:
                if '"session_meta"' not in line and '"turn_context"' not in line:
                    continue
                event = json.loads(line)
                if event.get("type") == "session_meta":
                    session_id = event.get("payload", {}).get("id")
                elif event.get("type") == "turn_context":
                    payload = event.get("payload", {})
                    turn = (payload.get("turn_id"), payload.get("model"))
    except (OSError, ValueError, AttributeError):
        return None
    if session_id != thread_id or not turn or turn[1] not in SELECTIONS or not isinstance(turn[0], str):
        return None
    if not runs_dir.is_dir() or runs_dir.is_symlink():
        return None
    matches = []
    try:
        run_logs = list(runs_dir.glob("*/decisions.jsonl"))
        if len(run_logs) > 500:
            return None
        for path in run_logs:
            if path.parent.is_symlink() or not _private_file(path):
                continue
            decisions = {}
            applied = set()
            with path.open(encoding="utf-8") as handle:
                for line in handle:
                    event = json.loads(line)
                    if event.get("threadId") != thread_id or event.get("turnId") != turn[0]:
                        continue
                    step = event.get("step")
                    if not isinstance(step, int) or step < 1:
                        continue
                    if event.get("type") == "decision" and event.get("confirmation") == "native_step_context_captured":
                        decisions[step] = event
                    elif event.get("type") == "effort_selected" and event.get("confirmation") == "native_step_context_captured":
                        applied.add((step, event.get("to")))
            for step, event in decisions.items():
                model, effort = event.get("model"), event.get("effort")
                if model == SELECTIONS[turn[1]] and effort in EFFORTS and (model == "gpt-6-astra" or effort != "ultra") and (step, effort) in applied:
                    matches.append((path.stat().st_mtime, step, model, effort))
    except (OSError, ValueError, AttributeError):
        return None
    if not matches:
        return None
    _, _, model, effort = max(matches)
    return {"thread_id": thread_id, "model": model, "effort": effort}
