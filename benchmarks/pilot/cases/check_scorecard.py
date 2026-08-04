import json
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
SCRIPT = ROOT / "plugins/astral-orchestrator/scripts/benchmark-scorecard.py"


def record(strategy, task_id):
    model = "gpt-5.6-sol" if strategy == "single-sol" else "gpt-5.6-terra"
    return {
        "schema_version": 1, "trial_id": f"{strategy}-{task_id}", "case_id": "case",
        "case_fingerprint": "frozen", "trial": 1, "strategy": strategy,
        "acceptance_checks": ["unit"], "accepted": True, "first_pass_accepted": True,
        "rework_required": False, "wall_time_seconds": 1, "model_calls": 1 if strategy == "single-sol" else 3,
        "input_tokens": 100, "cached_input_tokens": 40, "output_tokens": 20,
        "reasoning_output_tokens": 10,
        "route_evidence": ([{"role": "single-sol", "model": model, "effort": "high", "expected_effort": "high", "task_id": task_id}]
            if strategy == "single-sol" else [
                {"role": "orchestrator", "model": "gpt-5.6-sol", "effort": "high", "expected_effort": "high", "task_id": f"lead-{task_id}"},
                {"role": "terra", "model": model, "effort": "xhigh", "expected_effort": "xhigh", "task_id": task_id},
                {"role": "reviewer", "model": "gpt-5.6-sol", "effort": "high", "expected_effort": "high", "task_id": f"review-{task_id}"},
            ]),
    }


with tempfile.TemporaryDirectory() as directory:
    trials = Path(directory) / "trials.jsonl"
    records = [record("single-sol", "control"), record("astral", "worker")]
    trials.write_text("\n".join(json.dumps(item) for item in records) + "\n", encoding="utf-8")
    result = subprocess.run([sys.executable, str(SCRIPT), "--min-trials", "1", "--format", "json", str(trials)], check=False, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    report = json.loads(result.stdout)
    assert report["strategies"]["single-sol"]["mean_total_tokens"] == 120.0
    assert report["strategies"]["single-sol"]["mean_cached_input_tokens"] == 40.0
    assert report["strategies"]["single-sol"]["mean_reasoning_output_tokens"] == 10.0
    records[1].pop("cached_input_tokens")
    trials.write_text("\n".join(json.dumps(item) for item in records) + "\n", encoding="utf-8")
    partial = subprocess.run([sys.executable, str(SCRIPT), "--min-trials", "1", str(trials)], check=False, capture_output=True, text=True)
    assert partial.returncode != 0
    assert "cached_input_tokens" in partial.stderr
