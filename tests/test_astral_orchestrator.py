import importlib.util
import hashlib
import io
import json
import re
import shutil
import subprocess
import sys
import tempfile
import tomllib
import unittest
import xml.etree.ElementTree as ET
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
MARKETPLACE = ROOT / ".agents/plugins/marketplace.json"
PLUGIN = ROOT / "plugins/astral-orchestrator"
LICENSE = ROOT / "LICENSE"
NOTICE = ROOT / "NOTICE.md"
PLUGIN_LICENSE = PLUGIN / "LICENSE"
PLUGIN_NOTICE = PLUGIN / "NOTICE.md"
MANIFEST = PLUGIN / ".codex-plugin/plugin.json"
SKILL = PLUGIN / "skills/astral-orchestrator/SKILL.md"
MODES = PLUGIN / "skills/astral-orchestrator/references/modes-and-risk.md"
TEMPLATES = PLUGIN / "skills/astral-orchestrator/references/work-templates.md"
ROUTING = PLUGIN / "skills/astral-orchestrator/references/routing-and-preflight.md"
AGENTS = PLUGIN / "agents"
INSTALL_AGENTS = PLUGIN / "scripts/install-agents.sh"
INSPECT_RUNTIME = PLUGIN / "scripts/inspect-agent-runtime.sh"
RUN_AGENT = PLUGIN / "scripts/run-agent.py"
CONFIGURE_EFFORT = PLUGIN / "scripts/configure-effort.py"
EFFORT_SETTINGS = PLUGIN / "scripts/effort_settings.py"
CONFIGURE_EFFORT_WRAPPER = ROOT / "scripts/configure-effort.sh"
BENCHMARK_SCORECARD = PLUGIN / "scripts/benchmark-scorecard.py"
BENCHMARK_GUIDE = ROOT / "benchmarks/README.md"
CONTEXT_FOOTPRINT = ROOT / "benchmarks/context-footprint-2026-08-03.json"
CONTEXT_FOOTPRINT_MEASURER = ROOT / "benchmarks/measure_instruction_context.py"
ROUTING_DIAGRAM = ROOT / "assets/diagrams/routing-and-verification.svg"
ROUTING_EXCALIDRAW = ROOT / "assets/diagrams/routing-and-verification.excalidraw"
SCORECARD_DIAGRAM = ROOT / "assets/diagrams/outcome-scorecard.svg"
SCORECARD_EXCALIDRAW = ROOT / "assets/diagrams/outcome-scorecard.excalidraw"
SPEC = ROOT / "docs/SPEC.md"


def read(path: Path) -> str:
    if not path.is_file():
        raise AssertionError(f"required file is missing: {path.relative_to(ROOT)}")
    return path.read_text(encoding="utf-8")


def load_json(path: Path):
    return json.loads(read(path))


class MarketplaceTests(unittest.TestCase):
    def test_marketplace_exposes_one_local_astral_orchestrator_plugin(self):
        marketplace = load_json(MARKETPLACE)

        self.assertEqual(marketplace["name"], "astral-orchestrator")
        self.assertEqual(marketplace["interface"]["displayName"], "Astral Orchestrator")
        self.assertEqual(len(marketplace["plugins"]), 1)

        entry = marketplace["plugins"][0]
        self.assertEqual(entry["name"], "astral-orchestrator")
        self.assertEqual(
            entry["source"],
            {"source": "local", "path": "./plugins/astral-orchestrator"},
        )
        self.assertEqual(entry["policy"]["installation"], "AVAILABLE")
        self.assertEqual(entry["policy"]["authentication"], "ON_INSTALL")
        self.assertEqual(entry["category"], "Productivity")

    def test_manifest_is_minimal_and_shareable(self):
        manifest = load_json(MANIFEST)

        self.assertEqual(manifest["name"], "astral-orchestrator")
        self.assertEqual(manifest["version"], "3.1.3")
        self.assertEqual(manifest["license"], "MIT")
        self.assertEqual(manifest["skills"], "./skills/")
        self.assertEqual(manifest["interface"]["displayName"], "Astral Orchestrator")
        self.assertEqual(manifest["interface"]["category"], "Productivity")
        self.assertEqual(
            manifest["homepage"],
            "https://github.com/Demonbane18/astral-orchestrator",
        )
        self.assertEqual(
            manifest["repository"],
            "https://github.com/Demonbane18/astral-orchestrator",
        )
        self.assertNotIn("mcpServers", manifest)
        self.assertNotIn("apps", manifest)
        self.assertNotIn("hooks", manifest)
        self.assertTrue(read(SPEC).startswith("# Spec: Astral Orchestrator v3.1"))

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
            "astral_orchestrator_luna_implementer",
            "astral_orchestrator_terra_implementer",
            "astral_orchestrator_sol_reviewer",
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

            conflict = target / "astral-orchestrator-luna-implementer.toml"
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

    def test_agent_installer_removes_only_exact_astral_orchestrator_profiles(self):
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

            protected = target / "astral-orchestrator-luna-implementer.toml"
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
                                    "agent_path": "/profiles/astral-orchestrator-luna-implementer.toml",
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
                    "/astral-orchestrator-luna-implementer.toml"
                )
            )
            self.assertNotIn("agent_role", evidence)
            self.assertNotIn("secret", evidence)
            self.assertNotIn("prompt", evidence)

    def test_runtime_inspector_resolves_the_task_path_returned_by_spawn(self):
        thread_id = "87654321-4321-4321-4321-cba987654321"
        descendant_id = "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"
        agent_path = "/root/astral_luna_unique"
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
                "astral_orchestrator_luna_implementer",
                "gpt-5.6-luna",
                "xhigh",
                "workspace-write",
            ),
            "terra": (
                "astral_orchestrator_terra_implementer",
                "gpt-5.6-terra",
                "xhigh",
                "workspace-write",
            ),
            "reviewer": (
                "astral_orchestrator_sol_reviewer",
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
            prompt.chmod(0o600)

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
        spec = importlib.util.spec_from_file_location("astral_orchestrator_run_agent", RUN_AGENT)
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
            prompt.chmod(0o600)

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
                self.assertIn("ASTRAL_ORCHESTRATOR_ROUTE ", route_header)
                self.assertNotIn(prompt_text.strip(), route_header)
                self.assertNotIn(profile["developer_instructions"], route_header)

    def test_process_launcher_rejects_a_group_or_other_readable_prompt_packet_before_starting_codex(self):
        spec = importlib.util.spec_from_file_location("astral_orchestrator_run_agent", RUN_AGENT)
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader)
        launcher = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(launcher)

        with tempfile.TemporaryDirectory() as directory:
            workdir = Path(directory) / "work"
            workdir.mkdir()
            prompt = Path(directory) / "packet.txt"
            prompt.write_text("packet must remain private\n", encoding="utf-8")
            prompt.chmod(0o644)
            errors = io.StringIO()
            argv = [
                str(RUN_AGENT),
                "--role",
                "luna",
                "--workdir",
                str(workdir),
                "--prompt-file",
                str(prompt),
                "--settings-file",
                str(Path(directory) / "missing-effort-levels.toml"),
            ]
            with (
                mock.patch.object(sys, "argv", argv),
                mock.patch.object(launcher.shutil, "which") as find_codex,
                mock.patch.object(launcher.subprocess, "run") as start_codex,
                redirect_stderr(errors),
            ):
                with self.assertRaises(SystemExit) as raised:
                    launcher.main()

            self.assertEqual(raised.exception.code, 1)
            self.assertIn("private", errors.getvalue().lower())
            find_codex.assert_not_called()
            start_codex.assert_not_called()

    def test_effort_configurator_round_trips_partial_changes_and_reset(self):
        with tempfile.TemporaryDirectory() as directory:
            settings = Path(directory) / "astral-orchestrator" / "effort-levels.toml"

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
            prompt.chmod(0o600)

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
            prompt.chmod(0o600)

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
        self.assertTrue(skill.startswith("---\nname: astral-orchestrator\n"))
        self.assertNotIn("[TODO", skill)
        self.assertNotIn("YOUR-NAME", skill)


class UserExperienceTests(unittest.TestCase):
    def test_readme_covers_the_complete_nontechnical_journey(self):
        readme = read(ROOT / "README.md").lower()

        for topic in (
            "quick install",
            "what astral orchestrator does",
            "requirements",
            "installation",
            "first use",
            "modes",
            "configurable effort levels",
            "how routing and verification work",
            "safety and privacy",
            "updating and the 3.0 migration",
            "uninstalling",
            "troubleshooting",
            "frequently asked questions",
            "sharing",
            "contributor commands",
            "license",
            "sol advisor attribution",
        ):
            self.assertIn(topic, readme)
        self.assertIn("use astral orchestrator", readme)
        self.assertIn("no api key", readme)
        self.assertIn("sol high", readme)
        self.assertIn("luna xhigh", readme)
        self.assertIn("terra xhigh", readme)
        self.assertIn("three companion profiles", readme)
        self.assertIn("--remove", readme)
        self.assertIn("cannot grant access to models", readme)
        self.assertIn("codex plugin list --marketplace astral-orchestrator", readme)
        self.assertIn("configurable effort levels", readme)
        self.assertIn("configure-effort.sh", readme)
        self.assertIn("minimal", readme)
        self.assertIn("ultra", readme)
        self.assertIn("model-dependent", readme)
        self.assertIn("https://github.com/demonbane18/astral-orchestrator", readme)

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

    def test_readme_explains_heuristic_routing_and_the_local_benchmark(self):
        readme = " ".join(read(ROOT / "README.md").lower().split())

        self.assertIn("published, installable, open-source codex plugin", readme)
        self.assertIn("v3.1.3", readme)
        self.assertIn("not listed or endorsed by codex marketplace", readme)
        self.assertIn("mode determines whether to delegate", readme)
        self.assertIn("work characteristics choose sol, luna, or terra", readme)
        self.assertIn("instruction-context loading only", readme)
        self.assertIn("does not prove every multi-agent run uses fewer total tokens", readme)
        self.assertNotIn("mermaid", readme)
        self.assertIn("single-sol", readme)
        self.assertIn("repeated trials", readme)
        self.assertIn("identical acceptance checks", readme)
        self.assertIn("benchmark-scorecard.py", readme)
        self.assertIn("requested reasoning level/budget", readme)
        self.assertIn("increase latency and usage", readme)
        self.assertIn("do not guarantee a better answer", readme)

        for svg, source in (
            (ROUTING_DIAGRAM, ROUTING_EXCALIDRAW),
            (SCORECARD_DIAGRAM, SCORECARD_EXCALIDRAW),
        ):
            self.assertTrue(svg.is_file(), svg)
            self.assertTrue(source.is_file(), source)
            self.assertIn(svg.relative_to(ROOT).as_posix(), readme)
            self.assertIn(source.relative_to(ROOT).as_posix(), readme)
            self.assertEqual(ET.parse(svg).getroot().tag, "{http://www.w3.org/2000/svg}svg")
            excalidraw = load_json(source)
            self.assertEqual(excalidraw["type"], "excalidraw")
            self.assertTrue(excalidraw["elements"])

    def test_editable_diagrams_preserve_rendered_labels_and_quick_handoff(self):
        namespace = {"svg": "http://www.w3.org/2000/svg"}

        routing_root = ET.parse(ROUTING_DIAGRAM).getroot()
        routing_edge = routing_root.find(
            ".//svg:path[@id='quick-to-handoff']", namespace
        )
        self.assertIsNotNone(routing_edge)
        self.assertEqual(routing_edge.get("data-from"), "Sol primary + self-review")
        self.assertEqual(routing_edge.get("data-to"), "Evidence-backed handoff")
        self.assertEqual(routing_edge.get("marker-end"), "url(#gold-arrow)")

        routing_source = load_json(ROUTING_EXCALIDRAW)
        routing_elements = {element["id"]: element for element in routing_source["elements"]}
        source_edge = routing_elements["quick-to-handoff"]
        self.assertEqual(source_edge["type"], "arrow")
        self.assertEqual(source_edge["startBinding"]["elementId"], "quick-sol")
        self.assertEqual(source_edge["endBinding"]["elementId"], "handoff")

        for svg, source in (
            (ROUTING_DIAGRAM, ROUTING_EXCALIDRAW),
            (SCORECARD_DIAGRAM, SCORECARD_EXCALIDRAW),
        ):
            svg_root = ET.parse(svg).getroot()
            svg_text = " ".join(
                " ".join("".join(text.itertext()).split())
                for text in svg_root.findall(".//svg:text", namespace)
            )
            source_text = " ".join(
                " ".join(element["text"].split())
                for element in load_json(source)["elements"]
                if element["type"] == "text" and not element["isDeleted"]
            )
            self.assertEqual(source_text, svg_text, source.name)

    def test_context_footprint_evidence_matches_the_published_instruction_files(self):
        evidence = load_json(CONTEXT_FOOTPRINT)
        self.assertTrue(CONTEXT_FOOTPRINT_MEASURER.is_file())
        self.assertEqual(evidence["measured_on"], "2026-08-03")
        self.assertEqual(
            evidence["tokenizer"],
            {"library": "tiktoken", "version": "0.13.0", "encoding": "o200k_base"},
        )

        expected = {
            "plugins/astral-orchestrator/skills/astral-orchestrator/SKILL.md": (8501, 1205, 1791),
            "plugins/astral-orchestrator/skills/astral-orchestrator/references/modes-and-risk.md": (4027, 610, 788),
            "plugins/astral-orchestrator/skills/astral-orchestrator/references/work-templates.md": (3224, 455, 745),
            "plugins/astral-orchestrator/skills/astral-orchestrator/references/routing-and-preflight.md": (8149, 1158, 1725),
        }
        self.assertEqual({item["path"] for item in evidence["files"]}, set(expected))
        for item in evidence["files"]:
            path = ROOT / item["path"]
            data = path.read_bytes()
            self.assertEqual(
                (item["bytes"], item["words"], item["tokens"]), expected[item["path"]]
            )
            self.assertEqual(item["bytes"], len(data))
            self.assertEqual(item["words"], len(data.decode("utf-8").split()))
            self.assertEqual(item["sha256"], hashlib.sha256(data).hexdigest())

        self.assertEqual(evidence["bundles"]["core"]["tokens"], 1791)
        self.assertEqual(
            evidence["bundles"]["quick"],
            {
                "paths": [
                    "plugins/astral-orchestrator/skills/astral-orchestrator/SKILL.md",
                    "plugins/astral-orchestrator/skills/astral-orchestrator/references/modes-and-risk.md",
                    "plugins/astral-orchestrator/skills/astral-orchestrator/references/work-templates.md",
                ],
                "tokens": 3324,
            },
        )
        self.assertEqual(evidence["bundles"]["full"]["tokens"], 5049)
        self.assertEqual(evidence["quick_vs_full"], {"tokens_avoided": 1725, "percent_avoided": 34.2})
        self.assertIn("tiktoken==0.13.0", read(BENCHMARK_GUIDE))
        self.assertIn("measure_instruction_context.py", read(BENCHMARK_GUIDE))

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
        self.assertIn("codex plugin add astral-orchestrator@astral-orchestrator", result.stdout)
        self.assertIn("install-agents.sh", result.stdout)
        self.assertIn("DRY RUN", result.stdout)
        self.assertIn("command -v python3", setup_text)
        self.assertIn("sys.version_info >= (3, 11)", setup_text)
        self.assertIn("python 3.11", read(ROOT / "README.md").lower())

    def test_original_license_and_attribution_are_preserved(self):
        license_text = read(LICENSE)
        notice = read(NOTICE)

        self.assertIn("Copyright (c) 2026 Daniel McAteer", license_text)
        self.assertIn("DannyMac180/sol-advisor", notice)
        self.assertIn("MIT", notice)

    def test_distributable_license_and_notice_match_the_canonical_notices(self):
        self.assertEqual(PLUGIN_LICENSE.read_bytes(), LICENSE.read_bytes())
        self.assertEqual(PLUGIN_NOTICE.read_bytes(), NOTICE.read_bytes())


class BenchmarkScorecardTests(unittest.TestCase):
    def test_scorecard_validates_and_aggregates_repeated_comparable_trials(self):
        route = lambda role, model, task_id: {
            "role": role,
            "model": model,
            "effort": "high" if model == "gpt-5.6-sol" else "xhigh",
            "expected_effort": "high" if model == "gpt-5.6-sol" else "xhigh",
            "task_id": task_id,
        }
        records = []
        for case_id in ("search-box", "empty-state"):
            for trial in (1, 2):
                records.append(
                    {
                        "schema_version": 1,
                        "trial_id": f"{case_id}-single-sol-{trial}",
                        "case_id": case_id,
                        "case_fingerprint": f"{case_id}-v1",
                        "trial": trial,
                        "strategy": "single-sol",
                        "acceptance_checks": ["unit-tests", "manual-review"],
                        "accepted": trial == 1,
                        "first_pass_accepted": trial == 1,
                        "rework_required": trial != 1,
                        "wall_time_seconds": 40 + trial,
                        "model_calls": 1,
                        "input_tokens": 100,
                        "output_tokens": 200,
                        "quality_score": 80,
                        "quality_score_blinded": True,
                        "route_evidence": [
                            route("single-sol", "gpt-5.6-sol", f"sol-{case_id}-{trial}")
                        ],
                    }
                )
                records.append(
                    {
                        "schema_version": 1,
                        "trial_id": f"{case_id}-astral-{trial}",
                        "case_id": case_id,
                        "case_fingerprint": f"{case_id}-v1",
                        "trial": trial,
                        "strategy": "astral",
                        "acceptance_checks": ["manual-review", "unit-tests"],
                        "accepted": True,
                        "first_pass_accepted": trial == 1,
                        "rework_required": trial != 1,
                        "wall_time_seconds": 60 + trial,
                        "model_calls": 3,
                        "input_tokens": 150,
                        "output_tokens": 300,
                        "quality_score": 90,
                        "quality_score_blinded": True,
                        "route_evidence": [
                            route("orchestrator", "gpt-5.6-sol", f"lead-{case_id}-{trial}"),
                            route("terra", "gpt-5.6-terra", f"worker-{case_id}-{trial}"),
                            route("reviewer", "gpt-5.6-sol", f"review-{case_id}-{trial}"),
                        ],
                    }
                )

        with tempfile.TemporaryDirectory() as directory:
            trials = Path(directory) / "trials.jsonl"
            trials.write_text(
                "\n".join(json.dumps(record) for record in records) + "\n",
                encoding="utf-8",
            )
            result = subprocess.run(
                ["python3", str(BENCHMARK_SCORECARD), "--format", "json", str(trials)],
                cwd=ROOT,
                check=False,
                capture_output=True,
                text=True,
            )

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        report = json.loads(result.stdout)
        self.assertEqual(report["comparability"]["case_count"], 2)
        self.assertEqual(report["comparability"]["paired_trial_count"], 4)
        self.assertEqual(report["strategies"]["single-sol"]["success_rate"], 0.5)
        self.assertEqual(report["strategies"]["astral"]["success_rate"], 1.0)
        self.assertEqual(report["strategies"]["astral"]["route_correct_rate"], 1.0)
        self.assertEqual(report["strategies"]["astral"]["mean_total_tokens"], 450.0)
        self.assertEqual(
            report["comparison"]["astral_minus_single_sol"]["success_rate_percentage_points"],
            50.0,
        )

    def test_scorecard_rejects_incomparable_acceptance_checks(self):
        def record(strategy, checks, route_evidence):
            return {
                "schema_version": 1,
                "trial_id": f"case-1-{strategy}",
                "case_id": "case-1",
                "case_fingerprint": "case-1-v1",
                "trial": 1,
                "strategy": strategy,
                "acceptance_checks": checks,
                "accepted": True,
                "first_pass_accepted": True,
                "rework_required": False,
                "wall_time_seconds": 10,
                "model_calls": 1 if strategy == "single-sol" else 3,
                "route_evidence": route_evidence,
            }

        route = lambda role, model, task_id: {
            "role": role,
            "model": model,
            "effort": "high" if model == "gpt-5.6-sol" else "xhigh",
            "expected_effort": "high" if model == "gpt-5.6-sol" else "xhigh",
            "task_id": task_id,
        }
        records = [
            record(
                "single-sol",
                ["unit-tests"],
                [route("single-sol", "gpt-5.6-sol", "control")],
            ),
            record(
                "astral",
                ["manual-review"],
                [
                    route("orchestrator", "gpt-5.6-sol", "lead"),
                    route("luna", "gpt-5.6-luna", "worker"),
                    route("reviewer", "gpt-5.6-sol", "review"),
                ],
            ),
        ]

        with tempfile.TemporaryDirectory() as directory:
            trials = Path(directory) / "trials.jsonl"
            trials.write_text(
                "\n".join(json.dumps(item) for item in records) + "\n",
                encoding="utf-8",
            )
            result = subprocess.run(
                [
                    "python3",
                    str(BENCHMARK_SCORECARD),
                    "--min-trials",
                    "1",
                    str(trials),
                ],
                cwd=ROOT,
                check=False,
                capture_output=True,
                text=True,
            )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("acceptance checks differ", result.stderr.lower())

    def test_scorecard_rejects_malformed_jsonl(self):
        with tempfile.TemporaryDirectory() as directory:
            trials = Path(directory) / "trials.jsonl"
            trials.write_text('{"schema_version": 1, bad-json}\n', encoding="utf-8")
            result = subprocess.run(
                ["python3", str(BENCHMARK_SCORECARD), str(trials)],
                cwd=ROOT,
                check=False,
                capture_output=True,
                text=True,
            )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("line 1: invalid json", result.stderr.lower())

    def test_scorecard_requires_rework_after_a_failed_first_pass_that_is_accepted(self):
        record = {
            "schema_version": 1,
            "trial_id": "case-1-single-sol",
            "case_id": "case-1",
            "case_fingerprint": "case-1-v1",
            "trial": 1,
            "strategy": "single-sol",
            "acceptance_checks": ["unit-tests"],
            "accepted": True,
            "first_pass_accepted": False,
            "rework_required": False,
            "wall_time_seconds": 10,
            "model_calls": 1,
            "route_evidence": [
                {
                    "role": "single-sol",
                    "model": "gpt-5.6-sol",
                    "effort": "high",
                    "expected_effort": "high",
                    "task_id": "control",
                }
            ],
        }
        with tempfile.TemporaryDirectory() as directory:
            trials = Path(directory) / "trials.jsonl"
            trials.write_text(json.dumps(record) + "\n", encoding="utf-8")
            result = subprocess.run(
                ["python3", str(BENCHMARK_SCORECARD), "--min-trials", "1", str(trials)],
                cwd=ROOT,
                check=False,
                capture_output=True,
                text=True,
            )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("accepted is true", result.stderr.lower())
        self.assertIn("rework_required", result.stderr)

    def test_scorecard_rejects_route_settings_that_change_across_repetitions(self):
        def route(role, model, effort, task_id):
            return {
                "role": role,
                "model": model,
                "effort": effort,
                "expected_effort": effort,
                "task_id": task_id,
            }

        records = []
        for trial in (1, 2):
            records.extend(
                (
                    {
                        "schema_version": 1,
                        "trial_id": f"control-{trial}",
                        "case_id": "case-1",
                        "case_fingerprint": "case-1-v1",
                        "trial": trial,
                        "strategy": "single-sol",
                        "acceptance_checks": ["unit-tests"],
                        "accepted": True,
                        "first_pass_accepted": True,
                        "rework_required": False,
                        "wall_time_seconds": 10,
                        "model_calls": 1,
                        "route_evidence": [
                            route("single-sol", "gpt-5.6-sol", "high", f"control-{trial}")
                        ],
                    },
                    {
                        "schema_version": 1,
                        "trial_id": f"astral-{trial}",
                        "case_id": "case-1",
                        "case_fingerprint": "case-1-v1",
                        "trial": trial,
                        "strategy": "astral",
                        "acceptance_checks": ["unit-tests"],
                        "accepted": True,
                        "first_pass_accepted": True,
                        "rework_required": False,
                        "wall_time_seconds": 20,
                        "model_calls": 3,
                        "route_evidence": [
                            route("orchestrator", "gpt-5.6-sol", "high", f"lead-{trial}"),
                            route(
                                "terra",
                                "gpt-5.6-terra",
                                "xhigh" if trial == 1 else "high",
                                f"worker-{trial}",
                            ),
                            route("reviewer", "gpt-5.6-sol", "high", f"review-{trial}"),
                        ],
                    },
                )
            )

        with tempfile.TemporaryDirectory() as directory:
            trials = Path(directory) / "trials.jsonl"
            trials.write_text(
                "\n".join(json.dumps(record) for record in records) + "\n",
                encoding="utf-8",
            )
            result = subprocess.run(
                ["python3", str(BENCHMARK_SCORECARD), str(trials)],
                cwd=ROOT,
                check=False,
                capture_output=True,
                text=True,
            )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("expected_effort configuration changes", result.stderr)

    def test_scorecard_rejects_route_task_ids_reused_across_trials(self):
        def route(role, model, effort, task_id):
            return {
                "role": role,
                "model": model,
                "effort": effort,
                "expected_effort": effort,
                "task_id": task_id,
            }

        shared_task_id = "must-not-be-reused"
        records = [
            {
                "schema_version": 1,
                "trial_id": "control-1",
                "case_id": "case-1",
                "case_fingerprint": "case-1-v1",
                "trial": 1,
                "strategy": "single-sol",
                "acceptance_checks": ["unit-tests"],
                "accepted": True,
                "first_pass_accepted": True,
                "rework_required": False,
                "wall_time_seconds": 10,
                "model_calls": 1,
                "route_evidence": [
                    route("single-sol", "gpt-5.6-sol", "high", shared_task_id)
                ],
            },
            {
                "schema_version": 1,
                "trial_id": "astral-1",
                "case_id": "case-1",
                "case_fingerprint": "case-1-v1",
                "trial": 1,
                "strategy": "astral",
                "acceptance_checks": ["unit-tests"],
                "accepted": True,
                "first_pass_accepted": True,
                "rework_required": False,
                "wall_time_seconds": 20,
                "model_calls": 3,
                "route_evidence": [
                    route("orchestrator", "gpt-5.6-sol", "high", shared_task_id),
                    route("luna", "gpt-5.6-luna", "xhigh", "worker-1"),
                    route("reviewer", "gpt-5.6-sol", "high", "review-1"),
                ],
            },
        ]

        with tempfile.TemporaryDirectory() as directory:
            trials = Path(directory) / "trials.jsonl"
            trials.write_text(
                "\n".join(json.dumps(record) for record in records) + "\n",
                encoding="utf-8",
            )
            result = subprocess.run(
                ["python3", str(BENCHMARK_SCORECARD), "--min-trials", "1", str(trials)],
                cwd=ROOT,
                check=False,
                capture_output=True,
                text=True,
            )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("duplicate route task_id", result.stderr)

    def test_scorecard_rejects_observed_route_effort_changes_across_repetitions(self):
        guide = read(BENCHMARK_GUIDE)
        example = re.search(r"```jsonl\n(.*?)\n```", guide, flags=re.DOTALL)
        self.assertIsNotNone(example, "benchmark guide must include a JSONL example")
        records = [json.loads(line) for line in example.group(1).splitlines()]
        astral_trial = next(
            record
            for record in records
            if record["strategy"] == "astral" and record["trial"] == 2
        )
        next(
            route for route in astral_trial["route_evidence"] if route["role"] == "terra"
        )["effort"] = "high"

        with tempfile.TemporaryDirectory() as directory:
            trials = Path(directory) / "trials.jsonl"
            trials.write_text(
                "\n".join(json.dumps(record) for record in records) + "\n",
                encoding="utf-8",
            )
            result = subprocess.run(
                ["python3", str(BENCHMARK_SCORECARD), str(trials)],
                cwd=ROOT,
                check=False,
                capture_output=True,
                text=True,
            )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("observed route effort changes", result.stderr)

    def test_scorecard_requires_at_least_one_model_call_per_route_evidence_item(self):
        record = {
            "schema_version": 1,
            "trial_id": "control-1",
            "case_id": "case-1",
            "case_fingerprint": "case-1-v1",
            "trial": 1,
            "strategy": "single-sol",
            "acceptance_checks": ["unit-tests"],
            "accepted": True,
            "first_pass_accepted": True,
            "rework_required": False,
            "wall_time_seconds": 10,
            "model_calls": 1,
            "route_evidence": [
                {
                    "role": "single-sol",
                    "model": "gpt-5.6-sol",
                    "effort": "high",
                    "expected_effort": "high",
                    "task_id": "control-1",
                },
                {
                    "role": "reviewer",
                    "model": "gpt-5.6-sol",
                    "effort": "high",
                    "expected_effort": "high",
                    "task_id": "review-1",
                },
            ],
        }

        with tempfile.TemporaryDirectory() as directory:
            trials = Path(directory) / "trials.jsonl"
            trials.write_text(json.dumps(record) + "\n", encoding="utf-8")
            result = subprocess.run(
                ["python3", str(BENCHMARK_SCORECARD), "--min-trials", "1", str(trials)],
                cwd=ROOT,
                check=False,
                capture_output=True,
                text=True,
            )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("model_calls", result.stderr)
        self.assertIn("route_evidence", result.stderr)

    def test_scorecard_accepts_the_jsonl_example_in_the_benchmark_guide(self):
        guide = read(BENCHMARK_GUIDE)
        example = re.search(r"```jsonl\n(.*?)\n```", guide, flags=re.DOTALL)
        self.assertIsNotNone(example, "benchmark guide must include a JSONL example")

        with tempfile.TemporaryDirectory() as directory:
            trials = Path(directory) / "trials.jsonl"
            trials.write_text(example.group(1) + "\n", encoding="utf-8")
            result = subprocess.run(
                ["python3", str(BENCHMARK_SCORECARD), str(trials)],
                cwd=ROOT,
                check=False,
                capture_output=True,
                text=True,
            )

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("Astral Orchestrator benchmark scorecard", result.stdout)


class VerificationTests(unittest.TestCase):
    def make_package_fixture(self, directory: str) -> Path:
        fixture_root = Path(directory) / "repository"
        fixture_plugin = fixture_root / "plugins/astral-orchestrator"
        fixture_wrapper = fixture_root / "scripts/configure-effort.sh"

        fixture_plugin.parent.mkdir(parents=True)
        fixture_wrapper.parent.mkdir(parents=True)
        shutil.copytree(PLUGIN, fixture_plugin)
        shutil.copy2(LICENSE, fixture_root / "LICENSE")
        shutil.copy2(NOTICE, fixture_root / "NOTICE.md")
        shutil.copy2(CONFIGURE_EFFORT_WRAPPER, fixture_wrapper)

        return fixture_root

    def test_repository_verifier_rejects_missing_distributable_notices(self):
        for filename in ("LICENSE", "NOTICE.md"):
            with self.subTest(filename=filename), tempfile.TemporaryDirectory() as directory:
                fixture_root = self.make_package_fixture(directory)
                fixture_plugin = fixture_root / "plugins/astral-orchestrator"
                (fixture_plugin / filename).unlink()

                result = subprocess.run(
                    ["sh", str(fixture_plugin / "scripts/verify.sh")],
                    cwd=fixture_root,
                    check=False,
                    capture_output=True,
                    text=True,
                )

                self.assertNotEqual(result.returncode, 0)
                self.assertIn(f"required distributable notice is missing: {filename}", result.stderr)

    def test_repository_verifier_rejects_changed_distributable_notices(self):
        for filename in ("LICENSE", "NOTICE.md"):
            with self.subTest(filename=filename), tempfile.TemporaryDirectory() as directory:
                fixture_root = self.make_package_fixture(directory)
                fixture_plugin = fixture_root / "plugins/astral-orchestrator"
                copy = fixture_plugin / filename
                copy.write_bytes(copy.read_bytes() + b"\nchanged by test fixture\n")

                result = subprocess.run(
                    ["sh", str(fixture_plugin / "scripts/verify.sh")],
                    cwd=fixture_root,
                    check=False,
                    capture_output=True,
                    text=True,
                )

                self.assertNotEqual(result.returncode, 0)
                self.assertIn(
                    f"distributable notice differs from repository root: {filename}",
                    result.stderr,
                )

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
        self.assertIn("Astral Orchestrator verification passed", result.stdout)


if __name__ == "__main__":
    unittest.main()
