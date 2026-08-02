#!/bin/sh

set -eu

usage() {
  printf '%s\n' \
    'Usage: sh scripts/setup.sh [--dry-run | --refresh | --help]' \
    '' \
    'Install Astral Orchestrator from this local repository.' \
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
manifest=$repo_root/plugins/astral-orchestrator/.codex-plugin/plugin.json
agent_installer=$repo_root/plugins/astral-orchestrator/scripts/install-agents.sh
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
[ -f "$agent_installer" ] || fail "agent installer is missing: $agent_installer"

if [ "$mode" = dry-run ]; then
  printf '%s\n' 'DRY RUN: no Codex configuration will change.'
  printf 'codex plugin marketplace add "%s"\n' "$repo_root"
  printf 'sh "%s"\n' "$agent_installer"
  printf '%s\n' 'codex plugin add astral-orchestrator@astral-orchestrator'
  exit 0
fi

command -v codex >/dev/null 2>&1 || fail "the codex command is unavailable; install or update Codex first."
command -v python3 >/dev/null 2>&1 || fail "Python 3.11 or newer is required."
python3 -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 11) else 1)' >/dev/null 2>&1 || fail "Python 3.11 or newer is required."

if [ "$mode" = install ]; then
  codex plugin marketplace add "$repo_root"
fi

sh "$agent_installer"
codex plugin add astral-orchestrator@astral-orchestrator

printf '%s\n' \
  '' \
  'Astral Orchestrator and its three model-routed agents are installed.' \
  'Start a new Codex task with gpt-5.6-sol and your configured effort (High by default), then say:' \
  'Use Astral Orchestrator to orchestrate this request and verify every lane.' \
  '' \
  'Optional: run sh scripts/configure-effort.sh --show to view effort settings.'
