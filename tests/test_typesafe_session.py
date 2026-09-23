"""Focused behavior checks for the optional session switch and Jev route boundary."""

from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]


def load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


session = load("typesafe_session_script", ROOT / "plugins/typesafe-session/scripts/session.py")
router = load("astral_choose_worker", ROOT / "plugins/astral-orchestrator/scripts/choose-worker.py")
SESSION = "12345678-1234-1234-1234-123456789abc"


class SessionToggleTests(unittest.TestCase):
    def test_project_opt_in_explicit_off_compaction_and_other_session(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            project = root / "project"
            project.mkdir()
            (project / "AGENTS.md").write_text("TypeSafe session: on\n")
            with mock.patch.dict(os.environ, {"CODEX_HOME": str(root / "codex")}, clear=False):
                base = {"session_id": SESSION, "cwd": str(project)}
                start = session.hook({**base, "hook_event_name": "SessionStart", "source": "startup"})
                self.assertIn("is on", start["hookSpecificOutput"]["additionalContext"])
                off = session.hook({**base, "hook_event_name": "UserPromptSubmit", "prompt": "TypeSafe off"})
                self.assertIn("is off", off["hookSpecificOutput"]["additionalContext"])
                compact = session.hook({**base, "hook_event_name": "SessionStart", "source": "compact"})
                self.assertIn("is off", compact["hookSpecificOutput"]["additionalContext"])
                self.assertEqual(router.session_mode(SESSION, project), "off")
                self.assertEqual(router.session_mode("87654321-1234-1234-1234-123456789abc", project), "on")
                session.hook({**base, "hook_event_name": "SessionEnd"})
                self.assertEqual(router.session_mode(SESSION, project), "on")

    def test_default_off_and_commands_are_standalone(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with mock.patch.dict(os.environ, {"CODEX_HOME": str(root / "codex")}, clear=False):
                base = {"session_id": SESSION, "cwd": str(root), "hook_event_name": "UserPromptSubmit"}
                ordinary = session.hook({**base, "prompt": "Please say TypeSafe on later"})
                self.assertIn("is off", ordinary["hookSpecificOutput"]["additionalContext"])
                enabled = session.hook({**base, "prompt": "TypeSafe on"})
                self.assertIn("is on", enabled["hookSpecificOutput"]["additionalContext"])
                status = session.hook({**base, "prompt": "TypeSafe status"})
                self.assertIn("is on", status["hookSpecificOutput"]["additionalContext"])

    def test_trusted_project_instruction_can_activate_without_marker(self):
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            with mock.patch.dict(os.environ, {"CODEX_HOME": str(project / "codex")}, clear=False):
                self.assertEqual(router.session_mode(SESSION, project), "off")
                result = subprocess.run(
                    ["python3", str(ROOT / "plugins/typesafe-session/scripts/session.py"), "set", SESSION, str(project), "on"],
                    env=os.environ.copy(), capture_output=True, text=True, check=False,
                )
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(router.session_mode(SESSION, project), "on")


class RouteSelectionTests(unittest.TestCase):
    def packet(self, **changes):
        value = {"mode": "Orbit", "session_id": SESSION, "native_v2": True, "available_models": ["gpt-6-luna", "gpt-6-sol", "gpt-6-astra"], "permission_to_delegate": True, "acceptance_settled": True, "allow_external_judgment": True, "safe_summary": "Implement a bounded settings form with known acceptance checks."}
        value.update(changes)
        return value

    def response(self, model="gpt-6-sol", confidence=0.9, score=1.0):
        return {"answers": {"worker": {"type": "choice", "choice": model, "confidence": confidence}, "difficulty": {"type": "score", "score": score, "confidence": 0.9}}}

    def test_filters_models_and_never_routes_single_session_modes(self):
        self.assertEqual(router.valid_candidates(self.packet(available_models=["gpt-6-luna"])), ["gpt-6-luna"])
        self.assertEqual(router.valid_candidates(self.packet(mode="Hypernova")), ["gpt-6-sol", "gpt-6-astra"])
        self.assertEqual(router.valid_candidates(self.packet(mode="Comet")), [])
        self.assertEqual(router.valid_candidates(self.packet(mode="Hypernova", native_v2=False)), [])
        self.assertEqual(router.valid_candidates(self.packet(native_v2=False)), ["gpt-6-luna", "gpt-6-sol"])
        self.assertEqual(router.valid_candidates(self.packet(available_efforts={"gpt-6-luna": ["ultra"], "gpt-6-sol": ["high"]})), ["gpt-6-sol", "gpt-6-astra"])
        self.assertEqual(router.valid_candidates(self.packet(permission_to_delegate=False)), [])
        self.assertEqual(router.valid_candidates(self.packet(acceptance_settled=False)), [])
        self.assertNotIn("gpt-5.6-terra", router.valid_candidates(self.packet(available_models=["gpt-5.6-terra", "gpt-6-sol"])))

    def test_explicit_legacy_route_and_unavailable_model(self):
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            chosen = router.decide(self.packet(explicit_model="gpt-5.6-terra", available_models=["gpt-5.6-terra"]), project)
            self.assertEqual((chosen["source"], chosen["model"]), ("explicit", "gpt-5.6-terra"))
            unavailable = router.decide(self.packet(explicit_model="gpt-5.6-terra"), project)
            self.assertEqual(unavailable["reason"], "no-eligible-worker-route")
            with self.assertRaises(ValueError):
                router.decide(self.packet(explicit_model="gpt-6-sol", explicit_effort="ultra"), project)
            mismatch = router.decide(self.packet(explicit_model="gpt-6-sol", explicit_effort="max", native_v2=False), project)
            self.assertEqual(mismatch["reason"], "launcher-effort-mismatch")

    def test_choice_score_and_uncertainty_are_bounded(self):
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            (project / "AGENTS.md").write_text("TypeSafe session: on\n")
            high = router.decide(self.packet(), project, response=self.response(score=1.8))
            self.assertEqual((high["source"], high["model"], high["effort"]), ("jev", "gpt-6-sol", "max"))
            self.assertEqual(router.decide(self.packet(), project, response=self.response(model="gpt-5.6-terra"))["reason"], "invalid-jev-choice")
            self.assertEqual(router.decide(self.packet(), project, response=self.response(confidence=0.1))["reason"], "uncertain-jev-choice")
            self.assertEqual(router.decide(self.packet(), project, response=self.response(confidence=1.3))["reason"], "invalid-jev-confidence")
            hypernova = router.decide(self.packet(mode="Hypernova"), project, response=self.response(score=0.1))
            self.assertEqual(hypernova["effort"], "max")
            legacy_host = router.decide(self.packet(native_v2=False), project, response=self.response(score=1.8))
            self.assertEqual(legacy_host["effort"], "high")

    def test_missing_key_is_visible_without_network(self):
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            (project / "AGENTS.md").write_text("TypeSafe session: on\n")
            with mock.patch.dict(os.environ, {"CODEX_HOME": str(project / "codex")}, clear=False), mock.patch.dict(os.environ, {"TYPESAFE_API_KEY": ""}, clear=False), mock.patch.object(router, "typesafe_request") as request:
                result = router.decide(self.packet(), project)
                self.assertEqual(result["reason"], "typesafe-key-missing")
                request.assert_not_called()

    def test_project_key_is_private_and_live_call_uses_typed_candidates(self):
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            (project / "AGENTS.md").write_text("TypeSafe session: on\n")
            env_file = project / ".env.local"
            env_file.write_text("TYPESAFE_API_KEY=test-only\n")
            env_file.chmod(0o600)
            with mock.patch.dict(os.environ, {"CODEX_HOME": str(project / "codex"), "TYPESAFE_API_KEY": ""}, clear=False), mock.patch.object(router, "typesafe_request", return_value=self.response()) as request:
                chosen = router.decide(self.packet(), project)
                self.assertEqual(chosen["model"], "gpt-6-sol")
                self.assertEqual(request.call_args.args[1], ["gpt-6-luna", "gpt-6-sol", "gpt-6-astra"])
                self.assertEqual(request.call_args.args[2], "test-only")
            env_file.chmod(0o644)
            with mock.patch.dict(os.environ, {"TYPESAFE_API_KEY": ""}, clear=False), self.assertRaises(ValueError):
                router.project_key(project)
