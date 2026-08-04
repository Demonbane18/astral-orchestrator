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
skill=$plugin_dir/skills/astral-orchestrator/SKILL.md
modes=$plugin_dir/skills/astral-orchestrator/references/modes-and-risk.md
templates=$plugin_dir/skills/astral-orchestrator/references/work-templates.md
routing=$plugin_dir/skills/astral-orchestrator/references/routing-and-preflight.md
measured=$plugin_dir/skills/astral-orchestrator/references/measured-mode.md
agent_dir=$plugin_dir/agents
installer=$plugin_dir/scripts/install-agents.sh
inspector=$plugin_dir/scripts/inspect-agent-runtime.sh
launcher=$plugin_dir/scripts/run-agent.py
effort_settings=$plugin_dir/scripts/effort_settings.py
effort_configurator=$plugin_dir/scripts/configure-effort.py
benchmark_scorecard=$plugin_dir/scripts/benchmark-scorecard.py
effort_wrapper=$repo_root/scripts/configure-effort.sh
marketplace=$repo_root/.agents/plugins/marketplace.json
canonical_license=$repo_root/LICENSE
canonical_notice=$repo_root/NOTICE.md
plugin_license=$plugin_dir/LICENSE
plugin_notice=$plugin_dir/NOTICE.md
canonical_improvements_url=https://github.com/Demonbane18/astral-orchestrator/blob/main/docs/IMPROVEMENTS.md

[ -f "$canonical_license" ] || fail "canonical notice is missing: LICENSE"
[ -f "$canonical_notice" ] || fail "canonical notice is missing: NOTICE.md"
[ -f "$plugin_license" ] || fail "required distributable notice is missing: LICENSE"
[ -f "$plugin_notice" ] || fail "required distributable notice is missing: NOTICE.md"
cmp -s "$canonical_license" "$plugin_license" || fail "distributable notice differs from repository root: LICENSE"
cmp -s "$canonical_notice" "$plugin_notice" || fail "distributable notice differs from repository root: NOTICE.md"
grep -Fq "($canonical_improvements_url)" "$canonical_notice" || fail "canonical NOTICE must link to the repository improvements document"

for required in "$manifest" "$skill" "$modes" "$templates" "$routing" "$measured" "$installer" "$inspector" "$launcher" "$effort_settings" "$effort_configurator" "$benchmark_scorecard" "$effort_wrapper"; do
  [ -f "$required" ] || fail "required file is missing: $required"
done

command -v python3 >/dev/null 2>&1 || fail "Python 3.11 or newer is required for repository verification."
python3 -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 11) else 1)' >/dev/null 2>&1 || fail "Python 3.11 or newer is required for repository verification."

python3 - "$manifest" "$skill" "$modes" "$templates" "$routing" "$measured" "$agent_dir" "$marketplace" <<'PY'
import json
import sys
import tomllib
from pathlib import Path

manifest_path, skill_path, modes_path, templates_path, routing_path, measured_path, agent_dir, marketplace_path = map(
    Path, sys.argv[1:]
)

manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
if manifest.get("name") != "astral-orchestrator":
    raise SystemExit("manifest name must be astral-orchestrator")
if manifest.get("version") != "3.2.0":
    raise SystemExit("manifest version must be Astral Orchestrator v3.2.0")
if manifest.get("skills") != "./skills/":
    raise SystemExit("manifest skills path must be ./skills/")
if manifest.get("license") != "MIT":
    raise SystemExit("manifest license must be MIT")
if manifest.get("interface", {}).get("displayName") != "Astral Orchestrator":
    raise SystemExit("manifest display name must be Astral Orchestrator")
if manifest.get("homepage") != "https://github.com/Demonbane18/astral-orchestrator":
    raise SystemExit("manifest homepage must be the Astral Orchestrator repository")
repository = manifest.get("repository")
if repository != "https://github.com/Demonbane18/astral-orchestrator":
    raise SystemExit("manifest repository metadata is invalid")

prompts = manifest.get("interface", {}).get("defaultPrompt")
if not isinstance(prompts, list) or not 1 <= len(prompts) <= 3:
    raise SystemExit("manifest must contain one to three starter prompts")
if any(not isinstance(prompt, str) or len(prompt) > 128 for prompt in prompts):
    raise SystemExit("starter prompts must be strings no longer than 128 characters")

skill = skill_path.read_text(encoding="utf-8")
if not skill.startswith("---\nname: astral-orchestrator\n"):
    raise SystemExit("skill frontmatter name is invalid")
for required_text in (
    "Quick",
    "Guided (default)",
    "Careful",
    "Measured",
    "Sol High",
    "astral_orchestrator_luna_implementer",
    "astral_orchestrator_terra_implementer",
    "astral_orchestrator_sol_reviewer",
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

routing = routing_path.read_text(encoding="utf-8")
for required_text in (
    "gpt-5.6-sol",
    "gpt-5.6-luna",
    "gpt-5.6-terra",
    "Do not silently substitute",
    "runtime evidence",
):
    if required_text not in routing:
        raise SystemExit(f"routing contract is missing: {required_text}")

measured = " ".join(measured_path.read_text(encoding="utf-8").split())
for required_text in (
    "explicit opt-in",
    "Never auto-select",
    "repository-root SHA-256 prefix",
    "frozen-card SHA-256 prefix",
    "id -u",
    "exactly one Luna probe and one Terra probe",
    "card.txt",
    "phase-state.txt",
    "ledger.txt",
    "behaviorally read-only",
    "not hard sandbox isolation",
    "Only the selected implementation lane edits",
    "fresh verification",
    "new reviewer",
):
    if required_text not in measured:
        raise SystemExit(f"measured contract is missing: {required_text}")

expected_agents = {
    "astral-orchestrator-luna-implementer.toml": {
        "name": "astral_orchestrator_luna_implementer",
        "model": "gpt-5.6-luna",
        "model_reasoning_effort": "xhigh",
    },
    "astral-orchestrator-terra-implementer.toml": {
        "name": "astral_orchestrator_terra_implementer",
        "model": "gpt-5.6-terra",
        "model_reasoning_effort": "xhigh",
    },
    "astral-orchestrator-sol-reviewer.toml": {
        "name": "astral_orchestrator_sol_reviewer",
        "model": "gpt-5.6-sol",
        "model_reasoning_effort": "high",
        "sandbox_mode": "read-only",
    },
}
if {path.name for path in agent_dir.glob("*.toml")} != set(expected_agents):
    raise SystemExit("agent profile set does not match the v3 routing contract")
for filename, expected in expected_agents.items():
    profile = tomllib.loads((agent_dir / filename).read_text(encoding="utf-8"))
    for field, value in expected.items():
        if profile.get(field) != value:
            raise SystemExit(f"{filename} must set {field} to {value}")

if marketplace_path.is_file():
    marketplace = json.loads(marketplace_path.read_text(encoding="utf-8"))
    if marketplace.get("name") != "astral-orchestrator":
        raise SystemExit("marketplace name must be astral-orchestrator")
    entries = marketplace.get("plugins", [])
    if len(entries) != 1 or entries[0].get("name") != "astral-orchestrator":
        raise SystemExit("marketplace must contain exactly one astral-orchestrator entry")

for path in (manifest_path, skill_path, modes_path, templates_path, routing_path, measured_path, *agent_dir.glob("*.toml")):
    text = path.read_text(encoding="utf-8")
    if "[TODO" in text or "YOUR-NAME" in text:
        raise SystemExit(f"placeholder remains in {path}")
PY

sh -n "$0"
sh -n "$installer"
sh -n "$inspector"
sh -n "$effort_wrapper"
python3 "$launcher" --help >/dev/null
python3 "$effort_configurator" --help >/dev/null
python3 "$benchmark_scorecard" --help >/dev/null

printf '%s\n' 'Astral Orchestrator verification passed.'
