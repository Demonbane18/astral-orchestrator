import importlib.util
import io
import json
import re
import subprocess
import sys
import tempfile
import tomllib
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest import mock


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
RUN_AGENT = PLUGIN / "scripts/run-agent.py"
CONFIGURE_EFFORT = PLUGIN / "scripts/configure-effort.py"
EFFORT_SETTINGS = PLUGIN / "scripts/effort_settings.py"
CONFIGURE_EFFORT_WRAPPER = ROOT / "scripts/configure-effort.sh"


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
        self.assertIn("fork_turns", routing)
        self.assertIn("none", routing)
        self.assertIn("--check", routing)
        self.assertIn("run-agent.py", routing)
        self.assertIn("exact-process", routing)

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
            self.assertIn(
                "do not spawn",
                profile["developer_instructions"].lower(),
                filename,
            )

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

    def test_agent_installer_removes_only_exact_project_pilot_profiles(self):
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

            remove = subprocess.run(
                ["sh", str(INSTALL_AGENTS), "--target-dir", str(target), "--remove"],
                cwd=ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(remove.returncode, 0, remove.stdout + remove.stderr)
            self.assertTrue(target.is_dir())
            self.assertFalse(any(target.iterdir()))

            protected = target / "project-pilot-luna-implementer.toml"
            protected.write_text("user-owned = true\n", encoding="utf-8")
            refused = subprocess.run(
                ["sh", str(INSTALL_AGENTS), "--target-dir", str(target), "--remove"],
                cwd=ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertNotEqual(refused.returncode, 0)
            self.assertIn("will not be removed", refused.stderr)
            self.assertEqual(protected.read_text(encoding="utf-8"), "user-owned = true\n")

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
                                    "id": "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
                                    "agent_nickname": "Parent",
                                    "agent_path": None,
                                    "model_provider": "openai",
                                    "secret": "must-not-leak",
                                },
                            }
                        ),
                        json.dumps(
                            {
                                "type": "turn_context",
                                "payload": {
                                    "model": "gpt-5.6-sol",
                                    "effort": "high",
                                    "sandbox_policy": {"type": "workspace-write"},
                                    "permission_profile": {"type": "managed"},
                                    "cwd": str(ROOT),
                                    "prompt": "must-not-leak",
                                },
                            }
                        ),
                        json.dumps(
                            {
                                "type": "session_meta",
                                "payload": {
                                    "id": thread_id,
                                    "parent_thread_id": "parent",
                                    "agent_nickname": "Atlas",
                                    "agent_path": "/profiles/project-pilot-luna-implementer.toml",
                                    "model_provider": "openai",
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
            self.assertEqual(evidence["agent_nickname"], "Atlas")
            self.assertTrue(
                evidence["agent_path"].endswith(
                    "/project-pilot-luna-implementer.toml"
                )
            )
            self.assertNotIn("agent_role", evidence)
            self.assertNotIn("secret", evidence)
            self.assertNotIn("prompt", evidence)

    def test_runtime_inspector_resolves_the_task_path_returned_by_spawn(self):
        thread_id = "87654321-4321-4321-4321-cba987654321"
        descendant_id = "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"
        agent_path = "/root/pilot_luna_unique"
        with tempfile.TemporaryDirectory() as directory:
            sessions = Path(directory)
            direct = sessions / f"rollout-direct-{thread_id}.jsonl"
            inherited = sessions / f"rollout-descendant-{descendant_id}.jsonl"
            records = (
                {
                    "type": "session_meta",
                    "payload": {
                        "id": thread_id,
                        "agent_nickname": "Nova",
                        "agent_path": agent_path,
                        "model_provider": "openai",
                    },
                },
                {
                    "type": "turn_context",
                    "payload": {
                        "model": "gpt-5.6-luna",
                        "effort": "xhigh",
                        "sandbox_policy": {"type": "workspace-write"},
                        "permission_profile": {"type": "managed"},
                        "cwd": str(ROOT),
                    },
                },
            )
            direct.write_text(
                "\n".join(json.dumps(record) for record in records) + "\n",
                encoding="utf-8",
            )
            inherited.write_text(
                json.dumps(records[0]) + "\n",
                encoding="utf-8",
            )

            result = subprocess.run(
                [
                    "sh",
                    str(INSPECT_RUNTIME),
                    "--sessions-dir",
                    str(sessions),
                    "--since-epoch",
                    "0",
                    "--agent-path",
                    agent_path,
                ],
                cwd=ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            evidence = json.loads(result.stdout)
            self.assertEqual(evidence["thread_id"], thread_id)
            self.assertEqual(evidence["agent_path"], agent_path)
            self.assertEqual(evidence["model"], "gpt-5.6-luna")

    def test_process_launcher_maps_every_role_to_exact_runtime_settings(self):
        expected = {
            "luna": (
                "project_pilot_luna_implementer",
                "gpt-5.6-luna",
                "xhigh",
                "workspace-write",
            ),
            "terra": (
                "project_pilot_terra_implementer",
                "gpt-5.6-terra",
                "xhigh",
                "workspace-write",
            ),
            "reviewer": (
                "project_pilot_sol_reviewer",
                "gpt-5.6-sol",
                "high",
                "read-only",
            ),
        }
        with tempfile.TemporaryDirectory() as directory:
            workdir = Path(directory) / "work"
            workdir.mkdir()
            prompt = Path(directory) / "packet.txt"
            prompt.write_text("bounded standalone packet\n", encoding="utf-8")

            for role, values in expected.items():
                result = subprocess.run(
                    [
                        "python3",
                        str(RUN_AGENT),
                        "--role",
                        role,
                        "--workdir",
                        str(workdir),
                        "--prompt-file",
                        str(prompt),
                        "--settings-file",
                        str(Path(directory) / "missing-effort-levels.toml"),
                        "--dry-run",
                    ],
                    cwd=ROOT,
                    check=False,
                    capture_output=True,
                    text=True,
                )
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                evidence = json.loads(result.stdout)
                self.assertEqual(
                    (
                        evidence["agent_name"],
                        evidence["model"],
                        evidence["effort"],
                        evidence["sandbox"],
                    ),
                    values,
                )
                self.assertEqual(evidence["prompt_bytes"], prompt.stat().st_size)
                self.assertNotIn("prompt", evidence)
                self.assertNotIn("developer_instructions", evidence)

    def test_process_launcher_constructs_and_runs_every_exact_route(self):
        spec = importlib.util.spec_from_file_location("project_pilot_run_agent", RUN_AGENT)
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader)
        launcher = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(launcher)

        with tempfile.TemporaryDirectory() as directory:
            workdir = Path(directory) / "work"
            workdir.mkdir()
            prompt = Path(directory) / "packet.txt"
            prompt_text = "standalone packet with private details\n"
            prompt.write_text(prompt_text, encoding="utf-8")

            for role, contract in launcher.ROLE_CONTRACTS.items():
                captured = {}
                prompt.write_text(prompt_text, encoding="utf-8")

                def fake_run(command, *, input, check):
                    prompt.write_text("replacement that must not be forwarded\n", encoding="utf-8")
                    captured["command"] = command
                    captured["prompt"] = input
                    captured["check"] = check
                    return subprocess.CompletedProcess(command, 23)

                output = io.StringIO()
                argv = [
                    str(RUN_AGENT),
                    "--role",
                    role,
                    "--workdir",
                    str(workdir),
                    "--prompt-file",
                    str(prompt),
                    "--settings-file",
                    str(Path(directory) / "missing-effort-levels.toml"),
                ]
                with (
                    mock.patch.object(sys, "argv", argv),
                    mock.patch.object(launcher.shutil, "which", return_value="/test/codex"),
                    mock.patch.object(launcher.subprocess, "run", side_effect=fake_run),
                    redirect_stdout(output),
                ):
                    return_code = launcher.main()

                profile = tomllib.loads(read(AGENTS / contract["filename"]))
                command = captured["command"]
                config_overrides = [
                    command[index + 1]
                    for index, value in enumerate(command)
                    if value == "-c"
                ]

                self.assertEqual(return_code, 23)
                self.assertEqual(captured["prompt"], prompt_text.encode())
                self.assertFalse(captured["check"])
                self.assertEqual(command[0:2], ["/test/codex", "exec"])
                self.assertEqual(command[command.index("--model") + 1], contract["model"])
                self.assertEqual(
                    command[command.index("--sandbox") + 1], contract["sandbox"]
                )
                self.assertEqual(
                    command[command.index("--cd") + 1], str(workdir.resolve())
                )
                self.assertEqual(command[-1], "-")
                self.assertIn(
                    f"model_reasoning_effort={json.dumps(contract['effort'])}",
                    config_overrides,
                )
                self.assertIn(
                    "developer_instructions="
                    + json.dumps(profile["developer_instructions"]),
                    config_overrides,
                )
                route_header = output.getvalue()
                self.assertIn("PROJECT_PILOT_ROUTE ", route_header)
                self.assertNotIn(prompt_text.strip(), route_header)
                self.assertNotIn(profile["developer_instructions"], route_header)

    def test_effort_configurator_round_trips_partial_changes_and_reset(self):
        with tempfile.TemporaryDirectory() as directory:
            settings = Path(directory) / "project-pilot" / "effort-levels.toml"

            configured = subprocess.run(
                [
                    "python3",
                    str(CONFIGURE_EFFORT),
                    "--settings-file",
                    str(settings),
                    "--orchestrator",
                    "medium",
                    "--luna",
                    "low",
                    "--terra",
                    "max",
                    "--reviewer",
                    "ultra",
                    "--json",
                ],
                cwd=ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(
                configured.returncode, 0, configured.stdout + configured.stderr
            )
            self.assertEqual(
                json.loads(configured.stdout)["effort"],
                {
                    "orchestrator": "medium",
                    "luna": "low",
                    "terra": "max",
                    "reviewer": "ultra",
                },
            )

            partial = subprocess.run(
                [
                    "python3",
                    str(CONFIGURE_EFFORT),
                    "--settings-file",
                    str(settings),
                    "--luna",
                    "xhigh",
                    "--json",
                ],
                cwd=ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(partial.returncode, 0, partial.stdout + partial.stderr)
            self.assertEqual(
                json.loads(partial.stdout)["effort"],
                {
                    "orchestrator": "medium",
                    "luna": "xhigh",
                    "terra": "max",
                    "reviewer": "ultra",
                },
            )

            reset = subprocess.run(
                [
                    "python3",
                    str(CONFIGURE_EFFORT),
                    "--settings-file",
                    str(settings),
                    "--reset",
                    "--json",
                ],
                cwd=ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(reset.returncode, 0, reset.stdout + reset.stderr)
            self.assertEqual(
                json.loads(reset.stdout)["effort"],
                {
                    "orchestrator": "high",
                    "luna": "xhigh",
                    "terra": "xhigh",
                    "reviewer": "high",
                },
            )
            self.assertTrue(settings.is_file())

    def test_process_launcher_uses_configured_effort_and_marks_native_mismatch(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            settings = root / "effort-levels.toml"
            settings.write_text(
                """[effort]
orchestrator = "medium"
luna = "low"
terra = "minimal"
reviewer = "xhigh"
""",
                encoding="utf-8",
            )
            workdir = root / "work"
            workdir.mkdir()
            prompt = root / "packet.txt"
            prompt.write_text("bounded standalone packet\n", encoding="utf-8")

            for role, effort in {
                "luna": "low",
                "terra": "minimal",
                "reviewer": "xhigh",
            }.items():
                result = subprocess.run(
                    [
                        "python3",
                        str(RUN_AGENT),
                        "--role",
                        role,
                        "--workdir",
                        str(workdir),
                        "--prompt-file",
                        str(prompt),
                        "--settings-file",
                        str(settings),
                        "--dry-run",
                    ],
                    cwd=ROOT,
                    check=False,
                    capture_output=True,
                    text=True,
                )
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                evidence = json.loads(result.stdout)
                self.assertEqual(evidence["effort"], effort)
                self.assertEqual(evidence["effort_source"], "custom")
                self.assertFalse(evidence["native_profile_compatible"])

    def test_invalid_effort_settings_fail_before_a_process_starts(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            workdir = root / "work"
            workdir.mkdir()
            prompt = root / "packet.txt"
            prompt.write_text("bounded standalone packet\n", encoding="utf-8")

            for contents, expected_error in (
                (
                    "[effort]\nluna = \"impossible\"\n",
                    "unsupported effort",
                ),
                (
                    "[effort]\nunknown_lane = \"high\"\n",
                    "unknown effort lane",
                ),
            ):
                settings = root / "effort-levels.toml"
                settings.write_text(contents, encoding="utf-8")
                result = subprocess.run(
                    [
                        "python3",
                        str(RUN_AGENT),
                        "--role",
                        "luna",
                        "--workdir",
                        str(workdir),
                        "--prompt-file",
                        str(prompt),
                        "--settings-file",
                        str(settings),
                        "--dry-run",
                    ],
                    cwd=ROOT,
                    check=False,
                    capture_output=True,
                    text=True,
                )
                self.assertNotEqual(result.returncode, 0)
                self.assertIn(expected_error, result.stderr.lower())

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
        self.assertIn("no additional api key", readme)
        self.assertIn("sol high", readme)
        self.assertIn("luna xhigh", readme)
        self.assertIn("terra xhigh", readme)
        self.assertIn("three agent profiles", readme)
        self.assertIn("--remove", readme)
        self.assertIn("cannot grant model access", readme)
        self.assertIn("codex plugin list --marketplace project-pilot", readme)
        self.assertIn("tune the effort levels", readme)
        self.assertIn("configure-effort.sh", readme)
        self.assertIn("minimal", readme)
        self.assertIn("ultra", readme)
        self.assertIn("model-dependent", readme)

    def test_effort_tools_are_packaged_and_routing_respects_custom_values(self):
        self.assertTrue(CONFIGURE_EFFORT.is_file())
        self.assertTrue(EFFORT_SETTINGS.is_file())
        self.assertTrue(CONFIGURE_EFFORT_WRAPPER.is_file())

        routing = read(ROUTING).lower()
        self.assertIn("effort-levels.toml", routing)
        self.assertIn("configured orchestrator effort", routing)
        self.assertIn("native profile", routing)
        self.assertIn("exact-process", routing)
        self.assertIn("custom effort", routing)
        self.assertNotIn("sol high primary session", routing)

        self.assertIn("configured effort", read(MODES).lower())
        self.assertIn("configured effort", read(ROOT / "AGENTS.md").lower())
        self.assertIn(
            "configured efforts",
            load_json(MANIFEST)["interface"]["longDescription"].lower(),
        )
        self.assertIn(
            "23 repository contract tests",
            read(ROOT / "docs/IMPROVEMENTS.md").lower(),
        )

    def test_setup_helper_has_safe_non_mutating_dry_run(self):
        setup = ROOT / "scripts/setup.sh"
        setup_text = read(setup)
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
        self.assertIn("command -v python3", setup_text)
        self.assertIn("sys.version_info >= (3, 11)", setup_text)
        self.assertIn("python 3.11", read(ROOT / "README.md").lower())

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
