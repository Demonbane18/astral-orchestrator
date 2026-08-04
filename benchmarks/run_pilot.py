#!/usr/bin/env python3
"""Run a local, evidence-preserving Astral Orchestrator benchmark pilot."""

from __future__ import annotations

import argparse
import hashlib
import html
import io
import json
import os
import random
import re
import shutil
import subprocess
import sys
import tempfile
import time
import tomllib
import tarfile
import uuid
from pathlib import Path
from typing import Any, Iterable


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CASES_PATH = ROOT / "benchmarks" / "pilot" / "cases.json"
SCORECARD_PATH = ROOT / "plugins" / "astral-orchestrator" / "scripts" / "benchmark-scorecard.py"
PILOT_OVERLAY = ROOT / "benchmarks" / "pilot"
PROFILE_DIR = ROOT / "plugins" / "astral-orchestrator" / "agents"
DEFAULT_SEED = 20260804
DEFAULT_MAX_TRIALS = 24
DEFAULT_MAX_SECONDS = 7200
QUICK_DEFAULT_CASE = "scorecard-correctness"
QUICK_MAX_SECONDS = 1800
EMPTY_USAGE = {
    "input_tokens": 0,
    "cached_input_tokens": 0,
    "output_tokens": 0,
    "reasoning_output_tokens": 0,
    "total_tokens": 0,
}
EXPECTED_SANDBOXES = {
    "single-sol": "workspace-write",
    "orchestrator": "read-only",
    "terra": "workspace-write",
    "reviewer": "read-only",
}
VARIANTS = ("single-sol-xhigh", "single-sol-max", "astral-guided")
RUBRIC = """Fixed 100-point rubric (fixed-100-point-v1): correctness 45, completeness 20,
regression safety 15, maintainability 10, and scope discipline 10. Objective acceptance
checks are authoritative; score only the submitted artifact and task packet. Return exactly
one JSON object with numeric score from 0 to 100 and a concise reason."""


class PilotError(RuntimeError):
    pass


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def load_cases(path: Path) -> list[dict[str, Any]]:
    value = json.loads(Path(path).read_text(encoding="utf-8"))
    cases = value.get("cases") if isinstance(value, dict) else None
    if not isinstance(cases, list) or not cases:
        raise PilotError("cases file must contain a non-empty cases list")
    ids: set[str] = set()
    for case in cases:
        required = {"id", "title", "task", "allowed_paths", "immutable_paths", "checks"}
        if not isinstance(case, dict) or not required <= set(case):
            raise PilotError("each case must contain the frozen case fields")
        if case["id"] in ids:
            raise PilotError(f"duplicate case id: {case['id']}")
        ids.add(case["id"])
    return cases


def case_fingerprint(case: dict[str, Any]) -> str:
    frozen = json.dumps(case, sort_keys=True, separators=(",", ":")).encode()
    related: list[tuple[str, str]] = []
    for key in ("immutable_paths",):
        for relative in case.get(key, []):
            path = ROOT / relative
            related.append((relative, sha256_bytes(path.read_bytes())))
    setup_patch = case.get("setup_patch")
    if setup_patch:
        related.append((setup_patch, sha256_bytes((ROOT / setup_patch).read_bytes())))
    return sha256_bytes(frozen + json.dumps(related, sort_keys=True).encode())


def build_plan(
    cases: list[dict[str, Any]],
    repetitions: int,
    variants: Iterable[str],
    seed: int = DEFAULT_SEED,
) -> list[dict[str, Any]]:
    if repetitions < 1:
        raise PilotError("repetitions must be positive")
    selected = tuple(variants)
    unknown = set(selected) - set(VARIANTS)
    if unknown:
        raise PilotError(f"unsupported variants: {', '.join(sorted(unknown))}")
    rng = random.Random(seed)
    pairs = [(case, repetition) for case in cases for repetition in range(1, repetitions + 1)]
    rng.shuffle(pairs)
    plan: list[dict[str, Any]] = []
    for case, repetition in pairs:
        local = list(selected)
        rng.shuffle(local)
        for variant in local:
            plan.append({"case_id": case["id"], "repetition": repetition, "variant": variant})
    return plan


def max_route_disclosure(dry_run: bool) -> str:
    return (
        "single-sol-max not preflighted during dry run"
        if dry_run
        else "single-sol-max unsupported by exact preflight; variant omitted without substitution"
    )


def _codex_prefix(codex: str) -> list[str]:
    return [sys.executable, codex] if Path(codex).suffix == ".py" else [codex]


def preflight_max(
    codex: str, cwd: Path, timeout_seconds: float = 120
) -> tuple[bool, str]:
    prompt = "Reply with exactly READY_MAX and do not edit files."
    command = _codex_prefix(codex) + [
        "exec", "--ephemeral", "--ignore-user-config", "--json",
        "--model", "gpt-5.6-sol", "-c", 'model_reasoning_effort="max"',
        "--sandbox", "read-only", "--skip-git-repo-check", "--cd", str(cwd), prompt,
    ]
    try:
        result = subprocess.run(command, cwd=cwd, text=True, capture_output=True, timeout=timeout_seconds)
    except (OSError, subprocess.TimeoutExpired) as error:
        return False, f"single-sol-max unsupported: {error}"
    if result.returncode != 0 or "READY_MAX" not in result.stdout:
        detail = (result.stderr or result.stdout or "preflight failed").strip().replace("\n", " ")
        return False, f"single-sol-max unsupported: {detail[:300]}"
    return True, "single-sol-max exact preflight passed"


def snapshot_hashes(root: Path, paths: Iterable[str]) -> dict[str, str]:
    hashes: dict[str, str] = {}
    for relative in paths:
        path = root / relative
        hashes[relative] = sha256_bytes(path.read_bytes()) if path.is_file() else "MISSING"
    return hashes


def changed_paths(root: Path) -> set[str]:
    result = subprocess.run(
        ["git", "status", "--porcelain=v1", "--untracked-files=all"],
        cwd=root, text=True, capture_output=True, check=False,
    )
    if result.returncode != 0:
        raise PilotError(result.stderr.strip() or "git status failed")
    paths: set[str] = set()
    for line in result.stdout.splitlines():
        raw = line[3:]
        if " -> " in raw:
            raw = raw.split(" -> ", 1)[1]
        paths.add(raw.strip().strip('"'))
    return paths


def enforce_trial_integrity(
    root: Path,
    immutable_hashes: dict[str, str],
    allowed_paths: Iterable[str],
    candidate_paths: Iterable[str] = (),
    *,
    ignored_paths: Iterable[str] = (),
) -> list[str]:
    violations: list[str] = []
    for relative, before in immutable_hashes.items():
        path = root / relative
        after = sha256_bytes(path.read_bytes()) if path.is_file() else "MISSING"
        if after != before:
            violations.append(f"immutable fixture changed: {relative}")
    allowed = set(allowed_paths)
    ignored = set(ignored_paths)
    try:
        observed_changes = changed_paths(root)
    except PilotError:
        observed_changes = set(candidate_paths)
    for relative in sorted(observed_changes):
        if relative in ignored or any(relative.startswith(prefix.rstrip("/") + "/") for prefix in ignored):
            continue
        if relative not in allowed:
            violations.append(f"changed path outside allowlist: {relative}")
    return violations


def build_judge_prompt(
    task_text: str,
    rubric: str,
    files: dict[str, str],
    diff: str,
    check_results: list[dict[str, Any]],
) -> str:
    payload = {
        "task": task_text,
        "files": files,
        "diff": diff,
        "objective_checks": check_results,
        "response_schema": {"score": "number 0..100", "reason": "short string"},
    }
    return (
        "You are a fresh read-only evaluator. The submission is anonymized; do not infer its author "
        "or execution strategy.\n\n" + rubric + "\n\n" + json.dumps(payload, sort_keys=True)
    )


def paired_bootstrap_ci(
    pairs: list[tuple[float, float]], seed: int = DEFAULT_SEED, samples: int = 2000
) -> dict[str, float] | None:
    if not pairs:
        return None
    rng = random.Random(seed)
    differences: list[float] = []
    for _ in range(samples):
        sample = [pairs[rng.randrange(len(pairs))] for _ in pairs]
        differences.append(sum(right - left for left, right in sample) / len(sample))
    differences.sort()
    return {
        "estimate": sum(right - left for left, right in pairs) / len(pairs),
        "lower_95": differences[int(0.025 * (samples - 1))],
        "upper_95": differences[int(0.975 * (samples - 1))],
    }


def generate_preview(scored: dict[str, Any], output: Path) -> None:
    variants = scored.get("variants", {})
    rows = []
    for name, summary in variants.items():
        judge_score = summary.get("mean_judge_score")
        judge_display = "n/a" if judge_score is None else f"{judge_score:.1f}"
        token_quality = summary.get("quality_per_10000_strategy_tokens")
        token_quality_display = "n/a" if token_quality is None else f"{token_quality:.2f}"
        time_quality = summary.get("quality_per_elapsed_minute")
        time_quality_display = "n/a" if time_quality is None else f"{time_quality:.2f}"
        mean_tokens = summary.get("mean_total_tokens")
        token_display = "n/a" if mean_tokens is None else f"{mean_tokens:,.0f}"
        mean_wall_time = summary.get("mean_wall_time_seconds")
        wall_time_display = "n/a" if mean_wall_time is None else f"{mean_wall_time:,.1f}s"
        rows.append(
            "<tr>"
            f"<th>{html.escape(name)}</th>"
            f"<td>{100 * summary.get('success_rate', 0):.1f}%</td>"
            f"<td>{judge_display}</td>"
            f"<td>{token_display}</td>"
            f"<td>{wall_time_display}</td>"
            f"<td>{token_quality_display}</td>"
            f"<td>{time_quality_display}</td>"
            "</tr>"
        )
    scope = html.escape(str(scored.get("pilot_scope", "Four frozen local repository cases; results are not product-wide.")))
    disclosures = [
        *scored.get("limitations", []),
        *scored.get("disclosures", []),
        *scored.get("warnings", []),
    ]
    disclosure_html = "".join(f"<li>{html.escape(str(item))}</li>" for item in disclosures) or "<li>None recorded.</li>"
    document = f"""<!doctype html><html lang=\"en\"><head><meta charset=\"utf-8\">
<meta name=\"viewport\" content=\"width=device-width,initial-scale=1\"><title>Local Astral benchmark pilot</title>
<style>:root{{--bg:#08101f;--panel:#111b31;--text:#eef3ff;--muted:#aab6d0;--accent:#ffc34d}}*{{box-sizing:border-box}}body{{margin:0;background:var(--bg);color:var(--text);font:16px/1.5 system-ui,sans-serif}}main{{max-width:1100px;margin:auto;padding:48px 24px}}h1{{font-size:clamp(2rem,5vw,4rem);margin:.2em 0;color:var(--accent)}}p{{color:var(--muted)}}section{{background:var(--panel);border:1px solid #293858;border-radius:18px;padding:22px;margin-top:24px;overflow:auto}}table{{border-collapse:collapse;width:100%;min-width:760px}}th,td{{padding:13px;text-align:left;border-bottom:1px solid #293858}}thead th{{color:var(--accent)}}code{{color:#9ee6ff}}</style></head>
<body><main><p>MEASURED LOCAL EVIDENCE</p><h1>Local Astral benchmark pilot</h1><p>{scope}</p>
<section><table><thead><tr><th>Variant</th><th>Accepted</th><th>Blind score</th><th>Strategy tokens</th><th>Elapsed</th><th>Quality / 10k tokens</th><th>Quality / minute</th></tr></thead><tbody>{''.join(rows)}</tbody></table></section>
<section><h2>Limitations and disclosures</h2><ul>{disclosure_html}</ul></section></main></body></html>"""
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(document, encoding="utf-8")


def parse_json_stream(
    stdout: str,
) -> tuple[str | None, dict[str, int] | None, str, str | None, str | None, str | None]:
    session_id: str | None = None
    usage: dict[str, int] | None = None
    messages: list[str] = []
    model: str | None = None
    effort: str | None = None
    sandbox: str | None = None
    for line in stdout.splitlines():
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if not isinstance(event, dict):
            continue
        if event.get("type") == "thread.started":
            session_id = event.get("thread_id") or event.get("session_id")
        if event.get("type") in {"turn.completed", "turn_complete"}:
            raw = event.get("usage") or {}
            if isinstance(raw, dict):
                input_tokens = int(raw.get("input_tokens", 0))
                output_tokens = int(raw.get("output_tokens", 0))
                usage = {
                    "input_tokens": input_tokens,
                    "cached_input_tokens": int(raw.get("cached_input_tokens", 0)),
                    "output_tokens": output_tokens,
                    "reasoning_output_tokens": int(raw.get("reasoning_output_tokens", 0)),
                    "total_tokens": input_tokens + output_tokens,
                }
            model = event.get("model") or model
            effort = event.get("effort") or event.get("model_reasoning_effort") or effort
            sandbox = event.get("sandbox") or sandbox
        item = event.get("item")
        if isinstance(item, dict) and item.get("type") == "agent_message":
            text = item.get("text") or item.get("content")
            if isinstance(text, str):
                messages.append(text)
        if event.get("type") == "agent_message" and isinstance(event.get("text"), str):
            messages.append(event["text"])
    return session_id, usage, "\n".join(messages), model, effort, sandbox


def observe_persisted_route(
    session_id: str | None,
) -> tuple[str | None, str | None, str | None]:
    """Read model, effort, and sandbox Codex persisted for a completed session."""
    if not session_id:
        return None, None, None
    sessions = Path.home() / ".codex" / "sessions"
    if not sessions.is_dir():
        return None, None, None
    candidates = list(sessions.rglob(f"*{session_id}*.jsonl"))
    if not candidates:
        return None, None, None
    model: str | None = None
    effort: str | None = None
    sandbox: str | None = None
    try:
        for line in candidates[-1].read_text(encoding="utf-8").splitlines():
            event = json.loads(line)
            if event.get("type") == "turn_context" and isinstance(event.get("payload"), dict):
                model = event["payload"].get("model") or model
                effort = event["payload"].get("effort") or effort
                policy = event["payload"].get("sandbox_policy")
                if isinstance(policy, dict):
                    sandbox = policy.get("type") or sandbox
    except (OSError, json.JSONDecodeError):
        return None, None, None
    return model, effort, sandbox


def read_profile(role: str) -> tuple[str, str, str]:
    names = {
        "terra": "astral-orchestrator-terra-implementer.toml",
        "reviewer": "astral-orchestrator-sol-reviewer.toml",
    }
    with (PROFILE_DIR / names[role]).open("rb") as handle:
        profile = tomllib.load(handle)
    return profile["model"], profile["model_reasoning_effort"], profile["developer_instructions"]


def run_model(
    codex: str,
    worktree: Path,
    role: str,
    model: str,
    effort: str,
    sandbox: str,
    prompt: str,
    timeout_seconds: float,
    developer_instructions: str | None = None,
    deadline: float | None = None,
) -> dict[str, Any]:
    command = _codex_prefix(codex) + [
        "exec", "--ignore-user-config", "--json", "--model", model,
        "-c", f"model_reasoning_effort={json.dumps(effort)}",
    ]
    if developer_instructions:
        command += ["-c", f"developer_instructions={json.dumps(developer_instructions)}"]
    command += ["--sandbox", sandbox, "--skip-git-repo-check", "--cd", str(worktree), prompt]
    started = time.monotonic()
    effective_timeout = timeout_seconds
    if deadline is not None:
        effective_timeout = min(timeout_seconds, max(0.0, deadline - started))
    if effective_timeout <= 0:
        return {
            "returncode": 124, "duration_seconds": 0.0, "session_id": None,
            "usage": None, "message": "", "model": model, "effort": effort,
            "sandbox": sandbox, "stdout": "", "stderr": "pilot wall-time cap reached", "role": role,
            "expected_model": model, "expected_effort": effort, "expected_sandbox": sandbox,
            "timeout": True, "route_observed": False,
        }
    try:
        result = subprocess.run(command, cwd=worktree, text=True, capture_output=True, timeout=effective_timeout)
        duration = time.monotonic() - started
        session_id, usage, message, observed_model, observed_effort, observed_sandbox = parse_json_stream(result.stdout)
        persisted_model, persisted_effort, persisted_sandbox = observe_persisted_route(session_id)
        observed_model = persisted_model or observed_model
        observed_effort = persisted_effort or observed_effort
        observed_sandbox = persisted_sandbox or observed_sandbox
        return {
            "returncode": result.returncode, "duration_seconds": duration,
            "session_id": session_id, "usage": usage, "message": message,
            "model": observed_model or model, "effort": observed_effort or effort,
            "sandbox": observed_sandbox or sandbox,
            "expected_model": model, "expected_effort": effort, "expected_sandbox": sandbox,
            "route_observed": bool(observed_model and observed_effort and observed_sandbox),
            "stdout": result.stdout, "stderr": result.stderr, "role": role,
        }
    except subprocess.TimeoutExpired as error:
        return {
            "returncode": 124, "duration_seconds": time.monotonic() - started,
            "session_id": None, "usage": None, "message": "", "model": model,
            "effort": effort, "stdout": error.stdout or "", "stderr": "model call timed out",
            "sandbox": sandbox, "role": role, "timeout": True, "route_observed": False,
            "expected_model": model, "expected_effort": effort, "expected_sandbox": sandbox,
        }


def process_metric(call: dict[str, Any]) -> dict[str, Any] | None:
    if not call.get("session_id") or call.get("usage") is None or not call.get("route_observed"):
        return None
    return {
        "role": call["role"], "model": call["model"], "effort": call["effort"],
        "sandbox": call["sandbox"], "expected_sandbox": call["expected_sandbox"],
        "session_id": call["session_id"], **call["usage"],
        "duration_seconds": call["duration_seconds"],
    }


def sum_usage(calls: list[dict[str, Any]]) -> dict[str, int] | None:
    if any(call.get("usage") is None for call in calls):
        return None
    complete = [call["usage"] for call in calls]
    return {key: sum(int(item[key]) for item in complete) for key in EMPTY_USAGE}


def run_checks(worktree: Path, case: dict[str, Any]) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    for check in case["checks"]:
        started = time.monotonic()
        result = subprocess.run(check["command"], cwd=worktree, text=True, capture_output=True, check=False)
        results.append({
            "id": check["id"], "returncode": result.returncode,
            "duration_seconds": time.monotonic() - started,
            "stdout": result.stdout[-4000:], "stderr": result.stderr[-4000:],
        })
    return results


def apply_setup(worktree: Path, case: dict[str, Any]) -> None:
    destination = worktree / "benchmarks" / "pilot"
    if destination.exists():
        shutil.rmtree(destination)
    shutil.copytree(PILOT_OVERLAY, destination)
    if case.get("setup_patch"):
        result = subprocess.run(
            ["git", "apply", case["setup_patch"]], cwd=worktree,
            text=True, capture_output=True, check=False,
        )
        if result.returncode != 0:
            raise PilotError(result.stderr.strip() or "setup patch failed")


def create_worktree(
    base_ref: str, parent: Path, trial_id: str, *, allow_archive_fallback: bool = False
) -> Path:
    path = parent / trial_id
    result = subprocess.run(
        ["git", "worktree", "add", "--detach", str(path), base_ref], cwd=ROOT,
        text=True, capture_output=True, check=False,
    )
    if result.returncode != 0:
        if allow_archive_fallback:
            archive = subprocess.run(
                ["git", "archive", "--format=tar", base_ref], cwd=ROOT,
                capture_output=True, check=False,
            )
            if archive.returncode == 0:
                path.mkdir(parents=True)
                with tarfile.open(fileobj=io.BytesIO(archive.stdout), mode="r:") as bundle:
                    bundle.extractall(path, filter="data")
                return path
        raise PilotError(result.stderr.strip() or "git worktree add failed")
    return path


def remove_worktree(path: Path) -> None:
    if (path / ".git").exists():
        subprocess.run(["git", "worktree", "remove", "--force", str(path)], cwd=ROOT, capture_output=True)
    elif path.exists():
        shutil.rmtree(path)


def task_prompt(case: dict[str, Any]) -> str:
    return (
        case["task"] + "\n\nDo not edit any path outside: " + ", ".join(case["allowed_paths"])
        + "\nDo not modify the immutable acceptance fixtures. Work directly, then stop."
    )


def strategy_calls(
    variant: str, codex: str, worktree: Path, case: dict[str, Any], timeout_seconds: float,
    deadline: float,
) -> list[dict[str, Any]]:
    prompt = task_prompt(case)
    if variant.startswith("single-sol-"):
        effort = variant.removeprefix("single-sol-")
        return [run_model(codex, worktree, "single-sol", "gpt-5.6-sol", effort, "workspace-write", prompt, timeout_seconds, deadline=deadline)]

    terra_model, terra_effort, terra_instructions = read_profile("terra")
    lead = run_model(
        codex, worktree, "orchestrator", "gpt-5.6-sol", "high", "read-only",
        "Create a concise implementation plan for this frozen task. Do not edit files.\n\n" + prompt,
        timeout_seconds, deadline=deadline,
    )
    worker = run_model(
        codex, worktree, "terra", terra_model, terra_effort, "workspace-write",
        prompt + "\n\nLead plan:\n" + lead.get("message", ""), timeout_seconds, terra_instructions, deadline,
    )
    return [lead, worker]


def current_diff(worktree: Path, allowed_paths: list[str]) -> str:
    if not (worktree / ".git").exists():
        return "archive fallback used by injected test executable; diff unavailable\n"
    result = subprocess.run(
        ["git", "diff", "--binary", "--", *allowed_paths],
        cwd=worktree, text=True, capture_output=True, check=False,
    )
    return result.stdout


def internal_review_prompt(
    case: dict[str, Any], worktree: Path, check_results: list[dict[str, Any]]
) -> str:
    packet = {
        "task": case["task"],
        "objective_checks": check_results,
        "diff": current_diff(worktree, case["allowed_paths"]),
    }
    return (
        "Perform a fresh read-only Astral completion review after the objective checks. "
        "Do not edit files. Inspect correctness, completeness, regressions, scope, and the "
        "actual check evidence. Return exactly one first line: `VERDICT: ship`, "
        "`VERDICT: fix-first`, or `VERDICT: rethink`, followed by concise findings.\n\n"
        + json.dumps(packet, sort_keys=True)
    )


def review_verdict(message: str) -> str | None:
    match = re.search(r"(?im)^\s*VERDICT\s*:\s*(ship|fix-first|rethink)\b", message)
    return match.group(1).lower() if match else None


def run_internal_reviewer(
    codex: str, worktree: Path, case: dict[str, Any], check_results: list[dict[str, Any]],
    timeout_seconds: float, deadline: float,
) -> dict[str, Any]:
    model, effort, instructions = read_profile("reviewer")
    return run_model(
        codex, worktree, "reviewer", model, effort, "read-only",
        internal_review_prompt(case, worktree, check_results),
        timeout_seconds, instructions, deadline,
    )


def files_for_judge(worktree: Path, allowed_paths: list[str]) -> dict[str, str]:
    files: dict[str, str] = {}
    for relative in allowed_paths:
        path = worktree / relative
        if path.is_file() and path.stat().st_size <= 200_000:
            files[relative] = path.read_text(encoding="utf-8", errors="replace")
    return files


def parse_judge(message: str) -> tuple[float | None, str]:
    match = re.search(r"\{.*\}", message, re.DOTALL)
    if not match:
        return None, "judge returned no JSON score"
    try:
        value = json.loads(match.group(0))
        score = float(value["score"])
        if not 0 <= score <= 100:
            raise ValueError
        return score, str(value.get("reason", ""))
    except (KeyError, TypeError, ValueError, json.JSONDecodeError):
        return None, "judge returned invalid JSON score"


def route_for_call(call: dict[str, Any]) -> dict[str, str] | None:
    if not call.get("session_id") or not call.get("route_observed"):
        return None
    return {
        "role": call["role"], "model": call["model"], "effort": call["effort"],
        "expected_model": call["expected_model"], "expected_effort": call["expected_effort"],
        "sandbox": call["sandbox"], "expected_sandbox": call["expected_sandbox"],
        "task_id": call["session_id"],
    }


def run_trial(
    item: dict[str, Any], case: dict[str, Any], base_ref: str, codex: str,
    worktree_parent: Path, artifact_dir: Path, timeout_seconds: float, deadline: float,
) -> dict[str, Any]:
    opaque_id = f"artifact-{uuid.uuid4().hex}"
    trial_id = f"trial-{uuid.uuid4().hex}"
    started = time.monotonic()
    worktree: Path | None = None
    calls: list[dict[str, Any]] = []
    judge_call: dict[str, Any] | None = None
    failure: str | None = None
    timed_out = False
    disclosures: list[str] = []
    first_results: list[dict[str, Any]] = []
    final_results: list[dict[str, Any]] = []
    final_review_verdict: str | None = None
    repair_performed = False
    immutable_hashes: dict[str, str] = {}
    diff = ""
    try:
        worktree = create_worktree(
            base_ref, worktree_parent, trial_id,
            allow_archive_fallback=Path(codex).suffix == ".py",
        )
        apply_setup(worktree, case)
        immutable_hashes = snapshot_hashes(worktree, case["immutable_paths"])
        calls = strategy_calls(item["variant"], codex, worktree, case, timeout_seconds, deadline)
        timed_out = any(call.get("timeout", False) for call in calls)
        failed_calls = [call for call in calls if call["returncode"] != 0]
        if failed_calls:
            failure = "; ".join((call.get("stderr") or "model call failed")[:300] for call in failed_calls)
        first_results = run_checks(worktree, case)
        checks_first_pass = all(result["returncode"] == 0 for result in first_results)
        if item["variant"] == "astral-guided" and not failure and not timed_out:
            reviewer = run_internal_reviewer(
                codex, worktree, case, first_results, timeout_seconds, deadline,
            )
            calls.append(reviewer)
            timed_out = timed_out or reviewer.get("timeout", False)
            if reviewer["returncode"] != 0:
                failure = (reviewer.get("stderr") or "reviewer call failed")[:300]
            final_review_verdict = review_verdict(reviewer.get("message", ""))
        first_pass = checks_first_pass and (
            item["variant"] != "astral-guided" or final_review_verdict == "ship"
        )
        if not first_pass and not failure and not timed_out:
            repair_prompt = (
                task_prompt(case)
                + "\n\nThe first completion gate did not pass. Repair once using this exact evidence:\n"
                + json.dumps({
                    "objective_checks": first_results,
                    "review_verdict": final_review_verdict,
                    "review_findings": calls[-1].get("message", "")
                    if item["variant"] == "astral-guided" else None,
                }, sort_keys=True)
            )
            if item["variant"].startswith("single-sol"):
                effort = item["variant"].removeprefix("single-sol-")
                repair = run_model(codex, worktree, "single-sol", "gpt-5.6-sol", effort, "workspace-write", repair_prompt, timeout_seconds, deadline=deadline)
            else:
                model, effort, instructions = read_profile("terra")
                repair = run_model(codex, worktree, "terra", model, effort, "workspace-write", repair_prompt, timeout_seconds, instructions, deadline)
            calls.append(repair)
            repair_performed = True
            timed_out = timed_out or repair.get("timeout", False)
            if repair["returncode"] != 0:
                failure = (repair.get("stderr") or "repair call failed")[:300]
            final_results = run_checks(worktree, case)
            if item["variant"] == "astral-guided" and not failure and not timed_out:
                final_reviewer = run_internal_reviewer(
                    codex, worktree, case, final_results, timeout_seconds, deadline,
                )
                calls.append(final_reviewer)
                timed_out = timed_out or final_reviewer.get("timeout", False)
                if final_reviewer["returncode"] != 0:
                    failure = (final_reviewer.get("stderr") or "final reviewer call failed")[:300]
                final_review_verdict = review_verdict(final_reviewer.get("message", ""))
        else:
            final_results = first_results
        if item["variant"] == "astral-guided" and final_review_verdict != "ship" and not failure:
            failure = f"Astral completion reviewer did not ship: {final_review_verdict or 'missing verdict'}"
        integrity = enforce_trial_integrity(
            worktree, immutable_hashes, case["allowed_paths"], ignored_paths=["benchmarks/pilot"],
        )
        if integrity:
            failure = "; ".join(integrity)
            disclosures.extend(integrity)
        diff = current_diff(worktree, case["allowed_paths"])
        if not (worktree / ".git").exists():
            disclosures.append("archive snapshot fallback used only for injected test executable")
        artifact_dir.mkdir(parents=True, exist_ok=True)
        diff_path = artifact_dir / f"{opaque_id}.patch"
        diff_path.write_text(diff, encoding="utf-8")
        strategy_wall_time = time.monotonic() - started
        judge_prompt = build_judge_prompt(case["task"], RUBRIC, files_for_judge(worktree, case["allowed_paths"]), diff, final_results)
        judge_call = run_model(codex, worktree, "judge", "gpt-5.6-sol", "high", "read-only", judge_prompt, timeout_seconds, deadline=deadline)
        score, judge_reason = parse_judge(judge_call.get("message", ""))
        if judge_call.get("returncode") != 0 or judge_call.get("timeout"):
            score = None
            judge_reason = "Blind judge unavailable; objective checks remain authoritative."
            disclosures.append("blind judge unavailable; objective acceptance was preserved and judge quality is n/a")
        if judge_call.get("usage") is None:
            disclosures.append("blind judge token telemetry unavailable; no zero inferred in narrative")
        if any(call.get("usage") is None for call in calls):
            disclosures.append("strategy token telemetry incomplete; aggregate tokens are unavailable and no zero was inferred")
        if any(not call.get("route_observed") for call in calls):
            disclosures.append("observed route metadata unavailable for one or more strategy calls; requested route was not treated as proof")
        routes = [route for route in (route_for_call(call) for call in calls) if route]
        expected_roles = {"single-sol"} if item["variant"].startswith("single-sol") else {"orchestrator", "terra", "reviewer"}
        route_correct = expected_roles <= {route["role"] for route in routes} and all(
            route["model"] == route["expected_model"]
            and route["effort"] == route["expected_effort"]
            and route["sandbox"] == route["expected_sandbox"]
            for route in routes
        )
        accepted = all(result["returncode"] == 0 for result in final_results) and not failure and not timed_out
        first_pass_accepted = first_pass and not failure and not timed_out
        strategy_usage = sum_usage(calls)
        judge_usage = judge_call.get("usage")
        process = [metric for metric in (process_metric(call) for call in calls) if metric]
        if len(process) != len(calls):
            process = []
        return {
            "schema_version": 2, "trial_id": trial_id, "case_id": case["id"],
            "case_fingerprint": case_fingerprint(case), "repetition": item["repetition"],
            "strategy": "astral" if item["variant"] == "astral-guided" else "single-sol",
            "variant": item["variant"], "mode": "guided" if item["variant"] == "astral-guided" else "control",
            "acceptance_checks": [check["id"] for check in case["checks"]],
            "check_results": final_results, "accepted": accepted,
            "first_pass_accepted": first_pass_accepted,
            "rework_required": repair_performed,
            "wall_time_seconds": strategy_wall_time, "model_calls": len(calls),
            "aggregate_tokens": strategy_usage, "process_metrics": process or None,
            "route_evidence": routes, "route_correct": route_correct,
            "opaque_artifact": {
                "id": opaque_id, "diff_path": str(diff_path.relative_to(artifact_dir.parent)),
                "diff_sha256": sha256_bytes(diff.encode()),
            },
            "blind_judge": {
                "rubric": "fixed-100-point-v1", "score": score, "reason": judge_reason,
                "blinded": True, "usage": judge_usage,
                "duration_seconds": judge_call.get("duration_seconds"),
                "session_id": judge_call.get("session_id"),
                "model": judge_call.get("model"),
                "effort": judge_call.get("effort"),
                "sandbox": judge_call.get("sandbox"),
            },
            "failure": failure, "timeout": timed_out, "disclosures": disclosures,
        }
    finally:
        if worktree is not None:
            remove_worktree(worktree)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--profile", choices=("quick", "full"), default="quick",
        help="quick runs 2 strategy trials with a 30-minute cap; full runs up to 24 trials over 2 hours",
    )
    parser.add_argument("--base-ref", default="HEAD")
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--cases-file", type=Path, default=DEFAULT_CASES_PATH)
    parser.add_argument("--cases", help="comma-separated case ids")
    parser.add_argument("--repetitions", type=int)
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    parser.add_argument("--max-trials", type=int)
    parser.add_argument("--max-seconds", type=float)
    parser.add_argument("--include-max", action="store_true", help="preflight and add Max outside the full profile")
    parser.add_argument("--skip-max-preflight", action="store_true")
    parser.add_argument("--codex", default="codex")
    parser.add_argument("--timeout-seconds", type=float)
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def scope_copy(case_count: int, repetitions: int) -> tuple[str, str]:
    """Describe the actual selected pilot size, including CLI overrides."""
    case_label = "case" if case_count == 1 else "cases"
    repetition_label = "repetition" if repetitions == 1 else "randomized repetitions"
    scope = (
        f"{case_count} frozen local repository {case_label} with {repetitions} {repetition_label}; "
        "not a product-wide claim."
    )
    limitation = (
        f"Only {case_count} internal repository {case_label} and {repetitions} {repetition_label} were measured; "
        "this small local result is exploratory and not broadly generalizable."
    )
    return scope, limitation


def main() -> int:
    args = parse_args()
    cases = load_cases(args.cases_file)
    repetitions = args.repetitions if args.repetitions is not None else (1 if args.profile == "quick" else 2)
    max_trials = args.max_trials if args.max_trials is not None else (2 if args.profile == "quick" else DEFAULT_MAX_TRIALS)
    max_seconds = args.max_seconds if args.max_seconds is not None else (QUICK_MAX_SECONDS if args.profile == "quick" else DEFAULT_MAX_SECONDS)
    timeout_seconds = args.timeout_seconds if args.timeout_seconds is not None else (300 if args.profile == "quick" else 600)
    if args.cases:
        wanted = set(args.cases.split(","))
        cases = [case for case in cases if case["id"] in wanted]
        if {case["id"] for case in cases} != wanted:
            raise PilotError("unknown case requested")
    elif args.profile == "quick":
        cases = [case for case in cases if case["id"] == QUICK_DEFAULT_CASE]
    variants = ["single-sol-xhigh", "astral-guided"]
    disclosures: list[str] = []
    wants_max = args.profile == "full" or args.include_max
    if not wants_max:
        disclosures.append("quick profile intentionally omits single-sol-max to reduce time and tokens")
    elif args.dry_run or args.skip_max_preflight:
        disclosures.append(max_route_disclosure(True))
    else:
        supported, disclosure = preflight_max(args.codex, ROOT, min(timeout_seconds, 180))
        disclosures.append(disclosure)
        if supported:
            variants.insert(1, "single-sol-max")
    plan = build_plan(cases, repetitions, variants, args.seed)
    if len(plan) > max_trials or max_trials > DEFAULT_MAX_TRIALS:
        raise PilotError(f"planned {len(plan)} trials exceeds cap {min(max_trials, DEFAULT_MAX_TRIALS)}")
    manifest = {
        "schema_version": 1, "profile": args.profile, "base_ref": args.base_ref, "seed": args.seed,
        "repetitions": repetitions, "variants": variants, "plan": plan,
        "max_trials": max_trials, "max_seconds": min(max_seconds, DEFAULT_MAX_SECONDS),
        "disclosures": disclosures,
    }
    if args.dry_run:
        print(json.dumps(manifest, indent=2, sort_keys=True))
        return 0
    if args.output_dir.exists() and any(args.output_dir.iterdir()):
        raise PilotError("output directory must be empty; choose a new directory for each benchmark run")
    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / "run-manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    by_id = {case["id"]: case for case in cases}
    records: list[dict[str, Any]] = []
    run_started = time.monotonic()
    deadline = run_started + min(max_seconds, DEFAULT_MAX_SECONDS)
    with tempfile.TemporaryDirectory(prefix="astral-benchmark-worktrees-") as directory:
        parent = Path(directory)
        for item in plan:
            if time.monotonic() >= deadline:
                raise PilotError("pilot wall-time cap reached before all paired trials completed")
            trial_started = time.monotonic()
            try:
                record = run_trial(item, by_id[item["case_id"]], args.base_ref, args.codex, parent, args.output_dir / "artifacts", timeout_seconds, deadline)
            except Exception as error:  # keep the unattended pilot moving safely
                record = {
                    "schema_version": 2, "trial_id": f"trial-{uuid.uuid4().hex}",
                    "case_id": item["case_id"], "case_fingerprint": case_fingerprint(by_id[item["case_id"]]),
                    "repetition": item["repetition"], "strategy": "astral" if item["variant"] == "astral-guided" else "single-sol",
                    "variant": item["variant"], "mode": "guided" if item["variant"] == "astral-guided" else "control",
                    "acceptance_checks": [check["id"] for check in by_id[item["case_id"]]["checks"]],
                    "check_results": [{"id": check["id"], "returncode": 125} for check in by_id[item["case_id"]]["checks"]],
                    "accepted": False, "first_pass_accepted": False, "rework_required": False,
                    "wall_time_seconds": None, "model_calls": None, "aggregate_tokens": None,
                    "process_metrics": None, "route_evidence": [], "route_correct": False,
                    "opaque_artifact": {"id": f"artifact-{uuid.uuid4().hex}", "diff_path": "artifacts/unavailable.patch", "diff_sha256": sha256_bytes(b"")},
                    "blind_judge": {"rubric": "fixed-100-point-v1", "score": None, "blinded": True, "usage": None},
                    "failure": str(error), "timeout": False,
                    "disclosures": [
                        "trial infrastructure failed; unavailable wall time, model calls, and token telemetry remain null",
                        f"exception surfaced after {time.monotonic() - trial_started:.3f} seconds; this diagnostic is not scored",
                    ],
                }
            records.append(record)
            with (args.output_dir / "trials.jsonl").open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(record, sort_keys=True) + "\n")
    score = subprocess.run(
        [sys.executable, str(SCORECARD_PATH), "--min-trials", str(repetitions), "--format", "json", str(args.output_dir / "trials.jsonl")],
        cwd=ROOT, text=True, capture_output=True, check=False,
    )
    if score.returncode != 0:
        raise PilotError(score.stderr.strip() or "scorecard failed")
    scored = json.loads(score.stdout)
    scored["pilot_scope"], sample_limitation = scope_copy(len(cases), repetitions)
    scored["limitations"] = [
        sample_limitation,
        "The blind evaluator was Sol High rather than an independent human panel, and scores clustered near the rubric ceiling.",
        "Trials ran sequentially in one local environment; service load and cache effects were not independently controlled.",
        "The pilot compares tokens and elapsed time, not monetary price.",
    ]
    scored["disclosures"] = sorted(set(scored.get("disclosures", []) + disclosures))
    (args.output_dir / "scorecard.json").write_text(json.dumps(scored, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    generate_preview(scored, args.output_dir / "preview.html")
    print(json.dumps({"output_dir": str(args.output_dir), "trial_count": len(records), "variants": variants}, sort_keys=True))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except PilotError as error:
        print(f"ERROR: {error}", file=sys.stderr)
        raise SystemExit(2)
