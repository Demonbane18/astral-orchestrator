"""Focused behavior checks for the optional session switch and Jev route boundary."""

from __future__ import annotations

import importlib.util
import io
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
ares = load("astral_inspect_ares", ROOT / "plugins/astral-orchestrator/scripts/inspect-ares.py")
ares_evidence = load("astral_ares_evidence", ROOT / "plugins/astral-orchestrator/scripts/ares_evidence.py")
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

    def test_malformed_session_state_does_not_activate_adaptive(self):
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            with mock.patch.dict(os.environ, {"CODEX_HOME": str(project / "codex")}, clear=False):
                path = session.state_path(SESSION)
                path.parent.mkdir(parents=True)
                path.write_text("[]")
                self.assertEqual(router.session_settings(SESSION, project)["adaptive"], "off")
                self.assertEqual(session.read_state(path, str(project))["adaptive"], "off")

    def test_adaptive_provider_is_independent_and_compaction_scoped(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with mock.patch.dict(os.environ, {"CODEX_HOME": str(root / "codex")}, clear=False):
                base = {"session_id": SESSION, "cwd": str(root), "hook_event_name": "UserPromptSubmit"}
                session.hook({**base, "prompt": "Adaptive on openrouter"})
                self.assertEqual(router.session_settings(SESSION, root), {"typesafe": "off", "adaptive": "on", "provider": "openrouter"})
                session.hook({**base, "prompt": "TypeSafe off"})
                session.hook({**base, "hook_event_name": "SessionStart", "source": "compact"})
                self.assertEqual(router.session_settings(SESSION, root)["provider"], "openrouter")
                self.assertEqual(router.session_settings("87654321-1234-1234-1234-123456789abc", root)["adaptive"], "off")
                session.hook({**base, "prompt": "Adaptive off"})
                self.assertEqual(router.session_settings(SESSION, root)["adaptive"], "off")
                session.hook({**base, "prompt": "Please turn Adaptive on typesafe"})
                self.assertEqual(router.session_settings(SESSION, root)["adaptive"], "off")

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
        return {"model": "jev-1.13.0", "answers": {"worker": {"type": "choice", "choice": model, "confidence": confidence}, "difficulty": {"type": "score", "score": score, "confidence": 0.9}}}

    def test_filters_models_and_never_routes_single_session_modes(self):
        self.assertEqual(router.valid_candidates(self.packet(available_models=["gpt-6-luna"])), ["gpt-6-luna"])
        self.assertEqual(router.valid_candidates(self.packet(mode="Hypernova")), ["gpt-6-sol", "gpt-6-astra"])
        self.assertEqual(router.valid_candidates(self.packet(mode="Comet")), [])
        self.assertEqual(router.valid_candidates(self.packet(mode="Morph")), [])
        self.assertEqual(router.valid_candidates(self.packet(mode="Hypernova", native_v2=False)), [])
        self.assertEqual(router.valid_candidates(self.packet(native_v2=False)), ["gpt-6-luna", "gpt-6-sol"])
        self.assertEqual(router.valid_candidates(self.packet(available_efforts={"gpt-6-luna": ["ultra"], "gpt-6-sol": ["high"]})), ["gpt-6-sol", "gpt-6-astra"])
        self.assertEqual(router.valid_candidates(self.packet(permission_to_delegate=False)), [])
        self.assertEqual(router.valid_candidates(self.packet(acceptance_settled=False)), [])
        self.assertNotIn("gpt-5.6-terra", router.valid_candidates(self.packet(available_models=["gpt-5.6-terra", "gpt-6-sol"])))
        with mock.patch.dict(os.environ, {"CODEX_STEP_CONTROLLER_SOCKET": "/tmp/ares-test.sock"}, clear=False):
            self.assertEqual(router.decide(self.packet(), Path("/tmp"))["reason"], "ares-single-agent-only")

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
            self.assertEqual((high["source"], high["model"], high["effort"]), ("jev", "gpt-6-sol", "high"))
            self.assertEqual(router.decide(self.packet(), project, response=self.response(model="gpt-5.6-terra"))["reason"], "invalid-jev-choice")
            self.assertEqual(router.decide(self.packet(), project, response=self.response(confidence=0.1))["reason"], "uncertain-jev-choice")
            self.assertEqual(router.decide(self.packet(), project, response=self.response(confidence=1.3))["reason"], "invalid-jev-confidence")
            hypernova = router.decide(self.packet(mode="Hypernova"), project, response=self.response(score=0.1))
            self.assertEqual(hypernova["effort"], "max")
            legacy_host = router.decide(self.packet(native_v2=False), project, response=self.response(score=1.8))
            self.assertEqual(legacy_host["effort"], "high")
            self.assertEqual(router.decide(self.packet(mode="Comet", recommend_only=True), project)["reason"], "adaptive-off-no-recommendation")

    def test_adaptive_changes_effort_including_hypernova_and_solo_recommends(self):
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            with mock.patch.dict(os.environ, {"CODEX_HOME": str(project / "codex")}, clear=False):
                session.hook({"session_id": SESSION, "cwd": str(project), "hook_event_name": "UserPromptSubmit", "prompt": "Adaptive on typesafe"})
                chosen = router.decide(self.packet(mode="Hypernova"), project, response=self.response(score=0.1))
                self.assertEqual((chosen["model"], chosen["effort"]), ("gpt-6-sol", "low"))
                solo = router.decide(self.packet(mode="Comet", recommend_only=True, permission_to_delegate=False), project, response=self.response(score=1.8))
                self.assertEqual((solo["status"], solo["effort"]), ("recommendation", "max"))
                self.assertEqual(router.decide(self.packet(mode="Comet"), project)["reason"], "no-eligible-worker-route")

    def test_explicit_model_fixed_reviewer_and_uncertain_score(self):
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            with mock.patch.dict(os.environ, {"CODEX_HOME": str(project / "codex")}, clear=False):
                session.hook({"session_id": SESSION, "cwd": str(project), "hook_event_name": "UserPromptSubmit", "prompt": "Adaptive on openrouter"})
                fixed_model = router.decide(self.packet(explicit_model="gpt-6-luna"), project, response={"answers": {"difficulty": {"type": "score", "score": 0, "confidence": 0.9}}})
                self.assertEqual((fixed_model["model"], fixed_model["effort"]), ("gpt-6-luna", "low"))
                reviewer = router.decide(self.packet(role="reviewer", mode="Hypernova"), project)
                self.assertEqual((reviewer["model"], reviewer["effort"], reviewer["source"]), ("gpt-6-sol", "high", "fixed-reviewer"))
                uncertain = router.decide(self.packet(), project, response={"answers": {"worker": self.response()["answers"]["worker"], "difficulty": {"type": "score", "score": 1, "confidence": 0.1}}})
                self.assertEqual(uncertain["reason"], "uncertain-jev-score")

    def test_explicit_effort_filters_models_and_skips_score(self):
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            (project / ".env.local").write_text("TYPESAFE_API_KEY=test-only\n")
            (project / ".env.local").chmod(0o600)
            with mock.patch.dict(os.environ, {"CODEX_HOME": str(project / "codex")}, clear=False):
                session.hook({"session_id": SESSION, "cwd": str(project), "hook_event_name": "UserPromptSubmit", "prompt": "Adaptive on typesafe"})
                packet = self.packet(explicit_effort="high")
                with mock.patch.object(router, "typesafe_request", return_value=self.response()) as request:
                    selected = router.decide(packet, project)
                self.assertEqual((selected["model"], selected["effort"]), ("gpt-6-sol", "high"))
                self.assertFalse(request.call_args.kwargs["adaptive"])
                self.assertEqual(router.valid_candidates(self.packet(explicit_effort="ultra")), ["gpt-6-astra"])
                ultra = router.decide(self.packet(explicit_effort="ultra"), project,
                                      response={"answers": {"worker": {"type": "choice", "choice": "gpt-6-astra", "confidence": 0.9}}})
                self.assertEqual((ultra["model"], ultra["effort"]), ("gpt-6-astra", "ultra"))
                solo = router.decide(self.packet(mode="Comet", recommend_only=True, explicit_model="gpt-6-sol", explicit_effort="high"), project)
                self.assertEqual(solo["status"], "recommendation")

    def test_typesafe_only_filters_unavailable_configured_effort_before_call(self):
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            (project / "AGENTS.md").write_text("TypeSafe session: on\n")
            (project / ".env.local").write_text("TYPESAFE_API_KEY=test-only\n")
            (project / ".env.local").chmod(0o600)
            packet = self.packet(available_efforts={"gpt-6-luna": ["low"], "gpt-6-sol": ["high"], "gpt-6-astra": ["medium"]})
            with mock.patch.dict(os.environ, {"CODEX_HOME": str(project / "codex"), "TYPESAFE_API_KEY": ""}, clear=False), mock.patch.object(router, "typesafe_request", return_value=self.response(model="gpt-6-sol")) as request:
                result = router.decide(packet, project)
            self.assertEqual(result["model"], "gpt-6-sol")
            self.assertEqual(request.call_args.args[1], ["gpt-6-sol", "gpt-6-astra"])

    def test_openrouter_key_and_single_request(self):
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            env_file = project / ".env.local"
            env_file.write_text("OPENROUTER_API_KEY=test-openrouter\n")
            env_file.chmod(0o600)
            with mock.patch.dict(os.environ, {"CODEX_HOME": str(project / "codex"), "OPENROUTER_API_KEY": ""}, clear=False):
                session.hook({"session_id": SESSION, "cwd": str(project), "hook_event_name": "UserPromptSubmit", "prompt": "TypeSafe on"})
                session.hook({"session_id": SESSION, "cwd": str(project), "hook_event_name": "UserPromptSubmit", "prompt": "Adaptive on openrouter"})
                with mock.patch.object(router, "typesafe_request", return_value=self.response()) as request:
                    result = router.decide(self.packet(), project)
                self.assertEqual(result["provider"], "openrouter")
                request.assert_called_once()
                self.assertEqual(request.call_args.kwargs["provider"], "openrouter")
                self.assertTrue(request.call_args.kwargs["adaptive"])
                self.assertEqual(request.call_args.args[2], "test-openrouter")

    def test_opencodex_catalog_filters_exact_model_and_effort(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            home = root / "codex"
            home.mkdir()
            catalog = root / "catalog.json"
            catalog.write_text(json.dumps({"models": [{"slug": "gpt-6-sol", "supported_reasoning_levels": [{"effort": "high"}]}]}))
            (home / "config.toml").write_text(f'model_catalog_json = "{catalog}"\n')
            with mock.patch.dict(os.environ, {"CODEX_HOME": str(home)}, clear=False):
                self.assertEqual(router.valid_candidates(self.packet(transport="opencodex")), ["gpt-6-sol"])
                self.assertEqual(router.allowed_efforts(self.packet(transport="opencodex"), "gpt-6-sol", adaptive=True), ["high"])
                self.assertEqual(router.decide(self.packet(transport="opencodex", explicit_model="gpt-6-sol", explicit_effort="max"), root)["reason"], "effort-unavailable")

    def test_ares_provider_must_match_and_primary_remains_observed(self):
        with tempfile.TemporaryDirectory() as directory:
            config = Path(directory) / "ares.json"
            config.write_text(json.dumps({"provider": "openrouter", "apiKey": "redacted-test-only"}))
            config.chmod(0o600)
            socket_path = "/tmp/test-ares.sock"
            fake_socket = mock.Mock()
            fake_socket.is_absolute.return_value = True
            fake_socket.is_symlink.return_value = False
            fake_socket.exists.return_value = True
            fake_socket.stat.return_value = mock.Mock(st_mode=0o140600, st_uid=os.getuid())
            with mock.patch.object(ares, "Path", side_effect=lambda value: fake_socket if value == socket_path else Path(value)):
                matched = ares.inspect("Sol-Jev", "gpt-6-sol", "high", "openrouter", config, socket_path)
                self.assertEqual((matched["status"], matched["model"]), ("compatible", "gpt-6-sol"))
                self.assertNotIn("apiKey", json.dumps(matched))
                self.assertEqual(ares.inspect("Sol-Jev", "gpt-6-sol", "high", "typesafe", config, socket_path)["reason"], "ares-provider-mismatch")
                self.assertEqual(ares.inspect("Sol-Jev", "gpt-6-astra", "high", None, config, socket_path)["reason"], "primary-route-mismatch")
            self.assertEqual(ares.inspect("Sol-Jev", "gpt-6-sol", "high", None, config, None)["status"], "inactive")

    def test_ares_primary_requires_matching_rollout_and_native_checkpoint(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            rollout = root / f"rollout-test-{SESSION}.jsonl"
            turn_id = "87654321-1234-1234-1234-123456789abc"
            rollout.write_text("\n".join(json.dumps(item) for item in (
                {"type": "session_meta", "payload": {"id": SESSION}},
                {"type": "turn_context", "payload": {"turn_id": turn_id, "model": "Luna-Jev"}},
            )) + "\n")
            runs = root / "runs"
            run = runs / "run-one"
            run.mkdir(parents=True)
            log = run / "decisions.jsonl"
            events = [
                {"type": "decision", "threadId": SESSION, "turnId": turn_id, "step": 1, "model": "gpt-6-luna", "effort": "low", "confirmation": "native_step_context_captured"},
                {"type": "effort_selected", "threadId": SESSION, "turnId": turn_id, "step": 1, "to": "low", "confirmation": "native_step_context_captured"},
            ]
            log.write_text("\n".join(map(json.dumps, events)) + "\n")
            log.chmod(0o600)
            with mock.patch.object(ares_evidence, "private_socket", return_value=True):
                self.assertEqual(ares_evidence.observed_ares_primary(SESSION, rollout, runs, "/tmp/test.sock"),
                                 {"thread_id": SESSION, "model": "gpt-6-luna", "effort": "low"})
                events[1]["to"] = "high"
                log.write_text("\n".join(map(json.dumps, events)) + "\n")
                self.assertIsNone(ares_evidence.observed_ares_primary(SESSION, rollout, runs, "/tmp/test.sock"))
                events[1]["to"] = "low"
                events[0]["turnId"] = "00000000-0000-0000-0000-000000000000"
                log.write_text("\n".join(map(json.dumps, events)) + "\n")
                self.assertIsNone(ares_evidence.observed_ares_primary(SESSION, rollout, runs, "/tmp/test.sock"))

    def test_missing_key_is_visible_without_network(self):
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            (project / "AGENTS.md").write_text("TypeSafe session: on\n")
            with mock.patch.dict(os.environ, {"CODEX_HOME": str(project / "codex")}, clear=False), mock.patch.dict(os.environ, {"TYPESAFE_API_KEY": ""}, clear=False), mock.patch.object(router, "typesafe_request") as request:
                result = router.decide(self.packet(), project)
                self.assertEqual(result["reason"], "typesafe-key-missing")
                request.assert_not_called()

    def test_jev_transport_identifies_client(self):
        payload = io.BytesIO(json.dumps(self.response()).encode("utf-8"))
        with mock.patch.object(router.urllib.request, "urlopen", return_value=payload) as urlopen:
            self.assertEqual(router.typesafe_request("A synthetic bounded task", ["gpt-6-luna"], "test-only"), self.response())
        request = urlopen.call_args.args[0]
        self.assertEqual(request.get_header("User-agent"), "Astral-Orchestrator/3.13.0")
        self.assertEqual(request.get_method(), "POST")

    def test_openrouter_request_pins_jev_provider_without_fallback(self):
        result = {"model": "typesafe/jev-1.13", "provider": "TypeSafe", "answers": {}}
        with mock.patch.object(router.urllib.request, "urlopen", return_value=io.BytesIO(json.dumps(result).encode())) as urlopen:
            self.assertEqual(router.typesafe_request("A synthetic task", ["gpt-6-sol"], "test-only", provider="openrouter", adaptive=True), result)
        request = urlopen.call_args.args[0]
        self.assertEqual(request.full_url, router.OPENROUTER_ENDPOINT)
        body = json.loads(request.data)
        self.assertEqual(body["provider"], {"only": ["typesafe"], "allow_fallbacks": False})
        self.assertEqual(set(body["questions"]), {"worker", "difficulty"})
        with mock.patch.object(router.urllib.request, "urlopen", return_value=io.BytesIO(json.dumps({"model": "other/model", "provider": "Other"}).encode())):
            with self.assertRaises(ValueError):
                router.typesafe_request("A synthetic task", ["gpt-6-sol"], "test-only", provider="openrouter")

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
