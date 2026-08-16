#!/bin/sh
# Install Astral Orchestrator's custom-agent profiles without overwriting user-owned files.

set -eu

usage() {
  printf '%s\n' \
    'Usage: sh install-agents.sh [--target-dir PATH] [--check | --remove]' \
    '' \
    'Install the three Astral Orchestrator agent profiles.' \
    'The default destination is $CODEX_HOME/agents when CODEX_HOME is set,' \
    'otherwise $HOME/.codex/agents.' \
    '' \
    '  --target-dir PATH  Use an explicit destination (useful for testing).' \
    '  --check            Verify exact installed copies without changing anything.' \
    '  --remove           Remove only exact, unmodified Astral Orchestrator profiles.' \
    '  --help             Show this help.'
}

fail() {
  printf '%s\n' "ERROR: $*" >&2
  exit 1
}

script_dir=$(CDPATH= cd "$(dirname "$0")" && pwd) || exit 1
template_dir=$script_dir/../agents
legacy_template_dir=$template_dir/historical-v3.4.0

if [ -n "${CODEX_HOME-}" ]; then
  target_dir=$CODEX_HOME/agents
else
  [ -n "${HOME-}" ] || fail "HOME is unavailable; pass --target-dir explicitly."
  target_dir=$HOME/.codex/agents
fi

check_only=0
remove_only=0
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
      [ "$remove_only" -eq 0 ] || fail "--check and --remove cannot be combined."
      check_only=1
      shift
      ;;
    --remove)
      [ "$check_only" -eq 0 ] || fail "--check and --remove cannot be combined."
      remove_only=1
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

agent_files='astral-orchestrator-luna-implementer.toml astral-orchestrator-terra-implementer.toml astral-orchestrator-sol-reviewer.toml'

for agent_file in $agent_files; do
  template=$template_dir/$agent_file
  [ -f "$template" ] && [ ! -L "$template" ] || fail "profile is missing or unsafe: $template"
  legacy_template=$legacy_template_dir/$agent_file
  [ -f "$legacy_template" ] && [ ! -L "$legacy_template" ] || fail "legacy profile fixture is missing or unsafe: $legacy_template"
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
  legacy_template=$legacy_template_dir/$agent_file
  destination=$target_dir/$agent_file

  if [ -e "$destination" ] || [ -L "$destination" ]; then
    if [ ! -f "$destination" ] || [ -L "$destination" ]; then
      if [ "$remove_only" -eq 1 ]; then
        printf '%s\n' "ERROR: destination is not a regular file and will not be removed: $destination" >&2
      else
        printf '%s\n' "ERROR: destination is not a regular file and will not be replaced: $destination" >&2
      fi
      preflight_failed=1
    elif ! cmp -s "$template" "$destination"; then
      if [ "$check_only" -eq 0 ] && cmp -s "$legacy_template" "$destination"; then
        continue
      fi
      if [ "$remove_only" -eq 1 ]; then
        printf '%s\n' "ERROR: destination differs and will not be removed: $destination" >&2
        printf '%s\n' "       This may be user-owned or customized; remove it deliberately if desired." >&2
      else
        printf '%s\n' "ERROR: destination differs and will not be overwritten: $destination" >&2
        printf '%s\n' "       Review both files and resolve the conflict deliberately." >&2
      fi
      preflight_failed=1
    fi
  elif [ "$check_only" -eq 1 ]; then
    printf '%s\n' "ERROR: required installed profile is missing: $destination" >&2
    preflight_failed=1
  fi
done

[ "$preflight_failed" -eq 0 ] || exit 1

if [ "$remove_only" -eq 1 ]; then
  for agent_file in $agent_files; do
    template=$template_dir/$agent_file
    legacy_template=$legacy_template_dir/$agent_file
    destination=$target_dir/$agent_file
    if [ -f "$destination" ] && [ ! -L "$destination" ]; then
      if ! cmp -s "$template" "$destination" && ! cmp -s "$legacy_template" "$destination"; then
        fail "destination changed after preflight and will not be removed: $destination"
      fi
      rm -f "$destination" || fail "could not remove exact Astral Orchestrator profile: $destination"
      printf '%s\n' "REMOVED: $destination"
    fi
  done
  printf '%s\n' "REMOVE PASSED: exact Astral Orchestrator agent profiles are absent."
  exit 0
fi

if [ "$check_only" -eq 1 ]; then
  printf '%s\n' "CHECK PASSED: all Astral Orchestrator agent profiles match exactly."
  exit 0
fi

if [ ! -d "$target_dir" ]; then
  mkdir -p "$target_dir" || fail "could not create target directory: $target_dir"
fi

for agent_file in $agent_files; do
  template=$template_dir/$agent_file
  legacy_template=$legacy_template_dir/$agent_file
  destination=$target_dir/$agent_file

  if [ -e "$destination" ] || [ -L "$destination" ]; then
    if [ -f "$destination" ] && [ ! -L "$destination" ] && cmp -s "$template" "$destination"; then
      printf '%s\n' "ALREADY CURRENT: $destination"
      continue
    fi
    if [ -f "$destination" ] && [ ! -L "$destination" ] && cmp -s "$legacy_template" "$destination"; then
      staged=$(mktemp "$target_dir/.astral-orchestrator-agent.XXXXXX") || fail "could not stage migrated profile: $destination"
      if ! cp "$template" "$staged"; then
        rm -f "$staged"
        fail "could not stage migrated profile: $destination"
      fi
      if ! cmp -s "$legacy_template" "$destination"; then
        rm -f "$staged"
        fail "destination changed before migration and will not be overwritten: $destination"
      fi
      if ! mv -f "$staged" "$destination"; then
        rm -f "$staged"
        fail "could not migrate exact legacy profile: $destination"
      fi
      printf '%s\n' "MIGRATED: $destination"
      continue
    fi
    fail "destination changed after preflight and will not be overwritten: $destination"
  fi

  staged=$(mktemp "$target_dir/.astral-orchestrator-agent.XXXXXX") || fail "could not stage profile: $destination"
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

printf '%s\n' "INSTALL PASSED: all Astral Orchestrator agent profiles match exactly."
