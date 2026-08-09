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
portable_manifest=$plugin_dir/plugin.json
skill=$plugin_dir/skills/astral-orchestrator/SKILL.md
modes=$plugin_dir/skills/astral-orchestrator/references/modes-and-risk.md
templates=$plugin_dir/skills/astral-orchestrator/references/work-templates.md
routing=$plugin_dir/skills/astral-orchestrator/references/routing-and-preflight.md
measured=$plugin_dir/skills/astral-orchestrator/references/measured-mode.md
morph=$plugin_dir/skills/astral-orchestrator/references/morph-mode.md
constellation=$plugin_dir/skills/astral-orchestrator/references/constellation-mode.md
portable_hosts=$plugin_dir/skills/astral-orchestrator/references/portable-hosts.md
agent_dir=$plugin_dir/agents
installer=$plugin_dir/scripts/install-agents.sh
inspector=$plugin_dir/scripts/inspect-agent-runtime.sh
primary_checker=$plugin_dir/scripts/check-primary.py
launcher=$plugin_dir/scripts/run-agent.py
morph_launcher=$plugin_dir/scripts/run-morph-agent.py
codex_runtime=$plugin_dir/scripts/codex_runtime.py
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

for required in "$manifest" "$portable_manifest" "$skill" "$modes" "$templates" "$routing" "$measured" "$morph" "$constellation" "$portable_hosts" "$installer" "$inspector" "$primary_checker" "$launcher" "$morph_launcher" "$codex_runtime" "$effort_settings" "$effort_configurator" "$benchmark_scorecard" "$effort_wrapper"; do
  [ -f "$required" ] || fail "required file is missing: $required"
done

command -v python3 >/dev/null 2>&1 || fail "Python 3.11 or newer is required for repository verification."
python3 -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 11) else 1)' >/dev/null 2>&1 || fail "Python 3.11 or newer is required for repository verification."

python3 - "$manifest" "$portable_manifest" "$skill" "$modes" "$templates" "$routing" "$measured" "$morph" "$constellation" "$portable_hosts" "$agent_dir" "$marketplace" <<'PY'
import json
import re
import sys
import tomllib
from pathlib import Path

manifest_path, portable_manifest_path, skill_path, modes_path, templates_path, routing_path, measured_path, morph_path, constellation_path, portable_hosts_path, agent_dir, marketplace_path = map(
    Path, sys.argv[1:]
)

manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
if manifest.get("name") != "astral-orchestrator":
    raise SystemExit("manifest name must be astral-orchestrator")
if manifest.get("version") != "3.3.1":
    raise SystemExit("manifest version must be Astral Orchestrator v3.3.1")
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

portable_manifest = json.loads(portable_manifest_path.read_text(encoding="utf-8"))
portable_fields = {
    "$schema", "name", "version", "description", "author", "homepage", "repository",
    "license", "keywords", "extensions",
}
if not isinstance(portable_manifest, dict) or set(portable_manifest) - portable_fields:
    raise SystemExit("portable manifest must use only closed Agent Plugins top-level fields")
if portable_manifest.get("$schema") != "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json":
    raise SystemExit("portable manifest schema must be the canonical Agent Plugins v1.0.0 schema")
if portable_manifest.get("name") != "astral-orchestrator":
    raise SystemExit("portable manifest name must be astral-orchestrator")
if not re.fullmatch(r"(?!.*(?:--|\\.\\.))[a-z0-9](?:[a-z0-9.-]*[a-z0-9])?", portable_manifest["name"]):
    raise SystemExit("portable manifest name violates the Agent Plugins name contract")
if portable_manifest.get("version") != manifest.get("version"):
    raise SystemExit("Codex and portable manifest versions must match")
if any(field in portable_manifest for field in ("skills", "interface")):
    raise SystemExit("portable manifest must rely on fixed discovery, not Codex fields")
for field in ("description", "homepage", "repository", "license"):
    if not isinstance(portable_manifest.get(field), str):
        raise SystemExit(f"portable manifest {field} must be a string")
author = portable_manifest.get("author")
if not isinstance(author, dict) or set(author) - {"name", "email", "url"} or any(
    not isinstance(value, str) for value in author.values()
):
    raise SystemExit("portable manifest author must be a closed object of strings")
if not isinstance(portable_manifest.get("keywords"), list) or any(
    not isinstance(value, str) for value in portable_manifest["keywords"]
):
    raise SystemExit("portable manifest keywords must be strings")
if "extensions" in portable_manifest and (
    not isinstance(portable_manifest["extensions"], dict)
    or any(not isinstance(value, dict) for value in portable_manifest["extensions"].values())
):
    raise SystemExit("portable manifest extensions must map namespaces to objects")

portable_root = portable_manifest_path.parent.resolve()
skills_root = portable_root / "skills"
try:
    skills_root.resolve().relative_to(portable_root)
except ValueError:
    raise SystemExit("portable skills directory resolves outside the package")
if not skills_root.is_dir():
    raise SystemExit("portable fixed skills path must be a directory")
for child in skills_root.iterdir():
    skill_file = child / "SKILL.md"
    if not skill_file.exists():
        continue
    if not skill_file.is_file():
        raise SystemExit(f"portable discovered skill is not a regular file: {skill_file.name}")
    try:
        skill_file.resolve().relative_to(portable_root)
    except ValueError:
        raise SystemExit(f"portable discovered skill escapes the package: {child.name}")
if not (skills_root / "astral-orchestrator" / "SKILL.md").is_file():
    raise SystemExit("portable fixed skills path is missing Astral Orchestrator")

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
    "Morph",
    "Constellation",
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

morph = morph_path.read_text(encoding="utf-8")
for required_text in ("explicit opt-in", "OpenCodex is optional", "requested effort", "fresh Sol reviewer"):
    if required_text not in morph:
        raise SystemExit(f"Morph guide is missing: {required_text}")

constellation = constellation_path.read_text(encoding="utf-8")
for required_text in ("explicit opt-in", "first wave concurrently", "available slots", "fresh exact Sol reviewer"):
    if required_text not in constellation:
        raise SystemExit(f"Constellation guide is missing: {required_text}")

portable_hosts = " ".join(portable_hosts_path.read_text(encoding="utf-8").lower().split())
for required_text in ("observable", "separate worker context", "fresh reviewer context", "serial portable fallback"):
    if required_text not in portable_hosts:
        raise SystemExit(f"portable-host guide is missing: {required_text}")

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

for path in (manifest_path, portable_manifest_path, skill_path, modes_path, templates_path, routing_path, measured_path, morph_path, constellation_path, portable_hosts_path, *agent_dir.glob("*.toml")):
    text = path.read_text(encoding="utf-8")
    if "[TODO" in text or "YOUR-NAME" in text:
        raise SystemExit(f"placeholder remains in {path}")
PY

sh -n "$0"
sh -n "$installer"
sh -n "$inspector"
sh -n "$effort_wrapper"
python3 "$launcher" --help >/dev/null
python3 "$primary_checker" --help >/dev/null
python3 "$morph_launcher" --help >/dev/null
python3 "$effort_configurator" --help >/dev/null
python3 "$benchmark_scorecard" --help >/dev/null

printf '%s\n' 'Astral Orchestrator verification passed.'
