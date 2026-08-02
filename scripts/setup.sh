#!/bin/sh

set -eu

usage() {
  printf '%s\n' \
    'Usage: sh scripts/setup.sh [--dry-run | --refresh | --help]' \
    '' \
    'Install Project Pilot from this local repository.' \
    '' \
    '  --dry-run  Show the install commands without changing Codex.' \
    '  --refresh  Reinstall the plugin after updating this registered checkout.' \
    '  --help     Show this help.'
}

fail() {
  printf '%s\n' "ERROR: $*" >&2
  exit 1
}

script_dir=$(CDPATH= cd "$(dirname "$0")" && pwd) || exit 1
repo_root=$(CDPATH= cd "$script_dir/.." && pwd) || exit 1
marketplace=$repo_root/.agents/plugins/marketplace.json
manifest=$repo_root/plugins/project-pilot/.codex-plugin/plugin.json
mode=install

case "$#" in
  0) ;;
  1)
    case "$1" in
      --dry-run) mode=dry-run ;;
      --refresh) mode=refresh ;;
      --help|-h)
        usage
        exit 0
        ;;
      *)
        usage >&2
        exit 2
        ;;
    esac
    ;;
  *)
    usage >&2
    exit 2
    ;;
esac

[ -f "$marketplace" ] || fail "marketplace file is missing: $marketplace"
[ -f "$manifest" ] || fail "plugin manifest is missing: $manifest"

if [ "$mode" = dry-run ]; then
  printf '%s\n' 'DRY RUN: no Codex configuration will change.'
  printf 'codex plugin marketplace add "%s"\n' "$repo_root"
  printf '%s\n' 'codex plugin add project-pilot@project-pilot'
  exit 0
fi

command -v codex >/dev/null 2>&1 || fail "the codex command is unavailable; install or update Codex first."

if [ "$mode" = install ]; then
  codex plugin marketplace add "$repo_root"
fi

codex plugin add project-pilot@project-pilot

printf '%s\n' \
  '' \
  'Project Pilot is installed.' \
  'Start a new Codex task, then say:' \
  'Use Project Pilot to complete this request and verify the result.'
