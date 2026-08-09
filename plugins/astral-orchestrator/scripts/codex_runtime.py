#!/usr/bin/env python3
"""Select a Codex executable that can parse the active user configuration."""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
import unicodedata
from pathlib import Path, PureWindowsPath
from typing import Callable, Mapping, NamedTuple, Sequence


DEFAULT_PROBE_TIMEOUT = 5.0
MAX_CANDIDATES = 12


class RuntimeCandidate(NamedTuple):
    source: str
    path: str


class CodexRuntime(NamedTuple):
    path: str
    source: str
    version: str
    config_probe: str


class RuntimeResolutionError(RuntimeError):
    """Raised when no candidate can parse the active Codex configuration."""


def _candidate(source: str, path: object) -> RuntimeCandidate:
    return RuntimeCandidate(source, str(path))


def runtime_candidates(
    *,
    platform_name: str | None = None,
    environ: Mapping[str, str] | None = None,
    home: Path | None = None,
    which: Callable[[str], str | None] | None = None,
) -> tuple[RuntimeCandidate, ...]:
    """Return a small, ordered set of explicit, host, known, and PATH candidates."""

    platform_name = (platform_name or sys.platform).lower()
    environ = os.environ if environ is None else environ
    home = Path.home() if home is None else home
    which = shutil.which if which is None else which
    candidates: list[RuntimeCandidate] = []

    if environ.get("ASTRAL_CODEX_PATH"):
        candidates.append(
            _candidate("astral-override", environ["ASTRAL_CODEX_PATH"])
        )
    if environ.get("CODEX_CLI_PATH"):
        candidates.append(_candidate("host-runtime", environ["CODEX_CLI_PATH"]))

    if platform_name in {"darwin", "macos"}:
        for applications in (Path("/Applications"), home / "Applications"):
            candidates.extend(
                (
                    _candidate(
                        "chatgpt-app",
                        applications / "ChatGPT.app/Contents/Resources/codex",
                    ),
                    _candidate(
                        "codex-app",
                        applications / "Codex.app/Contents/Resources/codex",
                    ),
                )
            )
    elif platform_name in {"windows", "win32", "cygwin"}:
        local_app_data = environ.get("LOCALAPPDATA")
        program_files = environ.get("ProgramFiles") or environ.get("PROGRAMFILES")
        if local_app_data:
            root = PureWindowsPath(local_app_data)
            candidates.extend(
                (
                    _candidate(
                        "codex-app",
                        root / "Programs/OpenAI/Codex/bin/codex.exe",
                    ),
                    _candidate(
                        "codex-app", root / "OpenAI/Codex/bin/codex.exe"
                    ),
                )
            )
        if program_files:
            candidates.append(
                _candidate(
                    "codex-app",
                    PureWindowsPath(program_files)
                    / "OpenAI/Codex/bin/codex.exe",
                )
            )
    elif platform_name.startswith("linux"):
        candidates.extend(
            (
                _candidate(
                    "standalone-runtime",
                    home / ".codex/packages/standalone/current/bin/codex",
                ),
                _candidate("standalone-runtime", home / ".local/bin/codex"),
                _candidate("standalone-runtime", "/usr/local/bin/codex"),
                _candidate("standalone-runtime", "/usr/bin/codex"),
            )
        )

    path_candidate = which("codex")
    if path_candidate:
        candidates.append(_candidate("path", path_candidate))
    return tuple(candidates[:MAX_CANDIDATES])


def _has_control_characters(value: str) -> bool:
    return any(unicodedata.category(character) == "Cc" for character in value)


def _validated_path(candidate: RuntimeCandidate) -> tuple[Path | None, str | None]:
    raw_path = candidate.path
    if not raw_path or _has_control_characters(raw_path):
        return None, "invalid path"

    path = Path(raw_path)
    if not path.is_absolute():
        return None, "path is not absolute"
    try:
        resolved = path.resolve(strict=True)
    except (OSError, RuntimeError, ValueError):
        return None, "path is unavailable"

    if _has_control_characters(str(resolved)):
        return None, "invalid resolved path"
    try:
        if not resolved.is_file():
            return None, "path is not a regular file"
        if not os.access(resolved, os.X_OK):
            return None, "path is not executable"
    except OSError:
        return None, "path could not be inspected"
    return resolved, None


def _runtime_version(
    path: Path,
    runner: Callable[..., subprocess.CompletedProcess[str]],
    timeout: float,
) -> str:
    try:
        result = runner(
            [str(path), "--version"],
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return "unavailable"
    if result.returncode != 0 or not isinstance(result.stdout, str):
        return "unavailable"

    version = result.stdout.strip()
    if re.fullmatch(r"codex(?:-cli)? v?[0-9][0-9A-Za-z.+_-]{0,63}", version):
        return version
    return "unavailable"


def _failure_message(failures: Sequence[str]) -> str:
    details = "; ".join(failures) if failures else "no candidates were available"
    return f"no compatible Codex runtime ({details})"


def resolve_codex_runtime(
    *,
    platform_name: str | None = None,
    environ: Mapping[str, str] | None = None,
    home: Path | None = None,
    which: Callable[[str], str | None] | None = None,
    runner: Callable[..., subprocess.CompletedProcess[str]] | None = None,
    timeout: float = DEFAULT_PROBE_TIMEOUT,
) -> CodexRuntime:
    """Select the first candidate whose feature probe parses the active config."""

    if timeout <= 0:
        raise ValueError("probe timeout must be positive")
    runner = subprocess.run if runner is None else runner
    failures: list[str] = []
    seen_paths: set[str] = set()

    for candidate in runtime_candidates(
        platform_name=platform_name,
        environ=environ,
        home=home,
        which=which,
    ):
        path, validation_error = _validated_path(candidate)
        if path is None:
            failures.append(f"{candidate.source}: {validation_error}")
            continue

        identity = os.path.normcase(str(path))
        if identity in seen_paths:
            continue
        seen_paths.add(identity)

        try:
            probe = runner(
                [str(path), "features", "list"],
                capture_output=True,
                text=True,
                timeout=timeout,
                check=False,
            )
        except subprocess.TimeoutExpired:
            failures.append(f"{candidate.source}: probe timeout")
            continue
        except OSError:
            failures.append(f"{candidate.source}: probe could not start")
            continue

        if probe.returncode != 0:
            failures.append(
                f"{candidate.source}: probe exited {probe.returncode}"
            )
            continue

        return CodexRuntime(
            path=str(path),
            source=candidate.source,
            version=_runtime_version(path, runner, timeout),
            config_probe="pass",
        )

    raise RuntimeResolutionError(_failure_message(failures))
