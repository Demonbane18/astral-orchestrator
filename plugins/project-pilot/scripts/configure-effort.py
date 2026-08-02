#!/usr/bin/env python3
"""Show or change Project Pilot reasoning-effort settings."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import NoReturn

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from effort_settings import (  # noqa: E402
    ALLOWED_EFFORTS,
    DEFAULT_EFFORTS,
    LANES,
    EffortSettingsError,
    default_settings_path,
    load_efforts,
    save_efforts,
)


def fail(message: str) -> NoReturn:
    print(f"ERROR: {message}", file=sys.stderr)
    raise SystemExit(1)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Show or change Project Pilot effort levels."
    )
    parser.add_argument(
        "--settings-file",
        type=Path,
        default=default_settings_path(),
        help=argparse.SUPPRESS,
    )
    parser.add_argument(
        "--show",
        action="store_true",
        help="Show the current effective settings without changing them.",
    )
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Restore all four effort levels to Project Pilot defaults.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable output.",
    )
    for lane in LANES:
        parser.add_argument(
            f"--{lane}",
            choices=ALLOWED_EFFORTS,
            help=f"Set the {lane} effort level.",
        )
    return parser.parse_args()


def print_result(
    efforts: dict[str, str],
    settings_path: Path,
    *,
    file_present: bool,
    changed: bool,
    as_json: bool,
) -> None:
    if as_json:
        print(
            json.dumps(
                {
                    "changed": changed,
                    "effort": efforts,
                    "settings_file": str(settings_path),
                    "settings_file_present": file_present,
                },
                separators=(",", ":"),
                sort_keys=True,
            )
        )
        return

    heading = "Project Pilot effort levels"
    print(f"{heading} ({'saved' if file_present else 'defaults'}):")
    for lane in LANES:
        default_note = " (default)" if efforts[lane] == DEFAULT_EFFORTS[lane] else ""
        print(f"  {lane.capitalize()}: {efforts[lane]}{default_note}")
    print(f"Settings file: {settings_path}")
    if any(value in {"max", "ultra"} for value in efforts.values()):
        print("Note: max and ultra are model- and account-dependent.")


def main() -> int:
    if sys.version_info < (3, 11):
        fail("Python 3.11 or newer is required.")

    args = parse_args()
    requested = {
        lane: getattr(args, lane)
        for lane in LANES
        if getattr(args, lane) is not None
    }
    if args.reset and requested:
        fail("--reset cannot be combined with individual lane changes")
    if args.show and (args.reset or requested):
        fail("--show cannot be combined with changes")

    try:
        efforts, file_present = load_efforts(args.settings_file)
        changed = False
        if args.reset:
            efforts = dict(DEFAULT_EFFORTS)
            save_efforts(efforts, args.settings_file)
            file_present = True
            changed = True
        elif requested:
            efforts.update(requested)
            save_efforts(efforts, args.settings_file)
            file_present = True
            changed = True
    except EffortSettingsError as error:
        fail(str(error))

    print_result(
        efforts,
        args.settings_file,
        file_present=file_present,
        changed=changed,
        as_json=args.json,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
