import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
RUNNER = ROOT / "benchmarks" / "run_pilot.py"
SCORECARD = ROOT / "plugins" / "astral-orchestrator" / "scripts" / "benchmark-scorecard.py"


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


class BenchmarkPilotTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.runner = load_module("benchmark_pilot_runner", RUNNER)
        cls.scorecard = load_module("benchmark_pilot_scorecard", SCORECARD)

    def valid_v2(self):
        return {
            "schema_version": 2,
            "trial_id": "opaque-1",
            "case_id": "scorecard-correctness",
            "case_fingerprint": "frozen-sha",
            "repetition": 1,
            "strategy": "single-sol",
            "variant": "single-sol-xhigh",
            "mode": "control",
            "acceptance_checks": ["fixture-test"],
            "check_results": [{"id": "fixture-test", "returncode": 0, "duration_seconds": 0.1}],
            "accepted": True,
            "first_pass_accepted": True,
            "rework_required": False,
            "wall_time_seconds": 1.2,
            "model_calls": 1,
            "aggregate_tokens": {
                "input_tokens": 100,
                "cached_input_tokens": 25,
                "output_tokens": 50,
                "reasoning_output_tokens": 30,
                "total_tokens": 150,
            },
            "process_metrics": [{
                "role": "single-sol",
                "model": "gpt-5.6-sol",
                "effort": "xhigh",
                "sandbox": "workspace-write",
                "expected_sandbox": "workspace-write",
                "session_id": "session-1",
                "input_tokens": 100,
                "cached_input_tokens": 25,
                "output_tokens": 50,
                "reasoning_output_tokens": 30,
                "total_tokens": 150,
                "duration_seconds": 1.2,
            }],
            "route_evidence": [{
                "role": "single-sol",
                "model": "gpt-5.6-sol",
                "effort": "xhigh",
                "expected_model": "gpt-5.6-sol",
                "expected_effort": "xhigh",
                "sandbox": "workspace-write",
                "expected_sandbox": "workspace-write",
                "task_id": "session-1",
            }],
            "route_correct": True,
            "opaque_artifact": {"id": "opaque-1", "diff_path": "artifacts/opaque-1.patch", "diff_sha256": "a" * 64},
            "blind_judge": {
                "rubric": "fixed-100-point-v1",
                "score": 90,
                "blinded": True,
                "usage": {"input_tokens": 10, "cached_input_tokens": 0, "output_tokens": 5, "reasoning_output_tokens": 2, "total_tokens": 15},
            },
            "failure": None,
            "timeout": False,
            "disclosures": [],
        }

    def test_schema_v2_validation_and_exact_token_arithmetic(self):
        self.scorecard.validate_v2_record(self.valid_v2(), 1)
        invalid = self.valid_v2()
        invalid["aggregate_tokens"]["total_tokens"] = 175
        with self.assertRaisesRegex(self.scorecard.BenchmarkError, r"input_tokens \+ output_tokens"):
            self.scorecard.validate_v2_record(invalid, 1)

    def test_schema_v1_records_still_parse(self):
        v1 = {
            "schema_version": 1, "trial_id": "legacy", "case_id": "legacy", "case_fingerprint": "v1",
            "trial": 1, "strategy": "single-sol", "acceptance_checks": ["test"], "accepted": True,
            "first_pass_accepted": True, "rework_required": False, "wall_time_seconds": 1,
            "model_calls": 1,
            "route_evidence": [{"role": "single-sol", "model": "gpt-5.6-sol", "effort": "high", "expected_effort": "high", "task_id": "legacy-1"}],
        }
        trial = self.scorecard.parse_trial(v1, 1)
        self.assertEqual(trial.strategy, "single-sol")

    def test_plan_is_seeded_paired_and_discloses_max_in_dry_run(self):
        cases = self.runner.load_cases(self.runner.DEFAULT_CASES_PATH)
        first = self.runner.build_plan(cases, repetitions=2, variants=("single-sol-xhigh", "astral-guided"), seed=77)
        second = self.runner.build_plan(cases, repetitions=2, variants=("single-sol-xhigh", "astral-guided"), seed=77)
        self.assertEqual(first, second)
        self.assertEqual(len(first), 16)
        pairs = {(item["case_id"], item["repetition"]) for item in first}
        self.assertEqual(len(pairs), 8)
        for case_id, repetition in pairs:
            variants = {item["variant"] for item in first if item["case_id"] == case_id and item["repetition"] == repetition}
            self.assertEqual(variants, {"single-sol-xhigh", "astral-guided"})
        self.assertEqual(self.runner.max_route_disclosure(True), "single-sol-max not preflighted during dry run")

    def test_default_cli_profile_is_a_two_trial_quick_plan(self):
        result = subprocess.run(
            [
                "python3", str(RUNNER), "--dry-run",
                "--output-dir", "/tmp/unused-astral-quick-plan",
            ],
            cwd=ROOT, check=False, capture_output=True, text=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        manifest = json.loads(result.stdout)
        self.assertEqual(manifest["profile"], "quick")
        self.assertEqual(len(manifest["plan"]), 2)
        self.assertEqual({item["case_id"] for item in manifest["plan"]}, {"scorecard-correctness"})
        self.assertEqual(
            {item["variant"] for item in manifest["plan"]},
            {"single-sol-xhigh", "astral-guided"},
        )

    def test_unsupported_max_is_disclosed_without_substitution(self):
        result = mock.Mock(returncode=1, stdout="", stderr="unsupported effort")
        with mock.patch.object(self.runner.subprocess, "run", return_value=result):
            supported, disclosure = self.runner.preflight_max("codex", ROOT, timeout_seconds=2)
        self.assertFalse(supported)
        self.assertIn("single-sol-max unsupported", disclosure)

    def test_enforces_immutable_fixtures_and_allowed_paths(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            immutable = root / "fixture.py"
            allowed = root / "allowed.py"
            escaped = root / "escaped.py"
            immutable.write_text("original\n", encoding="utf-8")
            allowed.write_text("original\n", encoding="utf-8")
            escaped.write_text("original\n", encoding="utf-8")
            hashes = self.runner.snapshot_hashes(root, ["fixture.py"])
            immutable.write_text("changed\n", encoding="utf-8")
            violations = self.runner.enforce_trial_integrity(
                root, hashes, ["allowed.py"], ["fixture.py", "escaped.py"]
            )
        self.assertIn("immutable fixture changed: fixture.py", violations)
        self.assertIn("changed path outside allowlist: escaped.py", violations)

    def test_blind_judge_prompt_redacts_strategy_and_route_labels(self):
        prompt = self.runner.build_judge_prompt(
            task_text="Repair the fixture.",
            rubric="fixed rubric",
            files={"target.py": "x = 1\n"},
            diff="diff --git a/target.py b/target.py\n",
            check_results=[{"id": "unit", "returncode": 0, "duration_seconds": 1}],
        )
        self.assertNotIn("astral", prompt.lower())
        self.assertNotIn("single-sol", prompt.lower())
        self.assertNotIn("gpt-5", prompt.lower())
        self.assertIn('"score"', prompt)

    def test_bootstrap_confidence_intervals_are_deterministic(self):
        pairs = [(0.0, 1.0), (1.0, 1.0), (0.5, 0.75)]
        self.assertEqual(
            self.runner.paired_bootstrap_ci(pairs, seed=42, samples=300),
            self.runner.paired_bootstrap_ci(pairs, seed=42, samples=300),
        )

    def test_preview_is_generated_only_from_scored_json(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "preview.html"
            scored = {
                "schema_version": 2,
                "pilot_scope": "local pilot",
                "comparisons": {},
                "limitations": ["small local sample"],
                "variants": {
                    "failed-route": {
                        "success_rate": 0,
                        "mean_judge_score": None,
                        "mean_total_tokens": None,
                        "mean_wall_time_seconds": None,
                        "quality_per_10000_strategy_tokens": None,
                        "quality_per_elapsed_minute": None,
                    }
                },
            }
            self.runner.generate_preview(scored, output)
            content = output.read_text(encoding="utf-8")
        self.assertIn("Local Astral benchmark pilot", content)
        self.assertIn("local pilot", content)
        self.assertIn("small local sample", content)
        self.assertIn("failed-route", content)
        self.assertGreaterEqual(content.count("n/a"), 4)

    def test_scope_copy_uses_actual_case_and_repetition_overrides(self):
        scope, limitation = self.runner.scope_copy(2, 3)
        self.assertEqual(
            scope,
            "2 frozen local repository cases with 3 randomized repetitions; not a product-wide claim.",
        )
        self.assertIn("Only 2 internal repository cases and 3 randomized repetitions", limitation)
        singular_scope, _ = self.runner.scope_copy(1, 1)
        self.assertIn("1 frozen local repository case with 1 repetition", singular_scope)

    def test_retained_invalid_pilot_labels_every_derived_surface(self):
        result_dir = ROOT / "benchmarks" / "results" / "2026-08-04-invalid-pilot"
        scorecard = json.loads((result_dir / "scorecard.json").read_text(encoding="utf-8"))
        preview = (result_dir / "preview.html").read_text(encoding="utf-8")
        self.assertTrue(scorecard["invalid_evidence"])
        self.assertEqual(scorecard["evidence_status"], "invalid")
        self.assertGreaterEqual(len(scorecard["invalid_reasons"]), 1)
        self.assertIn("INVALID EXPLORATORY PILOT", preview)
        self.assertIn("none of the figures below support a claim", preview)

    def test_tiny_fake_codex_run_generates_all_artifacts(self):
        with tempfile.TemporaryDirectory() as directory:
            directory_path = Path(directory)
            fake = directory_path / "fake-codex.py"
            fake.write_text(
                "#!/usr/bin/env python3\n"
                "import json, pathlib, sys, uuid\n"
                "root = pathlib.Path.cwd()\n"
                "args = sys.argv[1:]\n"
                "model = args[args.index('--model') + 1]\n"
                "config = args[args.index('-c') + 1]\n"
                "effort = config.split('=', 1)[1].strip(chr(34))\n"
                "sandbox = args[args.index('--sandbox') + 1]\n"
                "prompt = args[-1]\n"
                "target = root / 'plugins/astral-orchestrator/scripts/run-agent.py'\n"
                "if sandbox == 'workspace-write' and target.is_file():\n"
                "    target.write_text(target.read_text(encoding='utf-8').replace(chr(34) + 'sandbox' + chr(34) + ': ' + chr(34) + 'workspace-write' + chr(34), chr(34) + 'sandbox' + chr(34) + ': ' + chr(34) + 'read-only' + chr(34)), encoding='utf-8')\n"
                "session = 'fake-' + uuid.uuid4().hex\n"
                "print(json.dumps({'type':'thread.started','thread_id':session}))\n"
                "if 'Astral completion review' in prompt:\n"
                "    state = pathlib.Path(__file__).with_suffix('.review-count')\n"
                "    count = int(state.read_text()) if state.exists() else 0\n"
                "    state.write_text(str(count + 1))\n"
                "    message = 'VERDICT: fix-first\\nexercise repair' if count == 0 else 'VERDICT: ship'\n"
                "    print(json.dumps({'type':'item.completed','item':{'type':'agent_message','text':message}}))\n"
                "elif 'fresh read-only evaluator' in prompt:\n"
                "    print(json.dumps({'type':'item.completed','item':{'type':'agent_message','text':'{\\\"score\\\": 88}'}}))\n"
                "else:\n"
                "    print(json.dumps({'type':'item.completed','item':{'type':'agent_message','text':'plan'}}))\n"
                "print(json.dumps({'type':'turn.completed','model':model,'effort':effort,'sandbox':sandbox,'usage':{'input_tokens':100,'cached_input_tokens':10,'output_tokens':20,'reasoning_output_tokens':5}}))\n",
                encoding="utf-8",
            )
            fake.chmod(0o755)
            output = directory_path / "output"
            result = subprocess.run(
                ["python3", str(RUNNER), "--base-ref", "HEAD", "--output-dir", str(output), "--cases", "launcher-telemetry", "--repetitions", "1", "--max-trials", "2", "--skip-max-preflight", "--codex", str(fake), "--timeout-seconds", "10"],
                cwd=ROOT, check=False, capture_output=True, text=True,
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            for name in ("run-manifest.json", "trials.jsonl", "scorecard.json", "preview.html"):
                self.assertTrue((output / name).is_file(), name)
            records = [json.loads(line) for line in (output / "trials.jsonl").read_text(encoding="utf-8").splitlines()]
            self.assertEqual(len(records), 2)
            self.assertEqual(
                {record["variant"]: record["aggregate_tokens"]["total_tokens"] for record in records},
                {"single-sol-xhigh": 120, "astral-guided": 600},
            )
            astral = next(record for record in records if record["variant"] == "astral-guided")
            self.assertFalse(astral["first_pass_accepted"])
            self.assertTrue(astral["rework_required"])
            self.assertTrue(astral["accepted"])
            self.assertEqual(
                {(route["role"], route["model"], route["effort"]) for route in astral["route_evidence"]},
                {
                    ("orchestrator", "gpt-5.6-sol", "high"),
                    ("terra", "gpt-5.6-terra", "xhigh"),
                    ("reviewer", "gpt-5.6-sol", "high"),
                },
            )

    def test_reviewer_verdict_requires_explicit_first_line(self):
        self.assertEqual(self.runner.review_verdict("VERDICT: ship\nclean"), "ship")
        self.assertEqual(self.runner.review_verdict("VERDICT: fix-first\nissue"), "fix-first")
        self.assertIsNone(self.runner.review_verdict("looks good"))


if __name__ == "__main__":
    unittest.main()
