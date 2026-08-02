#!/bin/sh
# Emit only allowlisted routing metadata from one exact native subagent rollout.

set -eu

usage() {
  printf '%s\n' \
    'Usage: sh inspect-agent-runtime.sh [--sessions-dir PATH] THREAD_ID' \
    '       sh inspect-agent-runtime.sh [--sessions-dir PATH] [--since-epoch N] --agent-path PATH' \
    '' \
    'Return a small JSON object containing only identity, model, effort, sandbox,' \
    'permission, and working-directory evidence for one subagent task.'
}

fail() {
  printf '%s\n' "ERROR: $*" >&2
  exit 1
}

sessions_dir=''
since_epoch=0
selector_kind=''
selector_value=''

while [ "$#" -gt 0 ]; do
  case "$1" in
    --sessions-dir)
      [ "$#" -ge 2 ] || fail "--sessions-dir requires a path."
      [ -n "$2" ] || fail "--sessions-dir requires a non-empty path."
      sessions_dir=$2
      shift 2
      ;;
    --since-epoch)
      [ "$#" -ge 2 ] || fail "--since-epoch requires whole seconds."
      since_epoch=$2
      shift 2
      ;;
    --thread-id)
      [ "$#" -ge 2 ] || fail "--thread-id requires a lowercase UUID."
      [ -z "$selector_kind" ] || fail "choose only one task selector."
      selector_kind=thread_id
      selector_value=$2
      shift 2
      ;;
    --agent-path)
      [ "$#" -ge 2 ] || fail "--agent-path requires the canonical spawned task path."
      [ -z "$selector_kind" ] || fail "choose only one task selector."
      selector_kind=agent_path
      selector_value=$2
      shift 2
      ;;
    --help|-h)
      usage
      exit 0
      ;;
    --*) fail "unknown option: $1" ;;
    *)
      [ -z "$selector_kind" ] || fail "choose only one task selector."
      selector_kind=thread_id
      selector_value=$1
      shift
      ;;
  esac
done

[ -n "$selector_kind" ] || fail "a THREAD_ID or --agent-path selector is required."
if ! printf '%s\n' "$since_epoch" | LC_ALL=C grep -Eq '^[0-9]+$'; then
  fail "--since-epoch must be zero or positive whole seconds."
fi

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

python3 - "$sessions_dir" "$selector_kind" "$selector_value" "$since_epoch" <<'PY'
import json
import re
import sys
from pathlib import Path


def fail(message):
    print(f"ERROR: {message}", file=sys.stderr)
    raise SystemExit(1)


sessions_dir = Path(sys.argv[1])
selector_kind = sys.argv[2]
selector_value = sys.argv[3]
since_epoch = int(sys.argv[4])
uuid_pattern = r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}"

if selector_kind == "thread_id":
    if not re.fullmatch(uuid_pattern, selector_value):
        fail("THREAD_ID must be a lowercase UUID.")
    thread_id = selector_value
elif selector_kind == "agent_path":
    if not re.fullmatch(r"/[A-Za-z0-9_./-]+", selector_value):
        fail("--agent-path must be a canonical task path.")
    matching_ids = set()
    for candidate in sessions_dir.rglob("rollout-*.jsonl"):
        try:
            if not candidate.is_file() or candidate.stat().st_mtime < since_epoch:
                continue
            with candidate.open(encoding="utf-8") as handle:
                for line in handle:
                    if not line.strip():
                        continue
                    item = json.loads(line)
                    payload = item.get("payload")
                    if (
                        item.get("type") == "session_meta"
                        and isinstance(payload, dict)
                        and payload.get("agent_path") == selector_value
                        and isinstance(payload.get("id"), str)
                        and re.fullmatch(uuid_pattern, payload["id"])
                    ):
                        matching_ids.add(payload["id"])
        except (OSError, UnicodeError, json.JSONDecodeError):
            continue
    if len(matching_ids) != 1:
        fail(
            "expected one task id for the returned agent path since the supplied time; "
            f"found {len(matching_ids)}."
        )
    thread_id = next(iter(matching_ids))
else:
    fail("unsupported task selector.")

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

sessions = [
    item.get("payload")
    for item in records
    if item.get("type") == "session_meta"
    and isinstance(item.get("payload"), dict)
    and item["payload"].get("id") == thread_id
]
turns = [
    item.get("payload")
    for item in records
    if item.get("type") == "turn_context" and isinstance(item.get("payload"), dict)
]
if len(sessions) != 1:
    fail("metadata for the requested task is missing or ambiguous.")
if not turns:
    fail("turn context is missing.")

session = sessions[0]
# Forked rollout snapshots can contain inherited parent contexts with different routes.
# The final turn_context is the effective context last observed for this task.
turn = turns[-1]


def required_string(label, value):
    if not isinstance(value, str) or not value:
        fail(f"{label} is missing.")
    return value


def optional_string(label, value):
    if value is None:
        return None
    if not isinstance(value, str):
        fail(f"{label} is invalid.")
    return value


sandbox = turn.get("sandbox_policy")
permission = turn.get("permission_profile")
if not isinstance(sandbox, dict):
    fail("sandbox policy is missing.")
if not isinstance(permission, dict):
    fail("permission profile is missing.")

evidence = {
    "thread_id": thread_id,
    "parent_thread_id": optional_string("parent task id", session.get("parent_thread_id")),
    "forked_from_id": optional_string("fork source id", session.get("forked_from_id")),
    "agent_nickname": optional_string("agent nickname", session.get("agent_nickname")),
    "agent_path": optional_string("agent path", session.get("agent_path")),
    "model_provider": optional_string("model provider", session.get("model_provider")),
    "model": required_string("model", turn.get("model")),
    "effort": required_string("effort", turn.get("effort")),
    "sandbox_policy_type": required_string("sandbox policy type", sandbox.get("type")),
    "permission_profile_type": required_string("permission profile type", permission.get("type")),
    "cwd": required_string("working directory", turn.get("cwd")),
}
print(json.dumps(evidence, separators=(",", ":"), sort_keys=True))
PY
