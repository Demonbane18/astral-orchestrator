#!/bin/sh

set -eu

fail() {
  printf '%s\n' "ERROR: $*" >&2
  exit 1
}

script_dir=$(CDPATH= cd "$(dirname "$0")" && pwd) || exit 1
plugin_dir=$(CDPATH= cd "$script_dir/.." && pwd) || exit 1
repo_root=$(CDPATH= cd "$plugin_dir/../.." && pwd) || exit 1
manifest=$plugin_dir/.codex-plugin/plugin.json
skill=$plugin_dir/skills/project-pilot/SKILL.md
modes=$plugin_dir/skills/project-pilot/references/modes-and-risk.md
templates=$plugin_dir/skills/project-pilot/references/work-templates.md
marketplace=$repo_root/.agents/plugins/marketplace.json

for required in "$manifest" "$skill" "$modes" "$templates"; do
  [ -f "$required" ] || fail "required file is missing: $required"
done

command -v python3 >/dev/null 2>&1 || fail "Python 3 is required for repository verification."

python3 - "$manifest" "$skill" "$modes" "$templates" "$marketplace" <<'PY'
import json
import sys
from pathlib import Path

manifest_path, skill_path, modes_path, templates_path, marketplace_path = map(
    Path, sys.argv[1:]
)

manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
if manifest.get("name") != "project-pilot":
    raise SystemExit("manifest name must be project-pilot")
if manifest.get("skills") != "./skills/":
    raise SystemExit("manifest skills path must be ./skills/")
if manifest.get("license") != "MIT":
    raise SystemExit("manifest license must be MIT")
if manifest.get("interface", {}).get("displayName") != "Project Pilot":
    raise SystemExit("manifest display name must be Project Pilot")

prompts = manifest.get("interface", {}).get("defaultPrompt")
if not isinstance(prompts, list) or not 1 <= len(prompts) <= 3:
    raise SystemExit("manifest must contain one to three starter prompts")
if any(not isinstance(prompt, str) or len(prompt) > 128 for prompt in prompts):
    raise SystemExit("starter prompts must be strings no longer than 128 characters")

skill = skill_path.read_text(encoding="utf-8")
if not skill.startswith("---\nname: project-pilot\n"):
    raise SystemExit("skill frontmatter name is invalid")
for required_text in (
    "Quick",
    "Guided (default)",
    "Careful",
    "primary session",
    "independent review",
    "verification",
):
    if required_text not in skill:
        raise SystemExit(f"skill contract is missing: {required_text}")

modes = modes_path.read_text(encoding="utf-8")
for required_text in ("Low risk", "Medium risk", "High risk", "User confirmation gate"):
    if required_text not in modes:
        raise SystemExit(f"risk guide is missing: {required_text}")

templates = templates_path.read_text(encoding="utf-8")
for required_text in ("Work card", "Implementation delegation", "Fresh review"):
    if required_text not in templates:
        raise SystemExit(f"work templates are missing: {required_text}")

if marketplace_path.is_file():
    marketplace = json.loads(marketplace_path.read_text(encoding="utf-8"))
    if marketplace.get("name") != "project-pilot":
        raise SystemExit("marketplace name must be project-pilot")
    entries = marketplace.get("plugins", [])
    if len(entries) != 1 or entries[0].get("name") != "project-pilot":
        raise SystemExit("marketplace must contain exactly one project-pilot entry")

for path in (manifest_path, skill_path, modes_path, templates_path):
    text = path.read_text(encoding="utf-8")
    if "[TODO" in text or "YOUR-NAME" in text:
        raise SystemExit(f"placeholder remains in {path}")
PY

sh -n "$0"

printf '%s\n' 'Project Pilot verification passed.'
