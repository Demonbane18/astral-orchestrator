#!/usr/bin/env python3
"""Append and reconcile evidence-backed Astral Orchestrator release events."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import tempfile
from pathlib import Path
from typing import Any


SURFACES = (
    "source",
    "github_release",
    "github_marketplace",
    "vercel",
    "openai_submission",
    "openai_directory",
)

STATUSES = (
    "draft",
    "verified",
    "submitted",
    "approved",
    "published",
    "installable",
    "deployed",
    "failed",
    "superseded",
)

FINAL_STATUS = {
    "source": "verified",
    "github_release": "published",
    "github_marketplace": "installable",
    "vercel": "deployed",
    "openai_directory": "published",
}

ALLOWED_STATUS = {
    "source": {"draft", "verified", "failed", "superseded"},
    "github_release": {"draft", "published", "failed", "superseded"},
    "github_marketplace": {"verified", "installable", "failed", "superseded"},
    "vercel": {"draft", "deployed", "failed", "superseded"},
    "openai_submission": {"draft", "submitted", "approved", "failed", "superseded"},
    "openai_directory": {"published", "failed", "superseded"},
}

SEMVER = re.compile(r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)(?:-[0-9A-Za-z.-]+)?(?:\+[0-9A-Za-z.-]+)?$")
RFC3339 = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})$")


class LedgerError(ValueError):
    """Raised when release-ledger data is invalid."""


def load_ledger(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as error:
        raise LedgerError(f"ledger does not exist: {path}") from error
    except json.JSONDecodeError as error:
        raise LedgerError(f"ledger is not valid JSON: {error}") from error
    validate_ledger(data)
    return data


def validate_ledger(data: Any) -> None:
    if not isinstance(data, dict):
        raise LedgerError("ledger root must be an object")
    if data.get("schema_version") != 1:
        raise LedgerError("schema_version must be 1")
    if data.get("product") != "Astral Orchestrator":
        raise LedgerError("product must be Astral Orchestrator")
    events = data.get("events")
    if not isinstance(events, list):
        raise LedgerError("events must be an array")
    for index, event in enumerate(events):
        validate_event(event, index)


def validate_event(event: Any, index: int | None = None) -> None:
    label = f"event {index}" if index is not None else "event"
    if not isinstance(event, dict):
        raise LedgerError(f"{label} must be an object")
    required = ("surface", "version", "status", "observed_at", "evidence")
    missing = [key for key in required if not event.get(key)]
    if missing:
        raise LedgerError(f"{label} is missing: {', '.join(missing)}")
    if event["surface"] not in SURFACES:
        raise LedgerError(f"{label} has unknown surface: {event['surface']}")
    if event["status"] not in STATUSES:
        raise LedgerError(f"{label} has unknown status: {event['status']}")
    if event["status"] not in ALLOWED_STATUS[event["surface"]]:
        raise LedgerError(
            f"{label} status {event['status']} is invalid for {event['surface']}"
        )
    if not isinstance(event["version"], str) or not SEMVER.fullmatch(event["version"]):
        raise LedgerError(f"{label} version is not semantic versioning: {event['version']}")
    if not isinstance(event["observed_at"], str) or not RFC3339.fullmatch(event["observed_at"]):
        raise LedgerError(f"{label} observed_at must be RFC 3339 with a timezone")
    if not isinstance(event["evidence"], str):
        raise LedgerError(f"{label} evidence must be a string")
    for optional in ("url", "commit"):
        if optional in event and not isinstance(event[optional], str):
            raise LedgerError(f"{label} {optional} must be a string")


def atomic_write(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    handle, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(handle, "w", encoding="utf-8") as stream:
            json.dump(data, stream, indent=2, ensure_ascii=False)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    except BaseException:
        try:
            os.unlink(temporary)
        except FileNotFoundError:
            pass
        raise


def latest_by_surface(data: dict[str, Any]) -> dict[str, dict[str, Any]]:
    latest: dict[str, dict[str, Any]] = {}
    for event in data["events"]:
        latest[event["surface"]] = event
    return latest


def record(args: argparse.Namespace) -> int:
    path = Path(args.ledger)
    data = load_ledger(path)
    event = {
        "surface": args.surface,
        "version": args.version,
        "status": args.status,
        "observed_at": args.observed_at,
        "evidence": args.evidence,
    }
    if args.url:
        event["url"] = args.url
    if args.commit:
        event["commit"] = args.commit
    validate_event(event)
    if event in data["events"]:
        print("Release event already recorded; ledger unchanged.")
        return 0
    data["events"].append(event)
    atomic_write(path, data)
    print(f"Recorded {args.surface} {args.version} as {args.status}.")
    return 0


def manifest_version(path: Path) -> str:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError) as error:
        raise LedgerError(f"cannot read plugin manifest: {path}: {error}") from error
    version = data.get("version")
    if not isinstance(version, str) or not SEMVER.fullmatch(version):
        raise LedgerError("plugin manifest version is missing or invalid")
    return version


def render_status(data: dict[str, Any], expected: str | None, output_format: str) -> str:
    latest = latest_by_surface(data)
    rows = []
    for surface in SURFACES:
        event = latest.get(surface)
        if event is None:
            rows.append((surface, "—", "unobserved", "—", "—"))
            continue
        relation = "—"
        if expected:
            relation = "match" if event["version"] == expected else "lag/mismatch"
        evidence = event.get("url") or event["evidence"]
        rows.append((surface, event["version"], event["status"], relation, evidence))
    if output_format == "json":
        payload = {
            "expected_version": expected,
            "surfaces": {
                surface: latest.get(surface) for surface in SURFACES
            },
        }
        return json.dumps(payload, indent=2, ensure_ascii=False)
    lines = [
        "| Surface | Version | Status | Target | Evidence |",
        "|---|---:|---|---|---|",
    ]
    for row in rows:
        escaped = [str(value).replace("|", "\\|") for value in row]
        lines.append("| " + " | ".join(escaped) + " |")
    return "\n".join(lines)


def status(args: argparse.Namespace) -> int:
    data = load_ledger(Path(args.ledger))
    if args.expected_version and not SEMVER.fullmatch(args.expected_version):
        raise LedgerError("expected version is not semantic versioning")
    print(render_status(data, args.expected_version, args.format))
    return 0


def check(args: argparse.Namespace) -> int:
    if not SEMVER.fullmatch(args.expected_version):
        raise LedgerError("expected version is not semantic versioning")
    data = load_ledger(Path(args.ledger))
    latest = latest_by_surface(data)
    errors: list[str] = []

    if args.manifest:
        actual = manifest_version(Path(args.manifest))
        if actual != args.expected_version:
            errors.append(
                f"manifest is {actual}; expected {args.expected_version}"
            )

    for surface, final_status in FINAL_STATUS.items():
        event = latest.get(surface)
        if event is None:
            errors.append(f"{surface} has no recorded evidence")
            continue
        if event["version"] != args.expected_version:
            errors.append(
                f"{surface} is {event['version']}; expected {args.expected_version}"
            )
        if event["status"] != final_status:
            errors.append(
                f"{surface} status is {event['status']}; expected {final_status}"
            )

    if errors:
        print("Release is not public on every required surface:", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1
    print(f"Astral Orchestrator {args.expected_version} is reconciled everywhere.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    record_parser = subparsers.add_parser("record", help="append an observed release event")
    record_parser.add_argument("--ledger", required=True)
    record_parser.add_argument("--surface", choices=SURFACES, required=True)
    record_parser.add_argument("--version", required=True)
    record_parser.add_argument("--status", choices=STATUSES, required=True)
    record_parser.add_argument("--observed-at", required=True)
    record_parser.add_argument("--evidence", required=True)
    record_parser.add_argument("--url")
    record_parser.add_argument("--commit")
    record_parser.set_defaults(handler=record)

    status_parser = subparsers.add_parser("status", help="show latest state by surface")
    status_parser.add_argument("--ledger", required=True)
    status_parser.add_argument("--expected-version")
    status_parser.add_argument("--format", choices=("markdown", "json"), default="markdown")
    status_parser.set_defaults(handler=status)

    check_parser = subparsers.add_parser("check", help="require a public, fully reconciled release")
    check_parser.add_argument("--ledger", required=True)
    check_parser.add_argument("--expected-version", required=True)
    check_parser.add_argument("--manifest")
    check_parser.set_defaults(handler=check)
    return parser


def main() -> int:
    try:
        args = build_parser().parse_args()
        return args.handler(args)
    except LedgerError as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
