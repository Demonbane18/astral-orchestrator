import json
import re
import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MARKETPLACE = ROOT / ".agents/plugins/marketplace.json"
PLUGIN = ROOT / "plugins/project-pilot"
MANIFEST = PLUGIN / ".codex-plugin/plugin.json"
SKILL = PLUGIN / "skills/project-pilot/SKILL.md"
MODES = PLUGIN / "skills/project-pilot/references/modes-and-risk.md"
TEMPLATES = PLUGIN / "skills/project-pilot/references/work-templates.md"


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
        self.assertRegex(manifest["version"], r"^\d+\.\d+\.\d+$")
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

    def test_skill_has_no_model_or_custom_agent_dependency(self):
        installable_text = "\n".join(
            read(path)
            for path in sorted(PLUGIN.rglob("*"))
            if path.is_file()
        )

        forbidden = (
            r"gpt-[0-9]",
            r"sol_advisor_",
            r"inspect-agent-runtime",
            r"install-agents",
            r"\bjq\b",
        )
        for pattern in forbidden:
            self.assertIsNone(
                re.search(pattern, installable_text, flags=re.IGNORECASE),
                f"installable plugin contains forbidden dependency: {pattern}",
            )

    def test_delegation_is_optional_and_fallback_is_honest(self):
        skill = read(SKILL).lower()

        self.assertIn("when available", skill)
        self.assertIn("primary session", skill)
        self.assertIn("independent review", skill)
        self.assertIn("do not claim", skill)

    def test_risk_and_destructive_actions_are_gated(self):
        skill = read(SKILL).lower()
        modes = read(MODES).lower()

        self.assertIn("risk", skill)
        self.assertIn("verification", skill)
        self.assertIn("user confirmation", modes)
        self.assertIn("destructive", modes)
        self.assertIn("credentials", modes)

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
