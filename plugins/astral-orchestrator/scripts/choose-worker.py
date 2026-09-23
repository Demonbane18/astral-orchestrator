#!/usr/bin/env python3
"""Filter exact Astral worker routes, then optionally ask TypeSafe Jev to choose."""

from __future__ import annotations

import argparse
import json
import os
import re
import stat
import sys
import urllib.error
import urllib.request
from pathlib import Path

ENDPOINT = "https://api.typesafe.ai/v1/systemone"
SESSION_ID = re.compile(r"[A-Za-z0-9_-]{8,128}\Z")
ROUTES = {
    "gpt-6-luna": {"role": "focused", "default_effort": "max", "efforts": ["medium", "high", "max"], "description": "bounded, repeatable implementation"},
    "gpt-6-sol": {"role": "context", "default_effort": "high", "efforts": ["medium", "high", "max"], "description": "context-heavy implementation or debugging"},
    "gpt-6-astra": {"role": "deep", "default_effort": "medium", "efforts": ["medium", "high", "ultra"], "description": "difficult diagnosis or deep synthesis"},
    "gpt-5.6-luna": {"role": "legacy-focused", "default_effort": "max", "efforts": ["max"], "description": "explicit legacy focused route"},
    "gpt-5.6-terra": {"role": "legacy-context", "default_effort": "high", "efforts": ["high"], "description": "explicit legacy context route"},
    "gpt-5.6-sol": {"role": "legacy-sol", "default_effort": "high", "efforts": ["high", "ultra"], "description": "explicit legacy Sol route"},
}
MODES = {"orbit", "event horizon", "pulsar", "morph", "constellation", "hypernova", "comet", "singularity"}


def session_mode(session_id: str, project: Path) -> str:
    if not SESSION_ID.fullmatch(session_id):
        raise ValueError("invalid session id")
    home = Path(os.environ.get("CODEX_HOME", Path.home() / ".codex")).expanduser()
    path = home / "typesafe-session" / "sessions" / f"{session_id}.json"
    if path.is_symlink():
        raise ValueError("unsafe session state")
    if path.is_file():
        data = json.loads(path.read_text(encoding="utf-8"))
        if data.get("project") == str(project.resolve()) and data.get("mode") in {"on", "off"}:
            return data["mode"]
    guide = project / "AGENTS.md"
    if guide.is_file() and not guide.is_symlink() and guide.stat().st_size <= 100_000:
        if "TypeSafe session: on" in guide.read_text(encoding="utf-8").splitlines():
            return "on"
    return "off"


def project_key(project: Path) -> str | None:
    value = os.environ.get("TYPESAFE_API_KEY")
    if value:
        return value
    env_file = project / ".env.local"
    if env_file.is_symlink() or not env_file.is_file():
        return None
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
    descriptor = os.open(env_file, flags)
    try:
        info = os.fstat(descriptor)
        if not stat.S_ISREG(info.st_mode) or stat.S_IMODE(info.st_mode) & 0o077 or (hasattr(os, "getuid") and info.st_uid != os.getuid()):
            raise ValueError(".env.local must be an owner-only regular file")
        if info.st_size > 16_384:
            raise ValueError(".env.local is too large")
        with os.fdopen(descriptor, "r", encoding="utf-8") as handle:
            contents = handle.read(16_385)
        descriptor = -1
    finally:
        if descriptor >= 0:
            os.close(descriptor)
    for line in contents.splitlines():
        if line.startswith("TYPESAFE_API_KEY="):
            return line.partition("=")[2].strip().strip('"\'') or None
    return None


def valid_candidates(packet: dict[str, object]) -> list[str]:
    mode = str(packet.get("mode", "")).lower()
    if mode not in MODES:
        raise ValueError("unknown Astral mode")
    if mode in {"comet", "singularity"} or packet.get("permission_to_delegate") is not True or packet.get("acceptance_settled") is not True:
        return []
    native_v2 = packet.get("native_v2")
    if not isinstance(native_v2, bool):
        raise ValueError("native_v2 must reflect observed host controls")
    if mode == "hypernova" and not native_v2:
        return []
    available = packet.get("available_models")
    if not isinstance(available, list) or any(not isinstance(x, str) for x in available):
        raise ValueError("available_models must be an observed model list")
    selected = packet.get("explicit_model")
    if selected is not None and selected not in ROUTES:
        raise ValueError("explicit_model is not an Astral route")
    defaults = ("gpt-6-sol", "gpt-6-astra") if mode == "hypernova" else ("gpt-6-luna", "gpt-6-sol", "gpt-6-astra")
    models = (selected,) if selected else defaults
    if not native_v2:
        models = tuple(model for model in models if model in {"gpt-6-luna", "gpt-6-sol", "gpt-5.6-luna", "gpt-5.6-terra"})
    host_efforts = packet.get("available_efforts")
    if host_efforts is not None and not isinstance(host_efforts, dict):
        raise ValueError("available_efforts must be a model-to-efforts map")
    return [model for model in models if model in available and (
        host_efforts is None or model not in host_efforts or
        (isinstance(host_efforts[model], list) and any(value in ROUTES[model]["efforts"] for value in host_efforts[model]))
    )]


def typesafe_request(summary: str, candidates: list[str], key: str, timeout: float = 10) -> dict[str, object]:
    criteria = {model: ROUTES[model]["description"] for model in candidates}
    criteria["primary"] = "Requirements, architecture, safety boundary, or acceptance still need the primary session"
    request = {
        "model": "jev-latest",
        "state": {"task": summary, "eligible_worker_models": candidates},
        "questions": {
            "worker": {"type": "choice", "instructions": "Choose the most cost-effective valid worker model for the bounded task, or primary if no worker should be assigned. Only choose among the listed eligible models.", "criteria": criteria},
            "difficulty": {"type": "score", "instructions": "How much reasoning effort does the bounded implementation need?", "criteria": ["Mechanical with exact steps", "Moderate repository context or debugging", "Difficult cross-component diagnosis or synthesis"]},
        },
    }
    body = json.dumps(request).encode("utf-8")
    http = urllib.request.Request(ENDPOINT, data=body, headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(http, timeout=timeout) as response:
        return json.load(response)


def decide(packet: dict[str, object], project: Path, *, response: dict[str, object] | None = None) -> dict[str, object]:
    candidates = valid_candidates(packet)
    if not candidates:
        return {"status": "blocked", "reason": "no-eligible-worker-route", "candidates": []}
    explicit_model = packet.get("explicit_model")
    explicit_effort = packet.get("explicit_effort")
    if explicit_effort is not None and explicit_model is None:
        raise ValueError("explicit_effort requires explicit_model")
    if explicit_model is not None:
        default = ROUTES[explicit_model]
        effort = explicit_effort or ("max" if packet["mode"].lower() == "hypernova" and explicit_model == "gpt-6-sol" else default["default_effort"])
        if effort not in default["efforts"]:
            raise ValueError("requested effort is unsupported by the selected model")
        host_efforts = packet.get("available_efforts")
        if isinstance(host_efforts, dict) and explicit_model in host_efforts and effort not in host_efforts[explicit_model]:
            return {"status": "blocked", "reason": "effort-unavailable", "model": explicit_model, "effort": effort}
        if not packet["native_v2"]:
            configured = packet.get("configured_efforts", {})
            if not isinstance(configured, dict):
                raise ValueError("configured_efforts must be a model-to-effort map")
            if effort != configured.get(explicit_model, default["default_effort"]):
                return {"status": "blocked", "reason": "launcher-effort-mismatch", "model": explicit_model, "effort": effort}
        return {"status": "selected", "source": "explicit", "model": explicit_model, "effort": effort, "role": default["role"]}
    session_id = packet.get("session_id")
    if not isinstance(session_id, str):
        raise ValueError("session_id is required")
    if session_mode(session_id, project) != "on":
        return {"status": "manual", "reason": "typesafe-off", "candidates": candidates}
    if response is None:
        if packet.get("allow_external_judgment") is not True:
            return {"status": "blocked", "reason": "external-judgment-not-authorized", "candidates": candidates}
        key = project_key(project)
        if not key:
            return {"status": "blocked", "reason": "typesafe-key-missing", "candidates": candidates}
        summary = packet.get("safe_summary")
        if not isinstance(summary, str) or not 1 <= len(summary) <= 2000:
            raise ValueError("safe_summary must contain 1 to 2000 non-sensitive characters")
        try:
            response = typesafe_request(summary, candidates, key)
        except (urllib.error.URLError, TimeoutError, ValueError) as error:
            return {"status": "blocked", "reason": "typesafe-call-failed", "detail": type(error).__name__, "candidates": candidates}
    answers = response.get("answers") if isinstance(response, dict) else None
    choice = answers.get("worker") if isinstance(answers, dict) else None
    difficulty = answers.get("difficulty") if isinstance(answers, dict) else None
    if not isinstance(choice, dict) or choice.get("type") != "choice" or choice.get("choice") not in [*candidates, "primary"]:
        return {"status": "blocked", "reason": "invalid-jev-choice", "candidates": candidates}
    confidence = choice.get("confidence")
    if isinstance(confidence, bool) or not isinstance(confidence, (int, float)) or not 0 <= confidence <= 1:
        return {"status": "blocked", "reason": "invalid-jev-confidence", "candidates": candidates}
    if confidence < 0.25:
        return {"status": "manual", "reason": "uncertain-jev-choice", "candidates": candidates}
    model = choice["choice"]
    if model == "primary":
        return {"status": "manual", "reason": "jev-kept-primary", "candidates": candidates}
    info = ROUTES[model]
    effort = info["default_effort"]
    if packet["mode"].lower() == "hypernova":
        if model == "gpt-6-sol":
            effort = "max"
    elif isinstance(difficulty, dict) and difficulty.get("type") == "score" and isinstance(difficulty.get("score"), (int, float)) and not isinstance(difficulty.get("score"), bool) and isinstance(difficulty.get("confidence"), (int, float)) and not isinstance(difficulty.get("confidence"), bool) and 0.25 <= difficulty["confidence"] <= 1:
        score = difficulty["score"]
        if 0 <= score <= 2:
            effort = info["efforts"][0 if score < 0.5 else (2 if score >= 1.5 else 1)] if len(info["efforts"]) == 3 else info["default_effort"]
    if not packet["native_v2"]:
        configured = packet.get("configured_efforts", {})
        if not isinstance(configured, dict):
            raise ValueError("configured_efforts must be a model-to-effort map")
        effort = configured.get(model, info["default_effort"])
        if effort not in info["efforts"]:
            raise ValueError("legacy launcher effort is unsupported by selected model")
    host_efforts = packet.get("available_efforts")
    if isinstance(host_efforts, dict) and model in host_efforts and effort not in host_efforts[model]:
        return {"status": "blocked", "reason": "effort-unavailable", "model": model, "effort": effort}
    return {"status": "selected", "source": "jev", "model": model, "effort": effort, "role": info["role"], "confidence": choice["confidence"]}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", type=Path, required=True)
    parser.add_argument("--input-file", type=Path, required=True)
    args = parser.parse_args()
    try:
        packet = json.loads(args.input_file.read_text(encoding="utf-8"))
        if not isinstance(packet, dict):
            raise ValueError("input must be a JSON object")
        result = decide(packet, args.project_root.resolve())
        print(json.dumps(result, separators=(",", ":"), sort_keys=True))
        return 0 if result["status"] in {"selected", "manual"} else 1
    except (OSError, ValueError, json.JSONDecodeError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
