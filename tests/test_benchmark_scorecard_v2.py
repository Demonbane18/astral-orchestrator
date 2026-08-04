import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCORECARD = ROOT / "plugins" / "astral-orchestrator" / "scripts" / "benchmark-scorecard.py"


def load_module():
    spec = importlib.util.spec_from_file_location("benchmark_scorecard_v2", SCORECARD)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class BenchmarkScorecardV2Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.scorecard = load_module()

    def record(self, variant="single-sol-xhigh", repetition=1, *, accepted=True,
               score=90, telemetry=True, trial_id=None):
        if variant.startswith("single-sol"):
            role, model, effort = "single-sol", "gpt-5.6-sol", variant.removeprefix("single-sol-")
            mode = "control"
            process = [{
                "role": role, "model": model, "effort": effort,
                "sandbox": "workspace-write", "expected_sandbox": "workspace-write",
                "session_id": f"session-{variant}-{repetition}",
                "input_tokens": 100, "cached_input_tokens": 25,
                "output_tokens": 50, "reasoning_output_tokens": 30,
                "total_tokens": 150, "duration_seconds": 1.2,
            }]
            route = [{
                "role": role, "model": model, "effort": effort,
                "expected_model": model, "expected_effort": effort,
                "sandbox": "workspace-write", "expected_sandbox": "workspace-write",
                "task_id": f"task-{variant}-{repetition}",
            }]
        else:
            mode = "guided"
            process = [
                {"role": "orchestrator", "model": "gpt-5.6-sol", "effort": "high",
                 "sandbox": "read-only", "expected_sandbox": "read-only",
                 "session_id": f"session-lead-{repetition}", "input_tokens": 60,
                 "cached_input_tokens": 10, "output_tokens": 20,
                 "reasoning_output_tokens": 5, "total_tokens": 80, "duration_seconds": .4},
                {"role": "terra", "model": "gpt-5.6-terra", "effort": "xhigh",
                 "sandbox": "workspace-write", "expected_sandbox": "workspace-write",
                 "session_id": f"session-worker-{repetition}", "input_tokens": 100,
                 "cached_input_tokens": 20, "output_tokens": 40,
                 "reasoning_output_tokens": 10, "total_tokens": 140, "duration_seconds": .7},
                {"role": "reviewer", "model": "gpt-5.6-sol", "effort": "high",
                 "sandbox": "read-only", "expected_sandbox": "read-only",
                 "session_id": f"session-review-{repetition}", "input_tokens": 40,
                 "cached_input_tokens": 5, "output_tokens": 20,
                 "reasoning_output_tokens": 5, "total_tokens": 60, "duration_seconds": .3},
            ]
            route = [{
                "role": item["role"], "model": item["model"], "effort": item["effort"],
                "expected_model": item["model"], "expected_effort": item["effort"],
                "sandbox": item["sandbox"], "expected_sandbox": item["expected_sandbox"],
                "task_id": item["session_id"],
            } for item in process]
        return {
            "schema_version": 2, "trial_id": trial_id or f"{variant}-{repetition}",
            "case_id": "case", "case_fingerprint": "frozen", "repetition": repetition,
            "strategy": "single-sol" if variant.startswith("single-sol") else "astral",
            "variant": variant, "mode": mode,
            "acceptance_checks": ["unit", "lint"],
            "check_results": [
                {"id": "unit", "returncode": 0 if accepted else 1, "duration_seconds": .1},
                {"id": "lint", "returncode": 0, "duration_seconds": .1},
            ],
            "accepted": accepted, "first_pass_accepted": accepted,
            "rework_required": False, "wall_time_seconds": 1.2,
            "model_calls": len(process),
            "aggregate_tokens": {
                "input_tokens": sum(item["input_tokens"] for item in process),
                "cached_input_tokens": sum(item["cached_input_tokens"] for item in process),
                "output_tokens": sum(item["output_tokens"] for item in process),
                "reasoning_output_tokens": sum(item["reasoning_output_tokens"] for item in process),
                "total_tokens": sum(item["total_tokens"] for item in process),
            },
            "process_metrics": process if telemetry else None,
            "route_evidence": route, "route_correct": True,
            "opaque_artifact": {"id": "artifact-1", "diff_path": "artifacts/a.patch", "diff_sha256": "a" * 64},
            "blind_judge": {
                "rubric": "fixed-v1", "score": score, "blinded": True,
                "usage": {"input_tokens": 10, "cached_input_tokens": 0,
                          "output_tokens": 5, "reasoning_output_tokens": 2, "total_tokens": 15},
            },
            "failure": None, "timeout": False, "disclosures": [] if telemetry else ["process telemetry unavailable"],
        }

    def test_valid_v2_report_has_variants_and_metrics(self):
        records = [self.record(variant, repetition)
                   for variant in ("single-sol-xhigh", "astral-guided")
                   for repetition in (1, 2)]
        report = self.scorecard.build_v2_report(self.scorecard.validate_v2_records(records, 2), 2)
        self.assertEqual(report["schema_version"], 2)
        self.assertEqual(set(report["variants"]), {"single-sol-xhigh", "astral-guided"})
        summary = report["variants"]["single-sol-xhigh"]
        self.assertEqual(summary["mean_total_tokens"], 150.0)
        self.assertEqual(summary["mean_cached_input_tokens"], 25.0)
        self.assertIn("quality_per_10000_strategy_tokens", summary)
        self.assertIn("quality_per_elapsed_minute", summary)

    def test_exact_token_arithmetic_and_judge_usage_exclusion(self):
        record = self.record()
        self.scorecard.validate_v2_record(record, 1)
        record["aggregate_tokens"]["total_tokens"] = 175
        with self.assertRaisesRegex(self.scorecard.BenchmarkError, "input_tokens \\+ output_tokens"):
            self.scorecard.validate_v2_record(record, 1)

    def test_repaired_control_can_have_multiple_calls_on_the_same_exact_route(self):
        record = self.record(repetition=2)
        repair_process = dict(record["process_metrics"][0])
        repair_process["session_id"] = "session-single-sol-xhigh-repair"
        record["process_metrics"].append(repair_process)
        record["route_evidence"].append({
            **record["route_evidence"][0],
            "task_id": "task-single-sol-xhigh-repair",
        })
        for field in record["aggregate_tokens"]:
            record["aggregate_tokens"][field] *= 2
        record["model_calls"] = 2
        record["first_pass_accepted"] = False
        record["rework_required"] = True
        self.scorecard.validate_v2_record(record, 1)
        records = [
            self.record("single-sol-xhigh", 1),
            record,
            self.record("astral-guided", 1),
            self.record("astral-guided", 2),
        ]
        self.scorecard.validate_v2_records(records, 2)

    def test_missing_process_telemetry_is_disclosed_not_zero(self):
        record = self.record(telemetry=False)
        astral = self.record("astral-guided", telemetry=True)
        parsed = self.scorecard.validate_v2_record(record, 1)
        parsed_astral = self.scorecard.validate_v2_record(astral, 1)
        report = self.scorecard.build_v2_report(
            self.scorecard.validate_v2_records([parsed, parsed_astral], 1), 1
        )
        self.assertIsNone(report["variants"]["single-sol-xhigh"]["mean_process_input_tokens"])
        self.assertTrue(any("telemetry" in item.lower() for item in report["disclosures"]))

    def test_objective_acceptance_is_independent_of_blind_judge(self):
        records = [self.record("single-sol-xhigh", 1, score=0), self.record("astral-guided", 1, score=100)]
        report = self.scorecard.build_v2_report(
            self.scorecard.validate_v2_records(records, 1), 1
        )
        self.assertEqual(report["variants"]["single-sol-xhigh"]["success_rate"], 1.0)
        self.assertEqual(report["variants"]["astral-guided"]["success_rate"], 1.0)

    def test_max_variant_can_be_absent_and_paired_ci_is_deterministic(self):
        records = [self.record(variant, repetition)
                   for variant in ("single-sol-xhigh", "astral-guided")
                   for repetition in (1, 2)]
        first = self.scorecard.build_v2_report(self.scorecard.validate_v2_records(records, 2), 2)
        second = self.scorecard.build_v2_report(self.scorecard.validate_v2_records(records, 2), 2)
        self.assertNotIn("single-sol-max", first["variants"])
        self.assertEqual(first["comparisons"], second["comparisons"])
        self.assertIn("ci95", first["comparisons"]["astral-guided_vs_single-sol-xhigh"]["mean_wall_time_seconds"])

    def test_blind_judge_validation_duplicate_ids_and_mixed_schema(self):
        record = self.record()
        record["blind_judge"]["blinded"] = False
        with self.assertRaisesRegex(self.scorecard.BenchmarkError, "blinded"):
            self.scorecard.validate_v2_record(record, 1)
        first = self.record(trial_id="same")
        second = self.record("astral-guided", trial_id="same")
        with self.assertRaisesRegex(self.scorecard.BenchmarkError, "duplicate trial_id"):
            self.scorecard.validate_v2_records([first, second], 1)
        v1 = {"schema_version": 1}
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "mixed.jsonl"
            path.write_text(json.dumps(first) + "\n" + json.dumps(v1) + "\n", encoding="utf-8")
            with self.assertRaisesRegex(self.scorecard.BenchmarkError, "mixed schema"):
                self.scorecard.load_records(path)

    def test_route_task_ids_are_unique_across_all_trials(self):
        first = self.record("single-sol-xhigh", 1)
        second = self.record("astral-guided", 1)
        second["route_evidence"][0]["task_id"] = first["route_evidence"][0]["task_id"]
        with self.assertRaisesRegex(self.scorecard.BenchmarkError, "duplicate route task_id"):
            self.scorecard.validate_v2_records([first, second], 1)

    def test_objective_checks_require_an_explicit_outcome(self):
        record = self.record()
        record["check_results"] = [{"id": "unit"}, {"id": "lint"}]
        with self.assertRaisesRegex(self.scorecard.BenchmarkError, "explicit outcome"):
            self.scorecard.validate_v2_record(record, 1)
        record["process_disclosures"] = []
        paired = self.record("astral-guided", 1)
        with self.assertRaisesRegex(self.scorecard.BenchmarkError, "explicit outcome"):
            self.scorecard.validate_v2_records([record, paired], 1)

    def test_missing_judge_usage_is_allowed_and_reported_as_unavailable(self):
        records = [self.record("single-sol-xhigh", 1), self.record("astral-guided", 1)]
        records[0]["blind_judge"]["usage"] = None
        records[0]["blind_judge"]["score"] = None
        records[0]["disclosures"].append("blind judge unavailable")
        report = self.scorecard.build_v2_report(
            self.scorecard.validate_v2_records(records, 1), 1
        )
        self.assertIsNone(report["variants"]["single-sol-xhigh"]["mean_judge_score"])
        self.assertIn("n/a", self.scorecard.text_report_v2(report))

    def test_route_sandbox_mismatch_invalidates_route_correctness(self):
        record = self.record()
        record["route_evidence"][0]["sandbox"] = "read-only"
        with self.assertRaisesRegex(self.scorecard.BenchmarkError, "route_correct"):
            self.scorecard.validate_v2_record(record, 1)

    def test_explicit_failure_can_use_null_strategy_telemetry_without_inferred_zeros(self):
        failed = self.record(accepted=False, score=None)
        failed.update({
            "first_pass_accepted": False,
            "failure": "worker failed before telemetry was collected",
            "wall_time_seconds": None,
            "model_calls": None,
            "aggregate_tokens": None,
            "process_metrics": None,
            "route_evidence": [],
            "route_correct": False,
        })
        failed["check_results"][0]["returncode"] = 1
        failed["blind_judge"]["usage"] = None
        successful = self.record("astral-guided", score=100)
        grouped = self.scorecard.validate_v2_records(
            [self.scorecard.validate_v2_record(failed, 1), successful], 1
        )
        report = self.scorecard.build_v2_report(grouped, 1)
        summary = report["variants"]["single-sol-xhigh"]
        self.assertEqual(summary["success_rate"], 0.0)
        self.assertEqual(summary["failure_count"], 1)
        self.assertIsNone(summary["mean_wall_time_seconds"])
        self.assertIsNone(summary["mean_model_calls"])
        self.assertIsNone(summary["mean_total_tokens"])
        self.assertIsNone(summary["quality_per_10000_strategy_tokens"])
        self.assertIsNone(summary["quality_per_elapsed_minute"])
        self.assertIn("n/a", self.scorecard.text_report_v2(report))

    def test_efficiency_comparisons_use_ratio_of_means_point_estimate(self):
        def set_aggregate(record, total_tokens, wall_time):
            record["process_metrics"] = None
            record["disclosures"] = ["process telemetry unavailable"]
            record["aggregate_tokens"] = {
                "input_tokens": total_tokens - 50,
                "cached_input_tokens": 0,
                "output_tokens": 50,
                "reasoning_output_tokens": 0,
                "total_tokens": total_tokens,
            }
            record["wall_time_seconds"] = wall_time

        baseline_one = self.record("single-sol-xhigh", 1, score=100)
        baseline_two = self.record("single-sol-xhigh", 2, score=100)
        variant_one = self.record("astral-guided", 1, score=100)
        variant_two = self.record("astral-guided", 2, score=100)
        set_aggregate(baseline_one, 100, 1)
        set_aggregate(baseline_two, 300, 3)
        set_aggregate(variant_one, 100, 1)
        set_aggregate(variant_two, 100, 1)
        records = [baseline_one, baseline_two, variant_one, variant_two]
        report = self.scorecard.build_v2_report(
            self.scorecard.validate_v2_records(records, 2), 2
        )
        baseline = report["variants"]["single-sol-xhigh"]
        variant = report["variants"]["astral-guided"]
        comparison = report["comparisons"]["astral-guided_vs_single-sol-xhigh"]
        self.assertEqual(
            comparison["quality_per_10000_strategy_tokens"]["delta"],
            variant["quality_per_10000_strategy_tokens"]
            - baseline["quality_per_10000_strategy_tokens"],
        )
        self.assertEqual(
            comparison["quality_per_elapsed_minute"]["delta"],
            variant["quality_per_elapsed_minute"] - baseline["quality_per_elapsed_minute"],
        )


if __name__ == "__main__":
    unittest.main()
