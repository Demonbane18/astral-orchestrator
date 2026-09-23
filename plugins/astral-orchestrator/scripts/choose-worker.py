#!/usr/bin/env python3
"""Filter exact Astral worker routes, then optionally ask TypeSafe Jev to choose."""

from __future__ import annotations

import argparse
import json
import os
import re
import stat
import sys
import tomllib
import urllib.error
import urllib.request
from pathlib import Path

ENDPOINT = "https://api.typesafe.ai/v1/systemone"
OPENROUTER_ENDPOINT = "https://openrouter.ai/api/alpha/decisions"
SESSION_ID = re.compile(r"[A-Za-z0-9_-]{8,128}\Z")
ROUTES = {
    "gpt-6-luna": {"role": "focused", "default_effort": "max", "efforts": ["low", "medium", "high", "xhigh", "max"], "description": "bounded, repeatable implementation"},
    "gpt-6-sol": {"role": "context", "default_effort": "high", "efforts": ["low", "medium", "high", "xhigh", "max"], "description": "context-heavy implementation or debugging"},
    "gpt-6-astra": {"role": "deep", "default_effort": "medium", "efforts": ["low", "medium", "high", "xhigh", "max", "ultra"], "description": "difficult diagnosis or deep synthesis"},
    "gpt-5.6-luna": {"role": "legacy-focused", "default_effort": "max", "efforts": ["max"], "description": "explicit legacy focused route"},
    "gpt-5.6-terra": {"role": "legacy-context", "default_effort": "high", "efforts": ["high"], "description": "explicit legacy context route"},
    "gpt-5.6-sol": {"role": "legacy-sol", "default_effort": "high", "efforts": ["high", "ultra"], "description": "explicit legacy Sol route"},
}
MODES = {"orbit", "event horizon", "pulsar", "morph", "constellation", "hypernova", "comet", "singularity"}


def opencodex_catalog(packet: dict[str, object]) -> dict[str, list[str]] | None:
    if packet.get("transport") != "opencodex":
        return None
    home = Path(os.environ.get("CODEX_HOME", Path.home() / ".codex")).expanduser()
    config = home / "config.toml"
    if not config.is_file() or config.stat().st_size > 1_000_000:
        raise ValueError("active Codex configuration is unavailable")
    with config.open("rb") as handle:
        settings = tomllib.load(handle)
    raw_path = settings.get("model_catalog_json")
    if not isinstance(raw_path, str) or not raw_path:
        raise ValueError("active OpenCodex catalog is not configured")
    path = Path(raw_path).expanduser()
    if not path.is_absolute() or not path.is_file() or path.stat().st_size > 20_000_000:
        raise ValueError("active OpenCodex catalog is unavailable")
    data = json.loads(path.read_text(encoding="utf-8"))
    entries = data.get("models") if isinstance(data, dict) else None
    if not isinstance(entries, list):
        raise ValueError("active OpenCodex catalog is invalid")
    catalog = {}
    for item in entries:
        if not isinstance(item, dict) or not isinstance(item.get("slug"), str):
            continue
        levels = item.get("supported_reasoning_levels")
        if isinstance(levels, list):
            catalog[item["slug"]] = [level["effort"] for level in levels if isinstance(level, dict) and isinstance(level.get("effort"), str)]
    return catalog


def session_settings(session_id: str, project: Path) -> dict[str, str | None]:
    if not SESSION_ID.fullmatch(session_id):
        raise ValueError("invalid session id")
    home = Path(os.environ.get("CODEX_HOME", Path.home() / ".codex")).expanduser()
    path = home / "typesafe-session" / "sessions" / f"{session_id}.json"
    if path.is_symlink():
        raise ValueError("unsafe session state")
    if path.is_file():
        data = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(data, dict) and data.get("project") == str(project.resolve()) and data.get("mode") in {"on", "off"}:
            provider = data.get("adaptive_provider")
            adaptive = data.get("adaptive")
            if adaptive == "on" and provider in {"typesafe", "openrouter"}:
                return {"typesafe": data["mode"], "adaptive": "on", "provider": provider}
            return {"typesafe": data["mode"], "adaptive": "off", "provider": None}
    guide = project / "AGENTS.md"
    if guide.is_file() and not guide.is_symlink() and guide.stat().st_size <= 100_000:
        if "TypeSafe session: on" in guide.read_text(encoding="utf-8").splitlines():
            return {"typesafe": "on", "adaptive": "off", "provider": None}
    return {"typesafe": "off", "adaptive": "off", "provider": None}


def session_mode(session_id: str, project: Path) -> str:
    return str(session_settings(session_id, project)["typesafe"])


def project_key(project: Path, provider: str = "typesafe") -> str | None:
    if provider not in {"typesafe", "openrouter"}:
        raise ValueError("unknown Jev provider")
    variable = "TYPESAFE_API_KEY" if provider == "typesafe" else "OPENROUTER_API_KEY"
    value = os.environ.get(variable)
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
        if line.startswith(f"{variable}="):
            return line.partition("=")[2].strip().strip('"\'') or None
    return None


def valid_candidates(packet: dict[str, object]) -> list[str]:
    mode = str(packet.get("mode", "")).lower()
    if mode not in MODES:
        raise ValueError("unknown Astral mode")
    recommend_only = packet.get("recommend_only") is True and mode in {"comet", "singularity"}
    if mode in {"comet", "singularity"} and not recommend_only:
        return []
    if not recommend_only and (packet.get("permission_to_delegate") is not True or packet.get("acceptance_settled") is not True):
        return []
    native_v2 = packet.get("native_v2")
    if not isinstance(native_v2, bool):
        raise ValueError("native_v2 must reflect observed host controls")
    if mode == "hypernova" and not native_v2:
        return []
    available = packet.get("available_models")
    if not isinstance(available, list) or any(not isinstance(x, str) for x in available):
        raise ValueError("available_models must be an observed model list")
    catalog = opencodex_catalog(packet)
    selected = packet.get("explicit_model")
    if selected is not None and (not isinstance(selected, str) or selected not in ROUTES):
        raise ValueError("explicit_model is not an Astral route")
    if mode == "morph" and selected is None:
        return []
    explicit_effort = packet.get("explicit_effort")
    if explicit_effort is not None and (not isinstance(explicit_effort, str) or explicit_effort not in {"minimal", "low", "medium", "high", "xhigh", "max", "ultra"}):
        raise ValueError("explicit_effort is unsupported")
    if selected is not None and explicit_effort is not None and explicit_effort not in ROUTES[selected]["efforts"]:
        raise ValueError("requested effort is unsupported by the selected model")
    role = packet.get("role", "worker")
    if not isinstance(role, str) or role not in {"worker", "reviewer"}:
        raise ValueError("unknown worker role")
    defaults = ("gpt-6-sol",) if role == "reviewer" else (("gpt-6-sol", "gpt-6-astra") if mode == "hypernova" else ("gpt-6-luna", "gpt-6-sol", "gpt-6-astra"))
    if role == "reviewer" and selected not in {None, "gpt-6-sol"}:
        raise ValueError("reviewer route is fixed to gpt-6-sol")
    models = (selected,) if selected else defaults
    if not native_v2:
        models = tuple(model for model in models if model in {"gpt-6-luna", "gpt-6-sol", "gpt-5.6-luna", "gpt-5.6-terra"})
    host_efforts = packet.get("available_efforts")
    if host_efforts is not None and not isinstance(host_efforts, dict):
        raise ValueError("available_efforts must be a model-to-efforts map")
    return [model for model in models if model in available and (catalog is None or model in catalog) and (explicit_effort is None or explicit_effort in ROUTES[model]["efforts"]) and (
        host_efforts is None or model not in host_efforts or
        (isinstance(host_efforts[model], list) and any(value in ROUTES[model]["efforts"] for value in host_efforts[model]))
    )]


def typesafe_request(summary: str, candidates: list[str], key: str, timeout: float = 10,
                     *, provider: str = "typesafe", adaptive: bool = False,
                     effort_options: dict[str, list[str]] | None = None,
                     fixed_model: bool = False) -> dict[str, object]:
    if provider not in {"typesafe", "openrouter"}:
        raise ValueError("unknown Jev provider")
    criteria = {model: ROUTES[model]["description"] for model in candidates}
    criteria["primary"] = "Requirements, architecture, safety boundary, or acceptance still need the primary session"
    questions = {}
    if not fixed_model:
        questions["worker"] = {"type": "choice", "instructions": "Choose the most cost-effective valid worker model for the bounded task, or primary if no worker should be assigned. Only choose among the listed eligible models.", "criteria": criteria}
    if adaptive:
        questions["difficulty"] = {"type": "score", "instructions": "How much reasoning effort does this bounded task need?", "criteria": ["Mechanical with exact steps", "Moderate repository context or debugging", "Difficult cross-component diagnosis or synthesis"]}
    request = {
        "model": "jev-latest" if provider == "typesafe" else "typesafe/jev-1.13",
        "state": {"task": summary, "eligible_worker_models": candidates, "eligible_efforts": effort_options or {}},
        "questions": questions,
    }
    if provider == "openrouter":
        request["provider"] = {"only": ["typesafe"], "allow_fallbacks": False}
    body = json.dumps(request).encode("utf-8")
    endpoint = ENDPOINT if provider == "typesafe" else OPENROUTER_ENDPOINT
    http = urllib.request.Request(endpoint, data=body, headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json", "User-Agent": "Astral-Orchestrator/3.13.0"}, method="POST")
    with urllib.request.urlopen(http, timeout=timeout) as response:
        result = json.load(response)
    if not isinstance(result, dict):
        raise ValueError("Jev returned an invalid response")
    model = result.get("model")
    if provider == "openrouter":
        if not isinstance(model, str) or not re.fullmatch(r"typesafe/jev-1\.13(?:-\d{8})?", model) or result.get("provider") != "TypeSafe":
            raise ValueError("OpenRouter did not confirm the selected Jev provider")
    elif not isinstance(model, str) or not re.fullmatch(r"jev-(?:latest|\d+\.\d+(?:\.\d+)?)", model):
        raise ValueError("TypeSafe did not confirm a Jev model")
    return result


def decide(packet: dict[str, object], project: Path, *, response: dict[str, object] | None = None) -> dict[str, object]:
    mode = str(packet.get("mode", "")).lower()
    if mode not in MODES:
        raise ValueError("unknown Astral mode")
    if os.environ.get("CODEX_STEP_CONTROLLER_SOCKET") and mode not in {"comet", "singularity"}:
        return {"status": "blocked", "reason": "ares-single-agent-only", "candidates": []}
    candidates = valid_candidates(packet)
    if not candidates:
        return {"status": "blocked", "reason": "no-eligible-worker-route", "candidates": []}
    recommend_only = mode in {"comet", "singularity"} and packet.get("recommend_only") is True
    explicit_model = packet.get("explicit_model")
    explicit_effort = packet.get("explicit_effort")
    session_id = packet.get("session_id")
    if not isinstance(session_id, str):
        raise ValueError("session_id is required")
    settings = session_settings(session_id, project)
    adaptive = settings["adaptive"] == "on"
    if recommend_only and not adaptive:
        return {"status": "manual", "reason": "adaptive-off-no-recommendation", "candidates": candidates}
    if packet.get("role") == "reviewer":
        effort = "high"
        if explicit_effort not in {None, effort}:
            raise ValueError("reviewer effort is fixed to high")
        if effort not in allowed_efforts(packet, "gpt-6-sol"):
            return {"status": "blocked", "reason": "effort-unavailable", "model": "gpt-6-sol", "effort": effort}
        return {"status": "recommendation" if recommend_only else "selected", "source": "fixed-reviewer", "model": "gpt-6-sol", "effort": effort, "role": "reviewer"}
    if explicit_model is not None and explicit_effort is not None:
        if explicit_effort not in ROUTES[explicit_model]["efforts"]:
            raise ValueError("requested effort is unsupported by the selected model")
        if explicit_effort not in allowed_efforts(packet, explicit_model):
            return {"status": "blocked", "reason": "effort-unavailable", "model": explicit_model, "effort": explicit_effort}
        if not packet["native_v2"] and explicit_effort != configured_effort(packet, explicit_model):
            return {"status": "blocked", "reason": "launcher-effort-mismatch", "model": explicit_model, "effort": explicit_effort}
        return {"status": "recommendation" if recommend_only else "selected", "source": "explicit", "model": explicit_model, "effort": explicit_effort, "role": ROUTES[explicit_model]["role"]}
    if not adaptive and explicit_model is not None:
        effort = configured_effort(packet, explicit_model)
        if effort not in allowed_efforts(packet, explicit_model):
            return {"status": "blocked", "reason": "effort-unavailable", "model": explicit_model, "effort": effort}
        return {"status": "recommendation" if recommend_only else "selected", "source": "explicit", "model": explicit_model, "effort": effort, "role": ROUTES[explicit_model]["role"]}
    if not adaptive and settings["typesafe"] != "on":
        return {"status": "manual", "reason": "typesafe-off", "candidates": candidates}
    if adaptive and not packet["native_v2"]:
        return {"status": "blocked", "reason": "adaptive-effort-requires-native-v2", "candidates": candidates}
    provider = str(settings["provider"] or "typesafe")
    effort_options = {model: [value for value in allowed_efforts(packet, model, adaptive=adaptive and explicit_effort is None)
                              if (explicit_effort is None or value == explicit_effort)
                              and (adaptive or value == configured_effort(packet, model))] for model in candidates}
    candidates = [model for model in candidates if effort_options[model]]
    if not candidates:
        return {"status": "blocked", "reason": "no-eligible-effort", "candidates": []}
    if response is None:
        if packet.get("allow_external_judgment") is not True:
            return {"status": "blocked", "reason": "external-judgment-not-authorized", "candidates": candidates}
        key = project_key(project, provider)
        if not key:
            return {"status": "blocked", "reason": f"{provider}-key-missing", "candidates": candidates}
        summary = packet.get("safe_summary")
        if not isinstance(summary, str) or not 1 <= len(summary) <= 2000:
            raise ValueError("safe_summary must contain 1 to 2000 non-sensitive characters")
        try:
            response = typesafe_request(summary, candidates, key, provider=provider, adaptive=adaptive and explicit_effort is None,
                                        effort_options=effort_options, fixed_model=explicit_model is not None)
        except (urllib.error.URLError, TimeoutError, ValueError) as error:
            return {"status": "blocked", "reason": f"{provider}-call-failed", "detail": type(error).__name__, "candidates": candidates}
    answers = response.get("answers") if isinstance(response, dict) else None
    if not isinstance(answers, dict):
        return {"status": "blocked", "reason": "invalid-jev-answer", "candidates": candidates}
    choice = answers.get("worker")
    if explicit_model is None:
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
    else:
        model = explicit_model
        if model not in candidates:
            return {"status": "blocked", "reason": "no-eligible-worker-route", "candidates": candidates}
        confidence = None
    if adaptive and explicit_effort is None:
        difficulty = answers.get("difficulty")
        if not isinstance(difficulty, dict) or difficulty.get("type") != "score" or isinstance(difficulty.get("score"), bool) or not isinstance(difficulty.get("score"), (int, float)) or not 0 <= difficulty["score"] <= 2:
            return {"status": "blocked", "reason": "invalid-jev-score", "candidates": candidates}
        score_confidence = difficulty.get("confidence")
        if isinstance(score_confidence, bool) or not isinstance(score_confidence, (int, float)) or not 0 <= score_confidence <= 1:
            return {"status": "blocked", "reason": "invalid-jev-score-confidence", "candidates": candidates}
        if score_confidence < 0.25:
            return {"status": "manual", "reason": "uncertain-jev-score", "candidates": candidates}
        options = effort_options[model]
        effort = options[round(difficulty["score"] / 2 * (len(options) - 1))]
    elif explicit_effort is not None:
        effort = explicit_effort
    else:
        effort = configured_effort(packet, model)
        if effort not in effort_options[model]:
            return {"status": "blocked", "reason": "effort-unavailable", "model": model, "effort": effort}
    if not packet["native_v2"] and effort != configured_effort(packet, model):
        return {"status": "blocked", "reason": "launcher-effort-mismatch", "model": model, "effort": effort}
    result = {"status": "recommendation" if recommend_only else "selected", "source": "jev", "provider": provider,
              "model": model, "effort": effort, "role": ROUTES[model]["role"]}
    if confidence is not None:
        result["confidence"] = confidence
    return result


def configured_effort(packet: dict[str, object], model: str) -> str:
    configured = packet.get("configured_efforts", {})
    if not isinstance(configured, dict):
        raise ValueError("configured_efforts must be a model-to-effort map")
    default = "max" if str(packet["mode"]).lower() == "hypernova" and model == "gpt-6-sol" else ROUTES[model]["default_effort"]
    effort = configured.get(model, default)
    if effort not in ROUTES[model]["efforts"]:
        raise ValueError("configured effort is unsupported by selected model")
    return effort


def allowed_efforts(packet: dict[str, object], model: str, *, adaptive: bool = False) -> list[str]:
    host = packet.get("available_efforts")
    if host is not None and not isinstance(host, dict):
        raise ValueError("available_efforts must be a model-to-efforts map")
    values = ROUTES[model]["efforts"]
    if adaptive:
        values = [value for value in values if value != "ultra"]
    if isinstance(host, dict) and model in host:
        if not isinstance(host[model], list) or any(not isinstance(value, str) for value in host[model]):
            raise ValueError("available effort entries must be lists of strings")
        values = [value for value in values if value in host[model]]
    catalog = opencodex_catalog(packet)
    if catalog is not None:
        values = [value for value in values if value in catalog.get(model, [])]
    return values


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
        return 0 if result["status"] in {"selected", "manual", "recommendation"} else 1
    except (OSError, ValueError, json.JSONDecodeError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
