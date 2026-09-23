#!/usr/bin/env python3
"""Report Ares compatibility without changing the running Codex primary."""

from __future__ import annotations

import argparse
import json
import os
import stat
from pathlib import Path

SELECTIONS = {"Astra-Jev": "gpt-6-astra", "Sol-Jev": "gpt-6-sol", "Luna-Jev": "gpt-6-luna"}
EFFORTS = {"low", "medium", "high", "xhigh", "max", "ultra"}


def inspect(selection: str, observed_model: str, observed_effort: str,
            adaptive_provider: str | None, config_path: Path, socket: str | None) -> dict[str, str]:
    if not socket:
        return {"status": "inactive", "reason": "ares-checkpoint-not-observed"}
    socket_path = Path(socket)
    if not socket_path.is_absolute() or socket_path.is_symlink() or not socket_path.exists():
        return {"status": "blocked", "reason": "ares-checkpoint-unavailable"}
    socket_info = socket_path.stat()
    if not stat.S_ISSOCK(socket_info.st_mode) or stat.S_IMODE(socket_info.st_mode) & 0o077 or (hasattr(os, "getuid") and socket_info.st_uid != os.getuid()):
        return {"status": "blocked", "reason": "ares-checkpoint-unsafe"}
    if selection not in SELECTIONS:
        return {"status": "blocked", "reason": "unknown-ares-selection"}
    if observed_model != SELECTIONS[selection] or observed_effort not in EFFORTS:
        return {"status": "blocked", "reason": "primary-route-mismatch"}
    if observed_model != "gpt-6-astra" and observed_effort == "ultra":
        return {"status": "blocked", "reason": "primary-effort-unsupported"}
    if config_path.is_symlink() or not config_path.is_file():
        return {"status": "blocked", "reason": "ares-config-unavailable"}
    info = config_path.stat()
    if not stat.S_ISREG(info.st_mode) or stat.S_IMODE(info.st_mode) & 0o077 or info.st_size > 100_000:
        return {"status": "blocked", "reason": "ares-config-unsafe"}
    try:
        config = json.loads(config_path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {"status": "blocked", "reason": "ares-config-invalid"}
    provider = config.get("provider", "openrouter") if isinstance(config, dict) else None
    if provider not in {"typesafe", "openrouter", "vercel"}:
        return {"status": "blocked", "reason": "ares-provider-invalid"}
    if adaptive_provider and adaptive_provider != provider:
        return {"status": "blocked", "reason": "ares-provider-mismatch", "ares_provider": provider,
                "adaptive_provider": adaptive_provider}
    return {"status": "compatible", "selection": selection, "model": observed_model,
            "effort": observed_effort, "provider": provider,
            "evidence": "private-checkpoint-socket-and-observed-primary; native-effort-application-unverified"}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--selection", required=True)
    parser.add_argument("--observed-model", required=True)
    parser.add_argument("--observed-effort", required=True)
    parser.add_argument("--adaptive-provider", choices=["typesafe", "openrouter"])
    parser.add_argument("--config-path", type=Path, default=Path(os.environ.get("ARES_CONFIG", Path.home() / ".config/astra-ares/config.json")))
    args = parser.parse_args()
    result = inspect(args.selection, args.observed_model, args.observed_effort,
                     args.adaptive_provider, args.config_path, os.environ.get("CODEX_STEP_CONTROLLER_SOCKET"))
    print(json.dumps(result, separators=(",", ":"), sort_keys=True))
    return 0 if result["status"] in {"inactive", "compatible"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
