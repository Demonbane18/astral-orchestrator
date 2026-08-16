"""Read and write Astral Orchestrator reasoning-effort settings."""

from __future__ import annotations

import os
import tempfile
import tomllib
from pathlib import Path


LANES = ("orchestrator", "luna", "terra", "reviewer")
ALLOWED_EFFORTS = ("minimal", "low", "medium", "high", "xhigh", "max", "ultra")
DEFAULT_EFFORTS = {
    "orchestrator": "high",
    "luna": "max",
    "terra": "high",
    "reviewer": "high",
}
MAX_SETTINGS_BYTES = 16_384


class EffortSettingsError(ValueError):
    """Raised when an effort settings file is unsafe or invalid."""


def default_settings_path() -> Path:
    """Return the persistent settings path without requiring a custom environment."""
    configured_home = os.environ.get("CODEX_HOME")
    codex_home = (
        Path(configured_home).expanduser()
        if configured_home
        else Path.home() / ".codex"
    )
    return codex_home / "astral-orchestrator" / "effort-levels.toml"


def _validate_efforts(efforts: dict[str, object]) -> dict[str, str]:
    unknown = sorted(set(efforts) - set(LANES))
    if unknown:
        raise EffortSettingsError(f"unknown effort lane: {', '.join(unknown)}")

    validated = dict(DEFAULT_EFFORTS)
    for lane, value in efforts.items():
        if not isinstance(value, str) or value not in ALLOWED_EFFORTS:
            rendered = value if isinstance(value, str) else type(value).__name__
            raise EffortSettingsError(
                f"unsupported effort for {lane}: {rendered}; choose from "
                + ", ".join(ALLOWED_EFFORTS)
            )
        validated[lane] = value
    return validated


def load_efforts(path: Path | None = None) -> tuple[dict[str, str], bool]:
    """Load effective settings and report whether a settings file supplied them."""
    settings_path = path or default_settings_path()
    if settings_path.is_symlink():
        raise EffortSettingsError(
            f"effort settings must be a real regular file: {settings_path}"
        )
    if not settings_path.exists():
        return dict(DEFAULT_EFFORTS), False
    if not settings_path.is_file():
        raise EffortSettingsError(
            f"effort settings must be a real regular file: {settings_path}"
        )
    if settings_path.stat().st_size > MAX_SETTINGS_BYTES:
        raise EffortSettingsError(
            f"effort settings exceed {MAX_SETTINGS_BYTES} bytes: {settings_path}"
        )

    try:
        with settings_path.open("rb") as handle:
            document = tomllib.load(handle)
    except (OSError, tomllib.TOMLDecodeError) as error:
        raise EffortSettingsError(f"could not read effort settings: {error}") from error

    unknown_sections = sorted(set(document) - {"effort"})
    if unknown_sections:
        raise EffortSettingsError(
            f"unknown settings section: {', '.join(unknown_sections)}"
        )
    effort_table = document.get("effort")
    if not isinstance(effort_table, dict):
        raise EffortSettingsError("effort settings must contain an [effort] table")
    return _validate_efforts(effort_table), True


def save_efforts(efforts: dict[str, object], path: Path | None = None) -> Path:
    """Atomically save a complete, validated settings file."""
    settings_path = path or default_settings_path()
    validated = _validate_efforts(efforts)

    if settings_path.is_symlink():
        raise EffortSettingsError(
            f"will not overwrite a symbolic-link settings file: {settings_path}"
        )
    if settings_path.exists() and not settings_path.is_file():
        raise EffortSettingsError(
            f"effort settings path is not a regular file: {settings_path}"
        )

    try:
        settings_path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        if settings_path.parent.is_symlink() or not settings_path.parent.is_dir():
            raise EffortSettingsError(
                f"effort settings folder must be a real directory: {settings_path.parent}"
            )

        lines = ["[effort]"]
        lines.extend(f'{lane} = "{validated[lane]}"' for lane in LANES)
        contents = "\n".join(lines) + "\n"

        temporary_name: str | None = None
        try:
            with tempfile.NamedTemporaryFile(
                "w",
                encoding="utf-8",
                dir=settings_path.parent,
                prefix=".effort-levels.",
                suffix=".tmp",
                delete=False,
            ) as handle:
                temporary_name = handle.name
                handle.write(contents)
                handle.flush()
                os.fsync(handle.fileno())
            os.chmod(temporary_name, 0o600)
            os.replace(temporary_name, settings_path)
        finally:
            if temporary_name and os.path.exists(temporary_name):
                os.unlink(temporary_name)
    except EffortSettingsError:
        raise
    except OSError as error:
        raise EffortSettingsError(f"could not save effort settings: {error}") from error

    return settings_path
