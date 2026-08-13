import importlib.util
import hashlib
import io
import json
import os
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
PORTABLE_MANIFEST = PLUGIN / "plugin.json"
PORTABILITY = ROOT / "docs/PORTABILITY.md"
OPENAI_METADATA = PLUGIN / "skills/astral-orchestrator/agents/openai.yaml"
BANNER = ROOT / "assets/brand/astral-orchestrator-banner.gif"
SKILL = PLUGIN / "skills/astral-orchestrator/SKILL.md"
MODES = PLUGIN / "skills/astral-orchestrator/references/modes-and-risk.md"
TEMPLATES = PLUGIN / "skills/astral-orchestrator/references/work-templates.md"
ROUTING = PLUGIN / "skills/astral-orchestrator/references/routing-and-preflight.md"
MORPH = PLUGIN / "skills/astral-orchestrator/references/morph-mode.md"
CONSTELLATION = PLUGIN / "skills/astral-orchestrator/references/constellation-mode.md"
MEASURED = PLUGIN / "skills/astral-orchestrator/references/measured-mode.md"
AGENTS = PLUGIN / "agents"
INSTALL_AGENTS = PLUGIN / "scripts/install-agents.sh"
INSPECT_RUNTIME = PLUGIN / "scripts/inspect-agent-runtime.sh"
CHECK_PRIMARY = PLUGIN / "scripts/check-primary.py"
RUN_AGENT = PLUGIN / "scripts/run-agent.py"
RUN_MORPH_AGENT = PLUGIN / "scripts/run-morph-agent.py"
CODEX_RUNTIME = PLUGIN / "scripts/codex_runtime.py"
CONFIGURE_EFFORT = PLUGIN / "scripts/configure-effort.py"
EFFORT_SETTINGS = PLUGIN / "scripts/effort_settings.py"
CONFIGURE_EFFORT_WRAPPER = ROOT / "scripts/configure-effort.sh"
BENCHMARK_SCORECARD = PLUGIN / "scripts/benchmark-scorecard.py"
BENCHMARK_GUIDE = ROOT / "benchmarks/README.md"
CONTEXT_FOOTPRINT = ROOT / "benchmarks/context-footprint-2026-08-03.json"
CONTEXT_FOOTPRINT_MEASURED = ROOT / "benchmarks/context-footprint-2026-08-04.json"
CONTEXT_FOOTPRINT_MEASURER = ROOT / "benchmarks/measure_instruction_context.py"
ROUTING_DIAGRAM = ROOT / "assets/diagrams/routing-and-verification.svg"
ROUTING_EXCALIDRAW = ROOT / "assets/diagrams/routing-and-verification.excalidraw"
SCORECARD_DIAGRAM = ROOT / "assets/diagrams/outcome-scorecard.svg"
SCORECARD_EXCALIDRAW = ROOT / "assets/diagrams/outcome-scorecard.excalidraw"
SPEC = ROOT / "docs/SPEC.md"
RELEASE_SKILL = ROOT / "skills/track-astral-releases/SKILL.md"
RELEASE_SKILL_METADATA = ROOT / "skills/track-astral-releases/agents/openai.yaml"
RELEASE_SURFACES = ROOT / "skills/track-astral-releases/references/release-surfaces.md"
RELEASE_LEDGER_SCRIPT = ROOT / "skills/track-astral-releases/scripts/release-ledger.py"
RELEASE_LEDGER = ROOT / "release/astral-release-ledger.json"
CANONICAL_IMPROVEMENTS_URL = (
    "https://github.com/Demonbane18/astral-orchestrator/blob/main/docs/IMPROVEMENTS.md"
)


def read(path: Path) -> str:
    if not path.is_file():
        raise AssertionError(f"required file is missing: {path.relative_to(ROOT)}")
    return path.read_text(encoding="utf-8")


def load_json(path: Path):
    return json.loads(read(path))


def make_fake_codex_runtime(
    root: Path, name: str = "codex", *, compatible: bool = True
) -> Path:
    runtime = root / name
    feature_exit = 0 if compatible else 42
    runtime.write_text(
        "#!/bin/sh\n"
        f"if [ \"$1 $2\" = \"features list\" ]; then exit {feature_exit}; fi\n"
        "if [ \"$1\" = \"--version\" ]; then echo 'codex-cli 99.0-test'; exit 0; fi\n"
        "exit 97\n",
        encoding="utf-8",
    )
    runtime.chmod(0o700)
    return runtime


def load_script(name: str, path: Path):
    specification = importlib.util.spec_from_file_location(name, path)
    if specification is None or specification.loader is None:
        raise AssertionError(f"could not load script: {path}")
    module = importlib.util.module_from_spec(specification)
    sys.modules[name] = module
    try:
        specification.loader.exec_module(module)
    except BaseException:
        sys.modules.pop(name, None)
        raise
    return module


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
        self.assertEqual(manifest["version"], "3.3.1")
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
        self.assertTrue(read(SPEC).startswith("# Spec: Astral Orchestrator v3.3"))

        interface = manifest["interface"]
        self.assertEqual(interface["composerIcon"], "./skills/astral-orchestrator/assets/icon.png")
        self.assertEqual(interface["logo"], "./skills/astral-orchestrator/assets/icon.png")
        description = interface["longDescription"].lower()
        for mode in ("quick", "guided", "careful", "measured", "morph", "constellation"):
            self.assertIn(mode, description)
        self.assertIn("opt-in", description)
        self.assertIn("never runs automatically", description)
        self.assertNotIn("slower", description)

        prompts = interface["defaultPrompt"]
        self.assertGreaterEqual(len(prompts), 2)
        self.assertLessEqual(len(prompts), 3)
        self.assertTrue(all(len(prompt) <= 128 for prompt in prompts))
        prompt_text = " ".join(prompts).lower()
        for mode in ("quick", "guided", "careful", "measured", "morph", "constellation"):
            self.assertIn(mode, prompt_text)

    def test_portable_manifest_uses_agent_plugins_v1_fixed_skill_discovery(self):
        manifest = load_json(PORTABLE_MANIFEST)

        self.assertEqual(
            manifest["$schema"],
            "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json",
        )
        self.assertEqual(manifest["name"], "astral-orchestrator")
        self.assertEqual(manifest["version"], "3.3.1")
        self.assertEqual(manifest["license"], "MIT")
        self.assertEqual(
            set(manifest),
            {
                "$schema",
                "name",
                "version",
                "description",
                "author",
                "homepage",
                "repository",
                "license",
                "keywords",
            },
        )
        self.assertNotIn("skills", manifest)
        self.assertNotIn("interface", manifest)

        plugin_root = PLUGIN.resolve()
        discovered = PLUGIN / "skills/astral-orchestrator/SKILL.md"
        self.assertTrue(discovered.is_file())
        self.assertEqual(discovered.resolve().parents[2], plugin_root)

    def test_portability_docs_limit_non_codex_routes_to_observed_capabilities(self):
        portability = " ".join(read(PORTABILITY).lower().split())
        skill = " ".join(read(SKILL).lower().split())
        portable_hosts = " ".join(read(PLUGIN / "skills/astral-orchestrator/references/portable-hosts.md").lower().split())
        readme = read(ROOT / "README.md").lower()

        for required in (
            "skills and mcp discovery only",
            "not agents, concurrency, model selection, or reasoning effort",
            "vs code",
            "cursor",
            "github copilot",
            "chatgpt/codex",
            "kiro",
            "component types incrementally",
            "https://agent-plugins.org/specification",
            "https://agent-plugins.org/compatible-clients",
        ):
            self.assertIn(required, portability)
        for required in (
            "whether the host is codex",
            "portable-hosts.md",
            "observable host capabilities",
            "never claim sol/luna/terra unless observed",
        ):
            self.assertIn(required, skill)
        self.assertIn("reserve and count the primary as one occupied slot", portable_hosts)
        self.assertIn("regardless of whether the host advertises it", portable_hosts)
        for forbidden in (
            "agent plugins",
            "agent-plugins.org",
            "portable manifest",
            "compatible clients",
            "cross-client",
        ):
            self.assertNotIn(forbidden, readme)

    def test_readme_safety_qualifies_external_morph_packet_processing(self):
        readme = " ".join(read(ROOT / "README.md").lower().split())

        self.assertIn("fixed local codex routes", readme)
        self.assertIn("external morph provider can receive its bounded worker packet", readme)
        self.assertNotIn("work packets remain local", readme)

    def test_openai_metadata_keeps_shared_icon_and_six_mode_aware_prompt(self):
        metadata = read(OPENAI_METADATA)

        self.assertIn('icon_small: "./assets/icon.png"', metadata)
        self.assertIn('icon_large: "./assets/icon.png"', metadata)
        prompt_line = next(
            line for line in metadata.splitlines() if line.strip().startswith("default_prompt:")
        )
        prompt = prompt_line.split(":", 1)[1].strip().strip('"')
        self.assertLessEqual(len(prompt), 128)
        for mode in ("guided", "quick", "careful", "measured", "morph", "constellation"):
            self.assertIn(mode, prompt.lower())


class SkillContractTests(unittest.TestCase):
    def test_live_route_panel_keeps_astral_and_lane_evidence_visible(self):
        skill = " ".join(read(SKILL).lower().split())
        routing = " ".join(read(ROUTING).lower().split())
        templates = read(TEMPLATES).lower()

        for required in (
            "astral status",
            "every progress update",
            "requested",
            "observed",
            "model",
            "effort",
            "running",
        ):
            self.assertIn(required, skill)
        for required in (
            "do not label a lane observed",
            "runtime evidence",
            "state changes",
            "long-running",
            "never include prompts",
            "secrets",
        ):
            self.assertIn(required, routing)
        for required in (
            "astral status",
            "lane | role | model | effort | state | evidence",
            "sol primary",
            "fresh reviewer",
            "morph worker",
            "use `planned`",
            "not yet required",
            "requested: <configured effort>",
        ):
            self.assertIn(required, templates)
        self.assertNotIn("use `not needed` or `not yet required`", templates)

        declared_section = routing.split(
            "use states that describe what the host has actually shown:", 1
        )[1].split("`requested` means", 1)[0]
        declared_states = set(re.findall(r"`([^`]+)`", declared_section))
        status_block = templates.split("```text", 1)[1].split("```", 1)[0]
        panel_rows = [
            line for line in status_block.splitlines()
            if line.startswith(("sol primary |", "worker <card> |", "fresh reviewer |"))
        ]
        self.assertEqual(len(panel_rows), 3)
        for row in panel_rows:
            template_states = set(row.split("|")[4].strip().strip("<>").split("/"))
            self.assertEqual(template_states, declared_states)

    def test_readme_has_copy_ready_mode_prompts_and_constellation_route_answer(self):
        readme = " ".join(read(ROOT / "README.md").lower().split())

        self.assertIn("sample prompts for every mode", readme)
        for mode in ("quick", "guided", "careful", "measured", "morph", "constellation"):
            self.assertRegex(readme, rf"{mode}[^.]*use astral orchestrator")
        for required in (
            "sol high is sufficient",
            "sol ultra is not required",
            "custom worker model and effort",
            "available concurrency",
            "non-overlapping ownership",
        ):
            self.assertIn(required, readme)

    def test_constellation_documents_default_sol_high_and_custom_worker_routes(self):
        constellation = " ".join(read(CONSTELLATION).lower().split())

        for required in (
            "sol high is sufficient",
            "sol ultra is not required",
            "custom worker model and effort",
            "morph",
            "runtime evidence",
            "available slots",
            "successful morph dry run before launch",
            "launch that same route",
            "matching runtime evidence after startup and before accepting",
        ):
            self.assertIn(required, constellation)
        self.assertNotIn("runtime evidence before launch", constellation)

    def test_skill_uses_six_plain_language_modes_and_loads_opt_in_references_on_demand(self):
        skill = read(SKILL)
        modes = read(MODES)

        for mode in ("Quick", "Guided", "Careful", "Measured", "Morph", "Constellation"):
            self.assertIn(mode, skill)
            self.assertIn(mode, modes)
        self.assertRegex(skill, r"Guided[^\n]*(default|Default)")
        self.assertIn("when the user explicitly names morph", skill.lower())
        self.assertIn("when the user explicitly names constellation", skill.lower())
        self.assertTrue(MORPH.is_file())
        self.assertTrue(CONSTELLATION.is_file())

        morph = " ".join(read(MORPH).lower().split())
        constellation = read(CONSTELLATION).lower()
        for required in (
            "explicit opt-in",
            "opencodex is optional",
            "never modifies ~/.opencodex",
            "provider/model",
            "requested effort",
            "upstream-native effort",
            "fresh sol reviewer",
            "after the process exits",
            "remove only that exact private packet",
            "external or non-openai provider",
            "worker packet as part of",
            "does not mean provider traffic or model inference is local",
        ):
            self.assertIn(required, morph)
        for required in (
            "explicit opt-in",
            "first wave concurrently",
            "available slots",
            "primary consumes one slot",
            "non-overlapping",
            "serial guided-style routing",
            "do not spawn extra sol implementers",
            "fresh sol reviewer",
        ):
            self.assertIn(required, constellation)

    def test_measured_state_sequence_templates_and_safe_state_are_explicit(self):
        measured = " ".join(read(MEASURED).lower().split())

        for required in (
            "prepare (unpersisted)",
            "one or more numbered execution attempts",
            "each in the order `implementation`, `verification`, `review`",
            "increment the attempt number",
            "complete is allowed only after a `ship` verdict",
            "`rethink` does not mutate the frozen card",
            "current attempt's first unfinished phase",
            "before any writes",
            "before recording `freeze started`",
            "first unfinished base phase",
            "id -u",
            "empty or non-decimal result",
            "canonical temp root",
            "/tmp/astral-orchestrator-measured-<effective-uid>",
            "exactly one luna probe and one terra probe",
            "identical frozen card",
            "owner-only parent directory",
            "symlink parents",
            "personal or regulated data",
            "no-follow",
            "atomic",
            "measured planning probe",
            "measured ledger entry",
            "not hard sandbox isolation",
        ):
            self.assertIn(required, measured)

        self.assertNotIn("Measured planning probe", read(TEMPLATES))
        self.assertNotIn("Measured ledger entry", read(TEMPLATES))

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
        self.assertIn("exact pinned sol", routing)
        self.assertIn("observed read-only access", routing)

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

            rollout.write_text(
                rollout.read_text(encoding="utf-8").replace(
                    '"agent_nickname": "Atlas"',
                    '"agent_nickname": "Conflict"',
                    1,
                ),
                encoding="utf-8",
            )
            conflicting = subprocess.run(
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
            self.assertNotEqual(conflicting.returncode, 0)
            self.assertIn("ambiguous", conflicting.stderr)

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

    def test_primary_checker_uses_the_bundled_inspector_and_never_leaks_rollout_contents(self):
        thread_id = "12345678-1234-1234-1234-123456789abc"
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            sessions = root / "sessions"
            sessions.mkdir()
            rollout = sessions / f"rollout-primary-{thread_id}.jsonl"
            rollout.write_text(
                "\n".join(
                    (
                        json.dumps(
                            {
                                "type": "session_meta",
                                "payload": {
                                    "id": thread_id,
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
                    )
                )
                + "\n",
                encoding="utf-8",
            )

            matched = subprocess.run(
                [
                    "python3",
                    str(CHECK_PRIMARY),
                    "--thread-id",
                    thread_id,
                    "--sessions-dir",
                    str(sessions),
                    "--settings-file",
                    str(root / "missing-effort-levels.toml"),
                ],
                cwd=ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(matched.returncode, 0, matched.stdout + matched.stderr)
            evidence = json.loads(matched.stdout)
            self.assertEqual(evidence["status"], "match")
            self.assertEqual(evidence["expected_model"], "gpt-5.6-sol")
            self.assertEqual(evidence["expected_effort"], "high")
            self.assertEqual(evidence["observed_model"], "gpt-5.6-sol")
            self.assertEqual(evidence["observed_effort"], "high")
            self.assertEqual(evidence["thread_id"], thread_id)
            self.assertNotIn("secret", matched.stdout)
            self.assertNotIn("prompt", matched.stdout)

            rollout.write_text(
                rollout.read_text(encoding="utf-8").replace('"high"', '"low"'),
                encoding="utf-8",
            )
            mismatched = subprocess.run(
                [
                    "python3",
                    str(CHECK_PRIMARY),
                    "--thread-id",
                    thread_id,
                    "--sessions-dir",
                    str(sessions),
                    "--settings-file",
                    str(root / "missing-effort-levels.toml"),
                ],
                cwd=ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertNotEqual(mismatched.returncode, 0)
            self.assertEqual(json.loads(mismatched.stdout)["status"], "mismatch")

            unavailable = subprocess.run(
                [
                    "python3",
                    str(CHECK_PRIMARY),
                    "--settings-file",
                    str(root / "missing-effort-levels.toml"),
                ],
                cwd=ROOT,
                env={key: value for key, value in os.environ.items() if key != "CODEX_THREAD_ID"},
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertNotEqual(unavailable.returncode, 0)
            self.assertEqual(json.loads(unavailable.stdout)["status"], "unavailable")

    def test_primary_checker_fails_closed_for_invalid_evidence_and_settings(self):
        thread_id = "abcdefab-cdef-cdef-cdef-abcdefabcdef"
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            sessions = root / "sessions"
            sessions.mkdir()
            rollout = sessions / f"rollout-primary-{thread_id}.jsonl"
            rollout.write_text(
                "\n".join(
                    (
                        json.dumps(
                            {
                                "type": "session_meta",
                                "payload": {
                                    "id": thread_id,
                                    "agent_nickname": "Primary",
                                    "secret": "must-not-leak",
                                },
                            }
                        ),
                        json.dumps(
                            {
                                "type": "session_meta",
                                "payload": {
                                    "id": thread_id,
                                    "agent_nickname": "Conflicting metadata",
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
                    )
                )
                + "\n",
                encoding="utf-8",
            )

            def check(settings: Path) -> subprocess.CompletedProcess[str]:
                return subprocess.run(
                    [
                        "python3",
                        str(CHECK_PRIMARY),
                        "--thread-id",
                        thread_id,
                        "--sessions-dir",
                        str(sessions),
                        "--settings-file",
                        str(settings),
                    ],
                    cwd=ROOT,
                    check=False,
                    capture_output=True,
                    text=True,
                )

            conflicting = check(root / "missing-effort-levels.toml")
            self.assertNotEqual(conflicting.returncode, 0)
            conflicting_evidence = json.loads(conflicting.stdout)
            self.assertEqual(conflicting_evidence["status"], "invalid")
            self.assertNotIn("secret", conflicting.stdout)
            self.assertNotIn("prompt", conflicting.stdout)
            self.assertLessEqual(
                set(conflicting_evidence),
                {
                    "expected_effort",
                    "expected_model",
                    "observed_effort",
                    "observed_model",
                    "reason",
                    "status",
                    "thread_id",
                },
            )

            duplicate_filename = sessions / f"rollout-copy-{thread_id}.jsonl"
            duplicate_filename.write_bytes(rollout.read_bytes())
            ambiguous = check(root / "missing-effort-levels.toml")
            self.assertNotEqual(ambiguous.returncode, 0)
            self.assertEqual(json.loads(ambiguous.stdout)["status"], "invalid")
            duplicate_filename.unlink()

            malformed_settings = root / "effort-levels.toml"
            malformed_settings.write_text("[effort\norchestrator = \"high\"\n", encoding="utf-8")
            malformed = check(malformed_settings)
            self.assertNotEqual(malformed.returncode, 0)
            self.assertEqual(json.loads(malformed.stdout)["status"], "invalid")

            rollout.unlink()
            missing_rollout = check(root / "missing-effort-levels.toml")
            self.assertNotEqual(missing_rollout.returncode, 0)
            self.assertEqual(json.loads(missing_rollout.stdout)["status"], "unavailable")

    def test_primary_checker_marks_malformed_or_invalid_inspector_evidence_invalid(self):
        spec = importlib.util.spec_from_file_location(
            "astral_orchestrator_check_primary", CHECK_PRIMARY
        )
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader)
        checker = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(checker)

        thread_id = "12345678-1234-1234-1234-123456789abc"
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            rollout = root / f"rollout-primary-{thread_id}.jsonl"
            rollout.write_text("{}\n", encoding="utf-8")

            for stdout in (
                "not-json",
                json.dumps([]),
                json.dumps(
                    {
                        "thread_id": thread_id,
                        "model": "invalid model id",
                        "effort": "high",
                    }
                ),
            ):
                output = io.StringIO()
                with (
                    mock.patch.object(
                        sys,
                        "argv",
                        [
                            str(CHECK_PRIMARY),
                            "--thread-id",
                            thread_id,
                            "--settings-file",
                            str(root / "missing-effort-levels.toml"),
                        ],
                    ),
                    mock.patch.object(checker, "find_rollouts", return_value=[rollout]),
                    mock.patch.object(
                        checker.subprocess,
                        "run",
                        return_value=subprocess.CompletedProcess([], 0, stdout, ""),
                    ),
                    redirect_stdout(output),
                ):
                    self.assertEqual(checker.main(), 1)
                evidence = json.loads(output.getvalue())
                self.assertEqual(evidence["status"], "invalid")
                self.assertEqual(evidence["reason"], "runtime-evidence-invalid")

    def test_primary_checker_distinguishes_missing_from_malformed_thread_ids(self):
        spec = importlib.util.spec_from_file_location(
            "astral_orchestrator_check_primary_thread_id", CHECK_PRIMARY
        )
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader)
        checker = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(checker)

        with tempfile.TemporaryDirectory() as directory:
            settings = Path(directory) / "missing-effort-levels.toml"

            def invoke(arguments: list[str], environment: dict[str, str]):
                output = io.StringIO()
                with (
                    mock.patch.object(sys, "argv", [str(CHECK_PRIMARY), *arguments]),
                    mock.patch.dict(os.environ, environment, clear=True),
                    redirect_stdout(output),
                ):
                    self.assertEqual(checker.main(), 1)
                return json.loads(output.getvalue())

            missing = invoke(["--settings-file", str(settings)], {})
            malformed_environment = invoke(
                ["--settings-file", str(settings)],
                {"CODEX_THREAD_ID": "not-a-uuid"},
            )
            malformed_argument = invoke(
                [
                    "--thread-id",
                    "also-not-a-uuid",
                    "--settings-file",
                    str(settings),
                ],
                {},
            )

        self.assertEqual(
            (missing["status"], missing["reason"]),
            ("unavailable", "thread-id-unavailable"),
        )
        self.assertEqual(
            (malformed_environment["status"], malformed_environment["reason"]),
            ("invalid", "thread-id-invalid"),
        )
        self.assertEqual(
            (malformed_argument["status"], malformed_argument["reason"]),
            ("invalid", "thread-id-invalid"),
        )

    def test_morph_launcher_validates_private_packets_and_marks_effort_as_requested_only(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            codex_runtime = make_fake_codex_runtime(root)
            workdir = root / "work"
            workdir.mkdir()
            prompt = root / "packet.txt"
            prompt.write_text("private Morph work card\n", encoding="utf-8")
            prompt.chmod(0o600)

            result = subprocess.run(
                [
                    "python3",
                    str(RUN_MORPH_AGENT),
                    "--model",
                    "opencodex/worker-model",
                    "--effort",
                    "xhigh",
                    "--workdir",
                    str(workdir),
                    "--prompt-file",
                    str(prompt),
                    "--dry-run",
                ],
                cwd=ROOT,
                check=False,
                capture_output=True,
                text=True,
                env={**os.environ, "ASTRAL_CODEX_PATH": str(codex_runtime)},
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            evidence = json.loads(result.stdout)
            self.assertEqual(evidence["route"], "morph")
            self.assertEqual(evidence["model"], "opencodex/worker-model")
            self.assertEqual(evidence["requested_effort"], "xhigh")
            self.assertEqual(evidence["verified_upstream_native_effort"], "unverified")
            self.assertEqual(evidence["effort_semantics"], "requested-only")
            self.assertEqual(evidence["sandbox"], "workspace-write")
            self.assertNotIn("private Morph work card", result.stdout)

            invalid_model = subprocess.run(
                [
                    "python3",
                    str(RUN_MORPH_AGENT),
                    "--model",
                    "bad model id",
                    "--effort",
                    "high",
                    "--workdir",
                    str(workdir),
                    "--prompt-file",
                    str(prompt),
                    "--dry-run",
                ],
                cwd=ROOT,
                check=False,
                capture_output=True,
                text=True,
                env={**os.environ, "ASTRAL_CODEX_PATH": str(codex_runtime)},
            )
            self.assertNotEqual(invalid_model.returncode, 0)
            self.assertIn("model", invalid_model.stderr.lower())

    def test_morph_launcher_constructs_the_explicit_workspace_write_codex_route(self):
        spec = importlib.util.spec_from_file_location(
            "astral_orchestrator_run_morph_agent", RUN_MORPH_AGENT
        )
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader)
        launcher = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(launcher)

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            workdir = root / "work"
            workdir.mkdir()
            prompt = root / "packet.txt"
            prompt_text = "private Morph card\n"
            prompt.write_text(prompt_text, encoding="utf-8")
            prompt.chmod(0o600)
            captured = {}

            def fake_run(command, *, input, check):
                captured["command"] = command
                captured["input"] = input
                captured["check"] = check
                return subprocess.CompletedProcess(command, 17)

            output = io.StringIO()
            argv = [
                str(RUN_MORPH_AGENT),
                "--model",
                "opencodex/worker-model",
                "--effort",
                "medium",
                "--workdir",
                str(workdir),
                "--prompt-file",
                str(prompt),
            ]
            with (
                mock.patch.object(sys, "argv", argv),
                mock.patch.object(
                    launcher,
                    "resolve_codex_runtime",
                    return_value=mock.Mock(
                        path="/test/codex",
                        source="host-runtime",
                        version="codex-cli test",
                        config_probe="pass",
                    ),
                ),
                mock.patch.object(launcher.subprocess, "run", side_effect=fake_run),
                redirect_stdout(output),
            ):
                return_code = launcher.main()

            command = captured["command"]
            config_overrides = [
                command[index + 1]
                for index, value in enumerate(command)
                if value == "-c"
            ]
            self.assertEqual(return_code, 17)
            self.assertEqual(captured["input"], prompt_text.encode())
            self.assertFalse(captured["check"])
            self.assertEqual(command[:2], ["/test/codex", "exec"])
            self.assertEqual(command[command.index("--model") + 1], "opencodex/worker-model")
            self.assertEqual(command[command.index("--sandbox") + 1], "workspace-write")
            self.assertEqual(command[command.index("--cd") + 1], str(workdir.resolve()))
            self.assertEqual(command[-1], "-")
            self.assertIn('model_reasoning_effort="medium"', config_overrides)
            self.assertIn(
                f"developer_instructions={json.dumps(launcher.MORPH_DEVELOPER_INSTRUCTIONS)}",
                config_overrides,
            )
            self.assertIn("must not spawn or delegate", launcher.MORPH_DEVELOPER_INSTRUCTIONS)
            route_header = output.getvalue()
            self.assertIn("ASTRAL_ORCHESTRATOR_ROUTE ", route_header)
            self.assertNotIn(prompt_text.strip(), route_header)

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
            codex_runtime = make_fake_codex_runtime(Path(directory))
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
                    env={**os.environ, "ASTRAL_CODEX_PATH": str(codex_runtime)},
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
                    mock.patch.object(
                        launcher,
                        "resolve_codex_runtime",
                        return_value=mock.Mock(
                            path="/test/codex",
                            source="host-runtime",
                            version="codex-cli test",
                            config_probe="pass",
                        ),
                    ),
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
                mock.patch.object(launcher, "resolve_codex_runtime") as find_codex,
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
            codex_runtime = make_fake_codex_runtime(root)
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
                    env={**os.environ, "ASTRAL_CODEX_PATH": str(codex_runtime)},
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


class CodexRuntimeResolutionTests(unittest.TestCase):
    def load_runtime(self):
        return load_script("astral_orchestrator_codex_runtime_tests", CODEX_RUNTIME)

    def test_incompatible_path_runtime_is_skipped_for_compatible_host_runtime(self):
        runtime = self.load_runtime()

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path_runtime = make_fake_codex_runtime(root, "path-codex")
            app_runtime = make_fake_codex_runtime(root, "app-codex")
            calls = []

            def runner(command, **kwargs):
                calls.append((command, kwargs))
                if command[1:] == ["features", "list"]:
                    if command[0] == str(path_runtime.resolve()):
                        return subprocess.CompletedProcess(
                            command,
                            1,
                            "",
                            "unknown variant audio from private catalog",
                        )
                    return subprocess.CompletedProcess(command, 0, "features", "")
                if command[1:] == ["--version"]:
                    return subprocess.CompletedProcess(
                        command, 0, "codex-cli 0.147.0-alpha.6.5\n", ""
                    )
                self.fail(f"unexpected inference command: {command}")

            candidates = [
                runtime.RuntimeCandidate("path", str(path_runtime)),
                runtime.RuntimeCandidate("chatgpt-app", str(app_runtime)),
            ]
            with mock.patch.object(
                runtime, "runtime_candidates", return_value=candidates
            ):
                selected = runtime.resolve_codex_runtime(runner=runner)

        self.assertEqual(selected.path, str(app_runtime.resolve()))
        self.assertEqual(selected.source, "chatgpt-app")
        self.assertEqual(selected.version, "codex-cli 0.147.0-alpha.6.5")
        self.assertEqual(selected.config_probe, "pass")
        self.assertEqual(
            [command[1:] for command, _ in calls],
            [["features", "list"], ["features", "list"], ["--version"]],
        )
        for command, kwargs in calls:
            self.assertNotIn("exec", command)
            self.assertTrue(kwargs["capture_output"])
            self.assertTrue(kwargs["text"])

    def test_invalid_hinted_paths_are_rejected_without_being_executed(self):
        runtime = self.load_runtime()

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            fallback = make_fake_codex_runtime(root, "fallback-codex")
            non_executable = root / "non-executable-codex"
            non_executable.write_text("not executable\n", encoding="utf-8")
            non_executable.chmod(0o600)
            directory_candidate = root / "codex-directory"
            directory_candidate.mkdir()
            unicode_control = make_fake_codex_runtime(
                root, "codex-\u0085-control"
            )
            invalid_paths = {
                "missing": root / "missing-codex",
                "non-executable": non_executable,
                "directory": directory_candidate,
                "control-character": f"{root}/codex\nsecret",
                "unicode-control-character": unicode_control,
            }

            for label, invalid_path in invalid_paths.items():
                with self.subTest(label=label):
                    calls = []

                    def runner(command, **kwargs):
                        calls.append(command)
                        if command[1:] == ["features", "list"]:
                            return subprocess.CompletedProcess(command, 0, "", "")
                        if command[1:] == ["--version"]:
                            return subprocess.CompletedProcess(
                                command, 0, "codex-cli test\n", ""
                            )
                        self.fail(f"unexpected inference command: {command}")

                    candidates = [
                        runtime.RuntimeCandidate("astral-override", str(invalid_path)),
                        runtime.RuntimeCandidate("path", str(fallback)),
                    ]
                    with mock.patch.object(
                        runtime, "runtime_candidates", return_value=candidates
                    ):
                        selected = runtime.resolve_codex_runtime(runner=runner)

                    self.assertEqual(selected.path, str(fallback.resolve()))
                    self.assertEqual(selected.source, "path")
                    self.assertEqual(
                        calls,
                        [
                            [str(fallback.resolve()), "features", "list"],
                            [str(fallback.resolve()), "--version"],
                        ],
                    )

    def test_duplicate_resolved_paths_are_probed_only_once(self):
        runtime = self.load_runtime()

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            duplicate = make_fake_codex_runtime(root, "duplicate-codex")
            fallback = make_fake_codex_runtime(root, "fallback-codex")
            feature_calls = []

            def runner(command, **kwargs):
                if command[1:] == ["features", "list"]:
                    feature_calls.append(command[0])
                    return subprocess.CompletedProcess(
                        command,
                        0 if command[0] == str(fallback.resolve()) else 1,
                        "",
                        "",
                    )
                return subprocess.CompletedProcess(command, 0, "codex-cli test\n", "")

            candidates = [
                runtime.RuntimeCandidate("astral-override", str(duplicate)),
                runtime.RuntimeCandidate("host-runtime", str(duplicate)),
                runtime.RuntimeCandidate("path", str(fallback)),
            ]
            with mock.patch.object(
                runtime, "runtime_candidates", return_value=candidates
            ):
                selected = runtime.resolve_codex_runtime(runner=runner)

        self.assertEqual(selected.source, "path")
        self.assertEqual(
            feature_calls,
            [str(duplicate.resolve()), str(fallback.resolve())],
        )

    def test_all_failed_probes_fail_closed_without_leaking_output_or_inferring(self):
        runtime = self.load_runtime()

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            first = make_fake_codex_runtime(root, "first-codex")
            second = make_fake_codex_runtime(root, "second-codex")
            calls = []
            packet_secret = "PRIVATE_WORKER_PACKET_DO_NOT_PRINT"
            config_secret = "provider_api_key=CONFIG_SECRET_DO_NOT_PRINT"

            def runner(command, **kwargs):
                calls.append(command)
                return subprocess.CompletedProcess(
                    command,
                    1,
                    f"catalog contained {config_secret}",
                    f"parse failed near {packet_secret}",
                )

            candidates = [
                runtime.RuntimeCandidate("host-runtime", str(first)),
                runtime.RuntimeCandidate("path", str(second)),
            ]
            with mock.patch.object(
                runtime, "runtime_candidates", return_value=candidates
            ):
                with self.assertRaises(runtime.RuntimeResolutionError) as raised:
                    runtime.resolve_codex_runtime(runner=runner)

        message = str(raised.exception)
        self.assertIn("host-runtime", message)
        self.assertIn("path", message)
        self.assertNotIn(config_secret, message)
        self.assertNotIn(packet_secret, message)
        self.assertEqual(
            calls,
            [
                [str(first.resolve()), "features", "list"],
                [str(second.resolve()), "features", "list"],
            ],
        )
        self.assertTrue(all("exec" not in command for command in calls))

    def test_probe_timeout_fails_closed(self):
        runtime = self.load_runtime()

        with tempfile.TemporaryDirectory() as directory:
            candidate = make_fake_codex_runtime(Path(directory))
            calls = []

            def runner(command, **kwargs):
                calls.append((command, kwargs))
                raise subprocess.TimeoutExpired(command, kwargs["timeout"])

            with mock.patch.object(
                runtime,
                "runtime_candidates",
                return_value=[runtime.RuntimeCandidate("path", str(candidate))],
            ):
                with self.assertRaises(runtime.RuntimeResolutionError) as raised:
                    runtime.resolve_codex_runtime(runner=runner, timeout=0.25)

        self.assertIn("path", str(raised.exception))
        self.assertIn("timeout", str(raised.exception).lower())
        self.assertEqual(len(calls), 1)
        self.assertEqual(calls[0][0][1:], ["features", "list"])
        self.assertEqual(calls[0][1]["timeout"], 0.25)

    def test_morph_dry_run_uses_real_probes_for_mismatch_and_all_fail_fixtures(self):
        runtime = load_script("codex_runtime", CODEX_RUNTIME)
        launcher = load_script(
            "astral_orchestrator_run_morph_fixture_test", RUN_MORPH_AGENT
        )

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            incompatible = make_fake_codex_runtime(
                root, "path-codex", compatible=False
            )
            compatible = make_fake_codex_runtime(root, "host-codex")
            workdir = root / "work"
            workdir.mkdir()
            prompt = root / "packet.txt"
            packet = "PRIVATE_FIXTURE_PACKET"
            prompt.write_text(packet, encoding="utf-8")
            prompt.chmod(0o600)
            argv = [
                str(RUN_MORPH_AGENT),
                "--model",
                "opencodex/worker-model",
                "--effort",
                "high",
                "--workdir",
                str(workdir),
                "--prompt-file",
                str(prompt),
                "--dry-run",
            ]

            mismatch = [
                runtime.RuntimeCandidate("path", str(incompatible)),
                runtime.RuntimeCandidate("host-runtime", str(compatible)),
            ]
            output = io.StringIO()
            with (
                mock.patch.object(sys, "argv", argv),
                mock.patch.object(
                    runtime, "runtime_candidates", return_value=mismatch
                ),
                redirect_stdout(output),
            ):
                self.assertEqual(launcher.main(), 0)

            evidence = json.loads(output.getvalue())
            self.assertEqual(evidence["codex_runtime_source"], "host-runtime")
            self.assertEqual(evidence["codex_config_probe"], "pass")
            self.assertNotIn(packet, output.getvalue())

            errors = io.StringIO()
            with (
                mock.patch.object(sys, "argv", argv),
                mock.patch.object(
                    runtime,
                    "runtime_candidates",
                    return_value=[
                        runtime.RuntimeCandidate("path", str(incompatible))
                    ],
                ),
                redirect_stderr(errors),
            ):
                with self.assertRaises(SystemExit) as raised:
                    launcher.main()

            self.assertEqual(raised.exception.code, 1)
            self.assertIn("no compatible Codex runtime", errors.getvalue())
            self.assertNotIn(packet, errors.getvalue())

    def test_candidate_generation_is_ordered_and_cross_platform(self):
        runtime = self.load_runtime()

        darwin = runtime.runtime_candidates(
            platform_name="Darwin",
            environ={
                "ASTRAL_CODEX_PATH": "/override/codex",
                "CODEX_CLI_PATH": "/host/codex",
            },
            home=Path("/Users/tester"),
            which=lambda _: "/path/codex",
        )
        self.assertEqual(
            [(candidate.source, candidate.path) for candidate in darwin],
            [
                ("astral-override", "/override/codex"),
                ("host-runtime", "/host/codex"),
                ("chatgpt-app", "/Applications/ChatGPT.app/Contents/Resources/codex"),
                ("codex-app", "/Applications/Codex.app/Contents/Resources/codex"),
                (
                    "chatgpt-app",
                    "/Users/tester/Applications/ChatGPT.app/Contents/Resources/codex",
                ),
                (
                    "codex-app",
                    "/Users/tester/Applications/Codex.app/Contents/Resources/codex",
                ),
                ("path", "/path/codex"),
            ],
        )

        windows = runtime.runtime_candidates(
            platform_name="Windows",
            environ={
                "LOCALAPPDATA": r"C:\Users\tester\AppData\Local",
                "ProgramFiles": r"C:\Program Files",
            },
            home=Path("C:/Users/tester"),
            which=lambda _: r"C:\Path\codex.exe",
        )
        self.assertEqual(
            [(candidate.source, candidate.path) for candidate in windows],
            [
                (
                    "codex-app",
                    r"C:\Users\tester\AppData\Local\Programs\OpenAI\Codex\bin\codex.exe",
                ),
                (
                    "codex-app",
                    r"C:\Users\tester\AppData\Local\OpenAI\Codex\bin\codex.exe",
                ),
                ("codex-app", r"C:\Program Files\OpenAI\Codex\bin\codex.exe"),
                ("path", r"C:\Path\codex.exe"),
            ],
        )

        linux = runtime.runtime_candidates(
            platform_name="Linux",
            environ={},
            home=Path("/home/tester"),
            which=lambda _: "/opt/bin/codex",
        )
        self.assertEqual(
            [(candidate.source, candidate.path) for candidate in linux],
            [
                (
                    "standalone-runtime",
                    "/home/tester/.codex/packages/standalone/current/bin/codex",
                ),
                ("standalone-runtime", "/home/tester/.local/bin/codex"),
                ("standalone-runtime", "/usr/local/bin/codex"),
                ("standalone-runtime", "/usr/bin/codex"),
                ("path", "/opt/bin/codex"),
            ],
        )

    def test_both_launchers_import_the_same_shared_resolver(self):
        runtime = load_script("codex_runtime", CODEX_RUNTIME)
        process_launcher = load_script(
            "astral_orchestrator_run_agent_shared_resolver_test", RUN_AGENT
        )
        morph_launcher = load_script(
            "astral_orchestrator_run_morph_shared_resolver_test", RUN_MORPH_AGENT
        )

        self.assertIs(
            process_launcher.resolve_codex_runtime,
            runtime.resolve_codex_runtime,
        )
        self.assertIs(
            morph_launcher.resolve_codex_runtime,
            runtime.resolve_codex_runtime,
        )

    def test_dry_runs_probe_runtime_and_emit_only_allowlisted_runtime_evidence(self):
        runtime = load_script("codex_runtime", CODEX_RUNTIME)
        selected = runtime.CodexRuntime(
            path="/selected/codex",
            source="host-runtime",
            version="codex-cli test-version",
            config_probe="pass",
        )

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            workdir = root / "work"
            workdir.mkdir()
            prompt = root / "packet.txt"
            packet = "PRIVATE_DRY_RUN_PACKET"
            prompt.write_text(packet, encoding="utf-8")
            prompt.chmod(0o600)
            settings = root / "missing-effort-levels.toml"

            cases = (
                (
                    "astral_orchestrator_run_agent_dry_run_test",
                    RUN_AGENT,
                    [
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
                ),
                (
                    "astral_orchestrator_run_morph_dry_run_test",
                    RUN_MORPH_AGENT,
                    [
                        "--model",
                        "opencodex/worker-model",
                        "--effort",
                        "high",
                        "--workdir",
                        str(workdir),
                        "--prompt-file",
                        str(prompt),
                        "--dry-run",
                    ],
                ),
            )
            for name, script, arguments in cases:
                with self.subTest(script=script.name):
                    launcher = load_script(name, script)
                    output = io.StringIO()
                    with (
                        mock.patch.object(sys, "argv", [str(script), *arguments]),
                        mock.patch.object(
                            launcher, "resolve_codex_runtime", return_value=selected
                        ) as resolve,
                        mock.patch.object(launcher.subprocess, "run") as start_codex,
                        redirect_stdout(output),
                    ):
                        self.assertEqual(launcher.main(), 0)

                    evidence = json.loads(output.getvalue())
                    resolve.assert_called_once_with()
                    start_codex.assert_not_called()
                    self.assertEqual(evidence["codex_runtime_source"], "host-runtime")
                    self.assertEqual(evidence["codex_version"], "codex-cli test-version")
                    self.assertEqual(evidence["codex_config_probe"], "pass")
                    self.assertNotIn("codex_runtime_path", evidence)
                    self.assertNotIn(packet, output.getvalue())

    def test_launchers_fail_before_inference_when_runtime_resolution_fails(self):
        runtime = load_script("codex_runtime", CODEX_RUNTIME)

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            workdir = root / "work"
            workdir.mkdir()
            prompt = root / "packet.txt"
            packet = "PRIVATE_PACKET_MUST_NOT_LEAK"
            prompt.write_text(packet, encoding="utf-8")
            prompt.chmod(0o600)
            settings = root / "missing-effort-levels.toml"

            cases = (
                (
                    "astral_orchestrator_run_agent_resolution_failure_test",
                    RUN_AGENT,
                    [
                        "--role",
                        "reviewer",
                        "--workdir",
                        str(workdir),
                        "--prompt-file",
                        str(prompt),
                        "--settings-file",
                        str(settings),
                    ],
                ),
                (
                    "astral_orchestrator_run_morph_resolution_failure_test",
                    RUN_MORPH_AGENT,
                    [
                        "--model",
                        "opencodex/worker-model",
                        "--effort",
                        "high",
                        "--workdir",
                        str(workdir),
                        "--prompt-file",
                        str(prompt),
                    ],
                ),
            )
            for name, script, arguments in cases:
                with self.subTest(script=script.name):
                    launcher = load_script(name, script)
                    output = io.StringIO()
                    errors = io.StringIO()
                    with (
                        mock.patch.object(sys, "argv", [str(script), *arguments]),
                        mock.patch.object(
                            launcher,
                            "resolve_codex_runtime",
                            side_effect=runtime.RuntimeResolutionError(
                                "no compatible Codex runtime (path: probe failed)"
                            ),
                        ),
                        mock.patch.object(launcher.subprocess, "run") as start_codex,
                        redirect_stdout(output),
                        redirect_stderr(errors),
                    ):
                        with self.assertRaises(SystemExit) as raised:
                            launcher.main()

                    self.assertEqual(raised.exception.code, 1)
                    start_codex.assert_not_called()
                    combined = output.getvalue() + errors.getvalue()
                    self.assertIn("no compatible Codex runtime", combined)
                    self.assertNotIn(packet, combined)


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

        self.assertIn("installable, open-source codex plugin", readme)
        self.assertIn("v3.2.0", readme)
        self.assertIn(
            "codex plugin marketplace add demonbane18/astral-orchestrator --ref main",
            readme,
        )
        self.assertIn("codex plugin add astral-orchestrator@astral-orchestrator", readme)
        self.assertIn("official chatgpt/codex directory", readme)
        self.assertIn("separate publication surface", readme)
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

    def test_preflight_uses_the_bundled_launcher_when_native_profiles_are_absent(self):
        skill = read(SKILL).lower()
        routing = read(ROUTING).lower()

        self.assertIn("successful dry-run", skill)
        self.assertIn("missing or different native profiles", routing)
        self.assertIn("force the exact-process route", routing)
        self.assertIn("do not permit substitution", routing)

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            codex_runtime = make_fake_codex_runtime(root)
            native_profiles = root / "agents"
            native_check = subprocess.run(
                ["sh", str(INSTALL_AGENTS), "--target-dir", str(native_profiles), "--check"],
                cwd=ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertNotEqual(native_check.returncode, 0)

            workdir = root / "work"
            workdir.mkdir()
            prompt = root / "packet.txt"
            prompt.write_text("bounded standalone packet\n", encoding="utf-8")
            prompt.chmod(0o600)
            result = subprocess.run(
                [
                    "python3",
                    str(RUN_AGENT),
                    "--role",
                    "terra",
                    "--workdir",
                    str(workdir),
                    "--prompt-file",
                    str(prompt),
                    "--settings-file",
                    str(root / "no-settings.toml"),
                    "--dry-run",
                ],
                cwd=ROOT,
                check=False,
                capture_output=True,
                text=True,
                env={**os.environ, "ASTRAL_CODEX_PATH": str(codex_runtime)},
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            evidence = json.loads(result.stdout)
            self.assertEqual(evidence["agent_name"], "astral_orchestrator_terra_implementer")
            self.assertEqual(evidence["model"], "gpt-5.6-terra")
            self.assertEqual(evidence["effort"], "xhigh")

    def test_readme_publishes_banner_footprint_and_ori_eval_attribution(self):
        readme = read(ROOT / "README.md")
        first_lines = readme.lstrip().splitlines()

        self.assertTrue(BANNER.is_file())
        self.assertTrue(first_lines[0].startswith("![Animated outer-space Astral Orchestrator banner"))
        self.assertIn("(assets/brand/astral-orchestrator-banner.gif)", first_lines[0])
        for visible_element in (
            "Sol at the center",
            "Luna and Terra orbiting",
            "twinkling stars",
            "passing comet",
        ):
            self.assertIn(visible_element, first_lines[0])
        self.assertIn("# Astral Orchestrator", first_lines[:4])

        for figure in ("2,036", "3,696", "5,636", "7,795", "1,940", "34.4%"):
            self.assertIn(figure, readme)
        footprint = " ".join(
            readme.split("## Measured instruction-context footprint", 1)[1]
            .split("## Configurable effort levels", 1)[0]
            .split()
        )
        self.assertIn("historical v3.2.0 core `SKILL.md` measures **2,036 tokens**", footprint)
        self.assertIn("Guided/full measures **5,636 tokens**", footprint)
        self.assertIn("Measured measures **7,795 tokens**", footprint)
        self.assertIn("instruction-context loading only", footprint)
        self.assertIn("quality, latency, or price", footprint)
        self.assertIn("total tokens for a complete run", footprint)

        self.assertIn("https://openrouter.ai/ori/eval", readme)
        self.assertIn("https://openrouter.ai/skills/spawn-ori-eval", readme)
        attribution = " ".join(readme.lower().split())
        self.assertIn("openrouter's ori eval", attribution)
        self.assertIn("inspired by", attribution)
        self.assertIn("pinned codex gpt-5.6 sol/terra/luna lanes", attribution)
        self.assertIn("does not run or depend on ori or openrouter", attribution)
        self.assertIn("worker-produced guided, measured, morph, or constellation work", attribution)
        self.assertIn("guided, careful, and measured require the three", attribution)

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

    def test_context_footprint_evidence_is_a_valid_historical_snapshot(self):
        self.assertTrue(CONTEXT_FOOTPRINT.is_file())
        evidence = load_json(CONTEXT_FOOTPRINT_MEASURED)
        self.assertTrue(CONTEXT_FOOTPRINT_MEASURER.is_file())
        self.assertEqual(evidence["measured_on"], "2026-08-04")
        self.assertEqual(
            evidence["tokenizer"],
            {"library": "tiktoken", "version": "0.13.0", "encoding": "o200k_base"},
        )

        expected_paths = {item["path"] for item in evidence["files"]}
        self.assertEqual(len(expected_paths), len(evidence["files"]))
        for item in evidence["files"]:
            snapshot = subprocess.run(
                ["git", "show", f"v3.2.0:{item['path']}"],
                cwd=ROOT,
                check=False,
                capture_output=True,
            )
            if snapshot.returncode != 0:
                self.fail(
                    "historical instruction snapshot v3.2.0 is unavailable for "
                    f"{item['path']}: {snapshot.stderr.decode('utf-8', 'replace')}"
                )
            data = snapshot.stdout
            self.assertEqual(item["bytes"], len(data))
            self.assertEqual(item["words"], len(data.decode("utf-8").split()))
            self.assertEqual(item["sha256"], hashlib.sha256(data).hexdigest())

        self.assertEqual(evidence["bundles"]["core"]["tokens"], evidence["files"][0]["tokens"])
        self.assertEqual(
            evidence["bundles"]["quick"],
            {
                "paths": [
                    "plugins/astral-orchestrator/skills/astral-orchestrator/SKILL.md",
                    "plugins/astral-orchestrator/skills/astral-orchestrator/references/modes-and-risk.md",
                    "plugins/astral-orchestrator/skills/astral-orchestrator/references/work-templates.md",
                ],
                "tokens": sum(item["tokens"] for item in evidence["files"][:3]),
            },
        )
        self.assertEqual(evidence["bundles"]["full"]["tokens"], sum(item["tokens"] for item in evidence["files"][:4]))
        self.assertEqual(
            evidence["quick_vs_full"]["tokens_avoided"],
            evidence["bundles"]["full"]["tokens"] - evidence["bundles"]["quick"]["tokens"],
        )
        self.assertEqual(evidence["bundles"]["guided"], evidence["bundles"]["full"])
        self.assertGreater(evidence["bundles"]["measured"]["tokens"], evidence["bundles"]["full"]["tokens"])
        benchmark_guide = read(BENCHMARK_GUIDE)
        self.assertIn("tiktoken==0.13.0", benchmark_guide)
        self.assertIn("measure_instruction_context.py", benchmark_guide)

        readme = read(ROOT / "README.md")
        footprint_section = " ".join(
            readme.split("## Measured instruction-context footprint", 1)[1]
            .split("## Configurable effort levels", 1)[0]
            .split()
        )
        self.assertIn("historical v3.2.0 core", footprint_section)
        for value in (
            evidence["bundles"]["core"]["tokens"],
            evidence["bundles"]["quick"]["tokens"],
            evidence["bundles"]["full"]["tokens"],
            evidence["quick_vs_full"]["tokens_avoided"],
        ):
            self.assertIn(f"**{value:,} tokens", footprint_section)
        self.assertIn(
            f"({evidence['quick_vs_full']['percent_avoided']}%)",
            footprint_section,
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

    def test_notice_uses_the_canonical_improvements_link(self):
        notice = read(NOTICE)

        self.assertIn(f"]({CANONICAL_IMPROVEMENTS_URL})", notice)
        self.assertNotIn("](docs/IMPROVEMENTS.md)", notice)

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


class ReleaseTrackingSkillTests(unittest.TestCase):
    def run_ledger(self, *arguments: str):
        return subprocess.run(
            ["python3", str(RELEASE_LEDGER_SCRIPT), *arguments],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )

    def test_release_skill_tracks_independent_public_surfaces(self):
        skill = read(RELEASE_SKILL)
        reference = read(RELEASE_SURFACES)
        metadata = read(RELEASE_SKILL_METADATA)

        for surface in (
            "source",
            "github_release",
            "github_marketplace",
            "vercel",
            "openai_submission",
            "openai_directory",
        ):
            self.assertIn(surface, skill)
            self.assertIn(surface, reference)
        self.assertIn("never infer one publication surface from another", read(ROOT / "AGENTS.md"))
        self.assertIn("legal or policy attestations", skill)
        self.assertIn("partially released", skill)
        self.assertIn("$track-astral-releases", metadata)

    def test_release_ledger_reports_the_current_public_version_lag(self):
        result = self.run_ledger(
            "status",
            "--ledger",
            str(RELEASE_LEDGER),
            "--expected-version",
            "3.3.1",
            "--format",
            "json",
        )

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        status = json.loads(result.stdout)
        surfaces = status["surfaces"]
        self.assertEqual(surfaces["source"]["version"], "3.3.1")
        self.assertEqual(surfaces["source"]["status"], "verified")
        self.assertEqual(surfaces["github_release"]["version"], "3.3.1")
        self.assertEqual(surfaces["github_marketplace"]["version"], "3.3.1")
        self.assertEqual(surfaces["vercel"]["version"], "3.3.1")
        self.assertEqual(surfaces["vercel"]["status"], "deployed")
        self.assertEqual(surfaces["openai_submission"]["version"], "3.3.1")
        self.assertEqual(surfaces["openai_submission"]["status"], "draft")
        self.assertEqual(surfaces["openai_directory"]["version"], "3.2.0")

    def test_strict_release_check_fails_while_public_directory_lags(self):
        result = self.run_ledger(
            "check",
            "--ledger",
            str(RELEASE_LEDGER),
            "--expected-version",
            "3.3.1",
            "--manifest",
            str(MANIFEST),
        )

        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("openai_directory is 3.2.0", result.stderr)

    def test_record_is_idempotent_and_preserves_history(self):
        with tempfile.TemporaryDirectory() as directory:
            ledger = Path(directory) / "ledger.json"
            shutil.copy2(RELEASE_LEDGER, ledger)
            before = load_json(ledger)
            arguments = (
                "record",
                "--ledger",
                str(ledger),
                "--surface",
                "openai_submission",
                "--version",
                "3.2.0",
                "--status",
                "submitted",
                "--observed-at",
                "2026-08-04T16:00:00+08:00",
                "--evidence",
                "OpenAI Platform accepted the review submission.",
            )

            first = self.run_ledger(*arguments)
            second = self.run_ledger(*arguments)
            after = load_json(ledger)

        self.assertEqual(first.returncode, 0, first.stdout + first.stderr)
        self.assertEqual(second.returncode, 0, second.stdout + second.stderr)
        self.assertEqual(len(after["events"]), len(before["events"]) + 1)
        self.assertIn("ledger unchanged", second.stdout)

    def test_record_rejects_a_status_that_cannot_exist_on_the_surface(self):
        with tempfile.TemporaryDirectory() as directory:
            ledger = Path(directory) / "ledger.json"
            shutil.copy2(RELEASE_LEDGER, ledger)
            result = self.run_ledger(
                "record",
                "--ledger",
                str(ledger),
                "--surface",
                "openai_directory",
                "--version",
                "3.2.0",
                "--status",
                "approved",
                "--observed-at",
                "2026-08-04T16:00:00+08:00",
                "--evidence",
                "Approval is not publication.",
            )

        self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
        self.assertIn("invalid for openai_directory", result.stderr)


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

    def test_repository_verifier_rejects_a_package_relative_improvements_link(self):
        with tempfile.TemporaryDirectory() as directory:
            fixture_root = self.make_package_fixture(directory)
            fixture_plugin = fixture_root / "plugins/astral-orchestrator"

            for notice in (fixture_root / "NOTICE.md", fixture_plugin / "NOTICE.md"):
                notice.write_text(
                    read(notice).replace(CANONICAL_IMPROVEMENTS_URL, "docs/IMPROVEMENTS.md"),
                    encoding="utf-8",
                )

            result = subprocess.run(
                ["sh", str(fixture_plugin / "scripts/verify.sh")],
                cwd=fixture_root,
                check=False,
                capture_output=True,
                text=True,
            )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("canonical NOTICE must link", result.stderr)

    def test_repository_verifier_rejects_a_portable_discovered_skill_symlink_escape(self):
        with tempfile.TemporaryDirectory() as directory:
            fixture_root = self.make_package_fixture(directory)
            fixture_plugin = fixture_root / "plugins/astral-orchestrator"
            outside = Path(directory) / "outside"
            outside.mkdir()
            escaped_skill = outside / "SKILL.md"
            escaped_skill.write_text("---\nname: escaped\n---\n", encoding="utf-8")

            discovered = fixture_plugin / "skills/astral-orchestrator/SKILL.md"
            discovered.unlink()
            discovered.symlink_to(escaped_skill)

            result = subprocess.run(
                ["sh", str(fixture_plugin / "scripts/verify.sh")],
                cwd=fixture_root,
                check=False,
                capture_output=True,
                text=True,
            )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("portable discovered skill escapes the package", result.stderr)

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
