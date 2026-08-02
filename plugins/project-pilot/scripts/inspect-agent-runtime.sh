#!/bin/sh
# Emit only allowlisted routing metadata from one exact native subagent rollout.

set -eu

usage() {
  printf '%s\n' \
    'Usage: sh inspect-agent-runtime.sh [--sessions-dir PATH] THREAD_ID' \
    '' \
    'Return a small JSON object containing only role, model, effort, sandbox,' \
    'permission, and working-directory evidence for one subagent task.'
}

fail() {
  printf '%s\n' "ERROR: $*" >&2
  exit 1
}

sessions_dir=''
case "$#" in
  1) thread_id=$1 ;;
  3)
    [ "$1" = "--sessions-dir" ] || {
      usage >&2
      exit 2
    }
    [ -n "$2" ] || fail "--sessions-dir requires a non-empty path."
    sessions_dir=$2
    thread_id=$3
    ;;
  *)
    usage >&2
    exit 2
    ;;
esac

if [ -z "$sessions_dir" ]; then
  if [ -n "${CODEX_HOME-}" ]; then
    sessions_dir=$CODEX_HOME/sessions
  else
    [ -n "${HOME-}" ] || fail "HOME is unavailable; pass --sessions-dir explicitly."
    sessions_dir=$HOME/.codex/sessions
  fi
fi

[ -d "$sessions_dir" ] || fail "sessions directory is unavailable: $sessions_dir"
command -v python3 >/dev/null 2>&1 || fail "Python 3 is required for route inspection."

python3 - "$sessions_dir" "$thread_id" <<'PY'
import json
import re
import sys
from pathlib import Path


def fail(message):
    print(f"ERROR: {message}", file=sys.stderr)
    raise SystemExit(1)


sessions_dir = Path(sys.argv[1])
thread_id = sys.argv[2]
if not re.fullmatch(
    r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}",
    thread_id,
):
    fail("THREAD_ID must be a lowercase UUID.")

matches = [
    path
    for path in sessions_dir.rglob(f"rollout-*-{thread_id}.jsonl")
    if path.is_file()
]
if len(matches) != 1:
    fail(f"expected one rollout filename for the task; found {len(matches)}.")

records = []
try:
    with matches[0].open(encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                records.append(json.loads(line))
except (OSError, UnicodeError, json.JSONDecodeError):
    fail("the matched rollout is unreadable or contains invalid JSON.")

sessions = [item.get("payload") for item in records if item.get("type") == "session_meta"]
turns = [item.get("payload") for item in records if item.get("type") == "turn_context"]
if len(sessions) != 1 or not isinstance(sessions[0], dict):
    fail("session metadata is missing or ambiguous.")
if not turns or not all(isinstance(turn, dict) for turn in turns):
    fail("turn context is missing or invalid.")

session = sessions[0]
if session.get("id") != thread_id:
    fail("session metadata does not identify the requested task.")


def one_value(label, values):
    if any(not isinstance(value, str) or not value for value in values):
        fail(f"{label} is missing.")
    unique = set(values)
    if len(unique) != 1:
        fail(f"{label} is inconsistent across turns.")
    return values[0]


agent_role = session.get("agent_role")
if not isinstance(agent_role, str) or not agent_role:
    fail("agent role is missing.")

evidence = {
    "thread_id": thread_id,
    "parent_thread_id": session.get("parent_thread_id") if isinstance(session.get("parent_thread_id"), str) else None,
    "agent_role": agent_role,
    "agent_path": session.get("agent_path") if isinstance(session.get("agent_path"), str) else None,
    "model_provider": session.get("model_provider") if isinstance(session.get("model_provider"), str) else None,
    "model": one_value("model", [turn.get("model") for turn in turns]),
    "effort": one_value("effort", [turn.get("effort") for turn in turns]),
    "sandbox_policy_type": one_value(
        "sandbox policy",
        [turn.get("sandbox_policy", {}).get("type") for turn in turns],
    ),
    "permission_profile_type": one_value(
        "permission profile",
        [turn.get("permission_profile", {}).get("type") for turn in turns],
    ),
    "cwd": one_value("working directory", [turn.get("cwd") for turn in turns]),
}
print(json.dumps(evidence, separators=(",", ":"), sort_keys=True))
PY
