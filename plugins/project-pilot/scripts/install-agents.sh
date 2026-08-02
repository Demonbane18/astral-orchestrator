#!/bin/sh
# Install Project Pilot's custom-agent profiles without overwriting user-owned files.

set -eu

usage() {
  printf '%s\n' \
    'Usage: sh install-agents.sh [--target-dir PATH] [--check]' \
    '' \
    'Install the three Project Pilot agent profiles.' \
    'The default destination is $CODEX_HOME/agents when CODEX_HOME is set,' \
    'otherwise $HOME/.codex/agents.' \
    '' \
    '  --target-dir PATH  Use an explicit destination (useful for testing).' \
    '  --check            Verify exact installed copies without changing anything.' \
    '  --help             Show this help.'
}

fail() {
  printf '%s\n' "ERROR: $*" >&2
  exit 1
}

script_dir=$(CDPATH= cd "$(dirname "$0")" && pwd) || exit 1
template_dir=$script_dir/../agents

if [ -n "${CODEX_HOME-}" ]; then
  target_dir=$CODEX_HOME/agents
else
  [ -n "${HOME-}" ] || fail "HOME is unavailable; pass --target-dir explicitly."
  target_dir=$HOME/.codex/agents
fi

check_only=0
while [ "$#" -gt 0 ]; do
  case "$1" in
    --target-dir)
      [ "$#" -ge 2 ] || fail "--target-dir requires a path."
      [ -n "$2" ] || fail "--target-dir requires a non-empty path."
      case "$2" in
        --*) fail "--target-dir must be an explicit path." ;;
      esac
      target_dir=$2
      shift 2
      ;;
    --check)
      check_only=1
      shift
      ;;
    --help|-h)
      usage
      exit 0
      ;;
    *) fail "unknown argument: $1 (run with --help for usage)." ;;
  esac
done

case "$target_dir" in
  /*) ;;
  *) target_dir=$(pwd -P)/$target_dir ;;
esac

[ "$target_dir" != "/" ] || fail "refusing to use the filesystem root as the target."

agent_files='project-pilot-luna-implementer.toml project-pilot-terra-implementer.toml project-pilot-sol-reviewer.toml'

for agent_file in $agent_files; do
  template=$template_dir/$agent_file
  [ -f "$template" ] && [ ! -L "$template" ] || fail "profile is missing or unsafe: $template"
done

preflight_failed=0
if [ -e "$target_dir" ] || [ -L "$target_dir" ]; then
  if [ ! -d "$target_dir" ] || [ -L "$target_dir" ]; then
    printf '%s\n' "ERROR: target is not a real directory: $target_dir" >&2
    preflight_failed=1
  fi
fi

for agent_file in $agent_files; do
  template=$template_dir/$agent_file
  destination=$target_dir/$agent_file

  if [ -e "$destination" ] || [ -L "$destination" ]; then
    if [ ! -f "$destination" ] || [ -L "$destination" ]; then
      printf '%s\n' "ERROR: destination is not a regular file and will not be replaced: $destination" >&2
      preflight_failed=1
    elif ! cmp -s "$template" "$destination"; then
      printf '%s\n' "ERROR: destination differs and will not be overwritten: $destination" >&2
      printf '%s\n' "       Review both files and resolve the conflict deliberately." >&2
      preflight_failed=1
    fi
  elif [ "$check_only" -eq 1 ]; then
    printf '%s\n' "ERROR: required installed profile is missing: $destination" >&2
    preflight_failed=1
  fi
done

[ "$preflight_failed" -eq 0 ] || exit 1

if [ "$check_only" -eq 1 ]; then
  printf '%s\n' "CHECK PASSED: all Project Pilot agent profiles match exactly."
  exit 0
fi

if [ ! -d "$target_dir" ]; then
  mkdir -p "$target_dir" || fail "could not create target directory: $target_dir"
fi

for agent_file in $agent_files; do
  template=$template_dir/$agent_file
  destination=$target_dir/$agent_file

  if [ -e "$destination" ] || [ -L "$destination" ]; then
    if [ -f "$destination" ] && [ ! -L "$destination" ] && cmp -s "$template" "$destination"; then
      printf '%s\n' "ALREADY CURRENT: $destination"
      continue
    fi
    fail "destination changed after preflight and will not be overwritten: $destination"
  fi

  staged=$(mktemp "$target_dir/.project-pilot-agent.XXXXXX") || fail "could not stage profile: $destination"
  if ! cp "$template" "$staged"; then
    rm -f "$staged"
    fail "could not stage profile: $destination"
  fi

  if ln "$staged" "$destination"; then
    rm -f "$staged" || fail "could not remove staged profile: $staged"
  else
    rm -f "$staged" || fail "could not remove staged profile after conflict: $staged"
    if [ -f "$destination" ] && [ ! -L "$destination" ] && cmp -s "$template" "$destination"; then
      printf '%s\n' "ALREADY CURRENT: $destination"
      continue
    fi
    fail "destination changed after preflight and will not be overwritten: $destination"
  fi

  printf '%s\n' "INSTALLED: $destination"
done

for agent_file in $agent_files; do
  cmp -s "$template_dir/$agent_file" "$target_dir/$agent_file" || fail "post-install check failed: $target_dir/$agent_file"
done

printf '%s\n' "INSTALL PASSED: all Project Pilot agent profiles match exactly."
