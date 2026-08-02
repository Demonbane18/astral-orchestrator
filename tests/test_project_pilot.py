import json
import re
import subprocess
import tempfile
import tomllib
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MARKETPLACE = ROOT / ".agents/plugins/marketplace.json"
PLUGIN = ROOT / "plugins/project-pilot"
MANIFEST = PLUGIN / ".codex-plugin/plugin.json"
SKILL = PLUGIN / "skills/project-pilot/SKILL.md"
MODES = PLUGIN / "skills/project-pilot/references/modes-and-risk.md"
TEMPLATES = PLUGIN / "skills/project-pilot/references/work-templates.md"
ROUTING = PLUGIN / "skills/project-pilot/references/routing-and-preflight.md"
AGENTS = PLUGIN / "agents"
INSTALL_AGENTS = PLUGIN / "scripts/install-agents.sh"
INSPECT_RUNTIME = PLUGIN / "scripts/inspect-agent-runtime.sh"


def read(path: Path) -> str:
    if not path.is_file():
        raise AssertionError(f"required file is missing: {path.relative_to(ROOT)}")
    return path.read_text(encoding="utf-8")


def load_json(path: Path):
    return json.loads(read(path))


class MarketplaceTests(unittest.TestCase):
    def test_marketplace_exposes_one_local_project_pilot_plugin(self):
        marketplace = load_json(MARKETPLACE)

        self.assertEqual(marketplace["name"], "project-pilot")
        self.assertEqual(marketplace["interface"]["displayName"], "Project Pilot")
        self.assertEqual(len(marketplace["plugins"]), 1)

        entry = marketplace["plugins"][0]
        self.assertEqual(entry["name"], "project-pilot")
        self.assertEqual(
            entry["source"],
            {"source": "local", "path": "./plugins/project-pilot"},
        )
        self.assertEqual(entry["policy"]["installation"], "AVAILABLE")
        self.assertEqual(entry["policy"]["authentication"], "ON_INSTALL")
        self.assertEqual(entry["category"], "Productivity")

    def test_manifest_is_minimal_and_shareable(self):
        manifest = load_json(MANIFEST)

        self.assertEqual(manifest["name"], "project-pilot")
        self.assertRegex(manifest["version"], r"^2\.\d+\.\d+$")
        self.assertEqual(manifest["license"], "MIT")
        self.assertEqual(manifest["skills"], "./skills/")
        self.assertEqual(manifest["interface"]["displayName"], "Project Pilot")
        self.assertEqual(manifest["interface"]["category"], "Productivity")
        self.assertNotIn("mcpServers", manifest)
        self.assertNotIn("apps", manifest)
        self.assertNotIn("hooks", manifest)

        prompts = manifest["interface"]["defaultPrompt"]
        self.assertGreaterEqual(len(prompts), 2)
        self.assertLessEqual(len(prompts), 3)
        self.assertTrue(all(len(prompt) <= 128 for prompt in prompts))


class SkillContractTests(unittest.TestCase):
    def test_skill_uses_three_plain_language_modes(self):
        skill = read(SKILL)
        modes = read(MODES)

        for mode in ("Quick", "Guided", "Careful"):
            self.assertIn(mode, skill)
            self.assertIn(mode, modes)
        self.assertRegex(skill, r"Guided[^\n]*(default|Default)")

    def test_skill_routes_work_to_exact_model_pinned_roles(self):
        skill = read(SKILL).lower()
        routing = read(ROUTING).lower()

        for required in (
            "sol high",
            "project_pilot_luna_implementer",
            "project_pilot_terra_implementer",
            "project_pilot_sol_reviewer",
        ):
            self.assertIn(required, skill)

        self.assertIn("repeatable", routing)
        self.assertIn("context-heavy", routing)
        self.assertIn("do not silently substitute", routing)
        self.assertIn("runtime evidence", routing)
        self.assertIn("stop", routing)

    def test_companion_agent_profiles_pin_exact_models_and_effort(self):
        expected = {
            "project-pilot-luna-implementer.toml": {
                "name": "project_pilot_luna_implementer",
                "model": "gpt-5.6-luna",
                "model_reasoning_effort": "xhigh",
            },
            "project-pilot-terra-implementer.toml": {
                "name": "project_pilot_terra_implementer",
                "model": "gpt-5.6-terra",
                "model_reasoning_effort": "xhigh",
            },
            "project-pilot-sol-reviewer.toml": {
                "name": "project_pilot_sol_reviewer",
                "model": "gpt-5.6-sol",
                "model_reasoning_effort": "high",
                "sandbox_mode": "read-only",
            },
        }

        self.assertEqual({path.name for path in AGENTS.glob("*.toml")}, set(expected))
        for filename, fields in expected.items():
            profile = tomllib.loads(read(AGENTS / filename))
            for field, value in fields.items():
                self.assertEqual(profile.get(field), value, f"{filename}: {field}")
            self.assertIn("developer_instructions", profile)

    def test_agent_installer_is_idempotent_and_conflict_safe(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "agents"
            install = subprocess.run(
                ["sh", str(INSTALL_AGENTS), "--target-dir", str(target)],
                cwd=ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(install.returncode, 0, install.stdout + install.stderr)

            check = subprocess.run(
                ["sh", str(INSTALL_AGENTS), "--target-dir", str(target), "--check"],
                cwd=ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(check.returncode, 0, check.stdout + check.stderr)
            for template in AGENTS.glob("*.toml"):
                self.assertEqual(
                    (target / template.name).read_bytes(),
                    template.read_bytes(),
                )

            conflict = target / "project-pilot-luna-implementer.toml"
            conflict.write_text("user-owned = true\n", encoding="utf-8")
            refused = subprocess.run(
                ["sh", str(INSTALL_AGENTS), "--target-dir", str(target)],
                cwd=ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertNotEqual(refused.returncode, 0)
            self.assertIn("will not be overwritten", refused.stderr)
            self.assertEqual(conflict.read_text(encoding="utf-8"), "user-owned = true\n")

    def test_runtime_inspector_emits_only_allowlisted_route_evidence(self):
        thread_id = "12345678-1234-1234-1234-123456789abc"
        with tempfile.TemporaryDirectory() as directory:
            sessions = Path(directory)
            rollout = sessions / f"rollout-test-{thread_id}.jsonl"
            rollout.write_text(
                "\n".join(
                    (
                        json.dumps(
                            {
                                "type": "session_meta",
                                "payload": {
                                    "id": thread_id,
                                    "parent_thread_id": "parent",
                                    "agent_role": "project_pilot_luna_implementer",
                                    "agent_path": "project-pilot-luna-implementer.toml",
                                    "model_provider": "openai",
                                    "secret": "must-not-leak",
                                },
                            }
                        ),
                        json.dumps(
                            {
                                "type": "turn_context",
                                "payload": {
                                    "model": "gpt-5.6-luna",
                                    "effort": "xhigh",
                                    "sandbox_policy": {"type": "workspace-write"},
                                    "permission_profile": {"type": "managed"},
                                    "cwd": str(ROOT),
                                    "prompt": "must-not-leak",
                                },
                            }
                        ),
                    )
                )
                + "\n",
                encoding="utf-8",
            )

            result = subprocess.run(
                [
                    "sh",
                    str(INSPECT_RUNTIME),
                    "--sessions-dir",
                    str(sessions),
                    thread_id,
                ],
                cwd=ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            evidence = json.loads(result.stdout)
            self.assertEqual(evidence["model"], "gpt-5.6-luna")
            self.assertEqual(evidence["effort"], "xhigh")
            self.assertEqual(
                evidence["agent_role"], "project_pilot_luna_implementer"
            )
            self.assertNotIn("secret", evidence)
            self.assertNotIn("prompt", evidence)

    def test_risk_and_destructive_actions_are_gated(self):
        skill = read(SKILL).lower()
        modes = read(MODES).lower()

        self.assertIn("risk", skill)
        self.assertIn("verification", skill)
        self.assertIn("user confirmation", modes)
        self.assertIn("destructive", modes)
        self.assertIn("credentials", modes)

    def test_unavailable_confirmation_returns_control_immediately(self):
        skill = read(SKILL).lower()
        modes = read(MODES).lower()

        self.assertIn("ends the current turn", skill)
        self.assertIn("make no changes", modes)
        self.assertIn("return the question immediately", modes)
        self.assertIn("do not wait", modes)

    def test_templates_cover_work_ownership_and_fresh_review(self):
        templates = read(TEMPLATES).lower()

        for heading in (
            "outcome",
            "done when",
            "ownership",
            "boundaries",
            "checks",
            "fresh review",
            "verdict",
        ):
            self.assertIn(heading, templates)
        self.assertIn("not alone in the codebase", templates)

    def test_skill_metadata_has_no_placeholder_fields(self):
        skill = read(SKILL)
        self.assertTrue(skill.startswith("---\nname: project-pilot\n"))
        self.assertNotIn("[TODO", skill)
        self.assertNotIn("YOUR-NAME", skill)


class UserExperienceTests(unittest.TestCase):
    def test_readme_covers_the_complete_nontechnical_journey(self):
        readme = read(ROOT / "README.md").lower()

        for topic in (
            "what project pilot does",
            "install",
            "try it",
            "choose a mode",
            "update",
            "share",
            "remove",
            "troubleshooting",
        ):
            self.assertIn(topic, readme)
        self.assertIn("use project pilot", readme)
        self.assertIn("no api key", readme)

    def test_setup_helper_has_safe_non_mutating_dry_run(self):
        setup = ROOT / "scripts/setup.sh"
        result = subprocess.run(
            ["sh", str(setup), "--dry-run"],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("codex plugin marketplace add", result.stdout)
        self.assertIn("codex plugin add project-pilot@project-pilot", result.stdout)
        self.assertIn("install-agents.sh", result.stdout)
        self.assertIn("DRY RUN", result.stdout)

    def test_original_license_and_attribution_are_preserved(self):
        license_text = read(ROOT / "LICENSE")
        notice = read(ROOT / "NOTICE.md")

        self.assertIn("Copyright (c) 2026 Daniel McAteer", license_text)
        self.assertIn("DannyMac180/sol-advisor", notice)
        self.assertIn("MIT", notice)


class VerificationTests(unittest.TestCase):
    def test_repository_verifier_passes(self):
        verifier = PLUGIN / "scripts/verify.sh"
        result = subprocess.run(
            ["sh", str(verifier)],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("Project Pilot verification passed", result.stdout)


if __name__ == "__main__":
    unittest.main()
