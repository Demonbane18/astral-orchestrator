#!/bin/sh

set -eu

script_dir=$(CDPATH= cd "$(dirname "$0")" && pwd) || exit 1
repo_root=$(CDPATH= cd "$script_dir/.." && pwd) || exit 1

command -v python3 >/dev/null 2>&1 || {
  printf '%s\n' 'ERROR: Python 3.11 or newer is required.' >&2
  exit 1
}
python3 -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 11) else 1)' >/dev/null 2>&1 || {
  printf '%s\n' 'ERROR: Python 3.11 or newer is required.' >&2
  exit 1
}

exec python3 "$repo_root/plugins/project-pilot/scripts/configure-effort.py" "$@"
