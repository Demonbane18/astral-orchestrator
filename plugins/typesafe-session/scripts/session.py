#!/usr/bin/env python3
"""Small, secret-free per-session switch shared with Astral's route selector."""

from __future__ import annotations

import json
import os
import re
import sys
import tempfile
from pathlib import Path

SESSION_ID = re.compile(r"[A-Za-z0-9_-]{8,128}\Z")
COMMAND = re.compile(r"\s*typesafe\s+(on|off|status)\s*\Z", re.I)
MARKER = "TypeSafe session: on"


def state_path(session_id: str) -> Path:
    if not SESSION_ID.fullmatch(session_id):
        raise ValueError("invalid session id")
    home = Path(os.environ.get("CODEX_HOME", Path.home() / ".codex")).expanduser()
    return home / "typesafe-session" / "sessions" / f"{session_id}.json"


def project_default(cwd: str) -> bool:
    root = Path(cwd).resolve()
    guide = root / "AGENTS.md"
    if guide.is_symlink() or not guide.is_file() or guide.stat().st_size > 100_000:
        return False
    return MARKER in guide.read_text(encoding="utf-8").splitlines()


def read_state(path: Path, cwd: str) -> dict[str, object]:
    if path.is_symlink():
        raise ValueError("session state is a symlink")
    if path.is_file():
        state = json.loads(path.read_text(encoding="utf-8"))
        if state.get("project") == str(Path(cwd).resolve()) and state.get("mode") in {"on", "off"}:
            return state
    return {"project": str(Path(cwd).resolve()), "mode": "on" if project_default(cwd) else "off", "explicit": False}


def save_state(path: Path, state: dict[str, object]) -> None:
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    if path.parent.is_symlink() or path.is_symlink():
        raise ValueError("unsafe session state path")
    fd, temporary_name = tempfile.mkstemp(prefix=".typesafe-session-", suffix=".tmp", dir=path.parent)
    temporary = Path(temporary_name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(state, handle, separators=(",", ":"))
            handle.write("\n")
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def hook(event: dict[str, object]) -> dict[str, object]:
    session_id = event.get("session_id")
    cwd = event.get("cwd")
    name = event.get("hook_event_name")
    if not isinstance(session_id, str) or not isinstance(cwd, str):
        return {}
    path = state_path(session_id)
    if name == "SessionEnd":
        path.unlink(missing_ok=True)
        return {}
    state = read_state(path, cwd)
    if name == "UserPromptSubmit":
        prompt = event.get("prompt")
        command = COMMAND.fullmatch(prompt) if isinstance(prompt, str) else None
        if command and command.group(1).lower() != "status":
            state["mode"] = command.group(1).lower()
            state["explicit"] = True
    save_state(path, state)
    return {"hookSpecificOutput": {"hookEventName": name,
            "additionalContext": f"TypeSafe/Jev is {state['mode']} for session {session_id}. "
            "Only use Jev for bounded semantic judgments; permissions and execution remain in code."}}


def main() -> int:
    try:
        if len(sys.argv) == 2 and sys.argv[1] == "hook":
            print(json.dumps(hook(json.load(sys.stdin)), separators=(",", ":")))
        elif len(sys.argv) == 3 and sys.argv[1] == "status":
            path = state_path(sys.argv[2])
            print(json.dumps(read_state(path, os.getcwd()), separators=(",", ":")))
        elif len(sys.argv) == 5 and sys.argv[1] == "set" and sys.argv[4] in {"on", "off"}:
            path = state_path(sys.argv[2])
            project = str(Path(sys.argv[3]).resolve())
            state = {"project": project, "mode": sys.argv[4], "explicit": True}
            save_state(path, state)
            print(json.dumps(state, separators=(",", ":")))
        else:
            print("usage: session.py hook | status SESSION_ID | set SESSION_ID PROJECT_ROOT on|off", file=sys.stderr)
            return 2
    except (OSError, ValueError, json.JSONDecodeError) as error:
        print(f"TypeSafe session error: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
