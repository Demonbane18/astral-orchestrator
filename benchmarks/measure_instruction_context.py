#!/usr/bin/env python3
"""Measure the published Astral instruction files with a pinned contributor tokenizer."""

from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
from pathlib import Path

import tiktoken


ROOT = Path(__file__).resolve().parents[1]
MEASURED_ON = "2026-08-21"
PRODUCT_VERSION = "3.6.0"
TOKENIZER_VERSION = "0.13.0"
TOKENIZER_ENCODING = "o200k_base"
PATHS = (
    Path("plugins/astral-orchestrator/skills/astral-orchestrator/SKILL.md"),
    Path("plugins/astral-orchestrator/skills/astral-orchestrator/references/modes-and-risk.md"),
    Path("plugins/astral-orchestrator/skills/astral-orchestrator/references/work-templates.md"),
    Path("plugins/astral-orchestrator/skills/astral-orchestrator/references/routing-and-preflight.md"),
    Path("plugins/astral-orchestrator/skills/astral-orchestrator/references/pulsar-mode.md"),
)


def measurement() -> dict[str, object]:
    """Return the stable, audit-friendly measurement for the published instruction files."""
    version = importlib.metadata.version("tiktoken")
    if version != TOKENIZER_VERSION:
        raise RuntimeError(
            f"tiktoken {TOKENIZER_VERSION} is required; found {version}. "
            "Use the documented uv command."
        )

    encoder = tiktoken.get_encoding(TOKENIZER_ENCODING)
    files = []
    for relative_path in PATHS:
        data = (ROOT / relative_path).read_bytes()
        text = data.decode("utf-8")
        files.append(
            {
                "path": relative_path.as_posix(),
                "bytes": len(data),
                "words": len(text.split()),
                "tokens": len(encoder.encode(text)),
                "sha256": hashlib.sha256(data).hexdigest(),
            }
        )

    core, modes, templates, routing, pulsar = files
    # Comet uses only the core skill and its mode/risk rules. Work templates and
    # routing/preflight remain progressive disclosures for broader routes.
    quick_files = (core, modes)
    quick_tokens = sum(item["tokens"] for item in quick_files)
    full_files = (core, modes, templates, routing)
    full_tokens = sum(item["tokens"] for item in full_files)
    pulsar_tokens = sum(item["tokens"] for item in files)
    avoided = full_tokens - quick_tokens
    return {
        "schema_version": 1,
        "measurement": "instruction-context-footprint",
        "measured_on": MEASURED_ON,
        "product_version": PRODUCT_VERSION,
        "generated_by": "benchmarks/measure_instruction_context.py",
        "command": (
            "uv run --no-project --with tiktoken==0.13.0 python "
            "benchmarks/measure_instruction_context.py"
        ),
        "tokenizer": {
            "library": "tiktoken",
            "version": TOKENIZER_VERSION,
            "encoding": TOKENIZER_ENCODING,
        },
        "counting": {
            "bytes": "UTF-8 byte length",
            "words": "whitespace-separated UTF-8 text segments",
            "tokens": "tiktoken encoding of the complete UTF-8 text",
        },
        "files": files,
        "bundles": {
            "core": {
                "paths": [core["path"]],
                "tokens": core["tokens"],
            },
            "quick": {
                "paths": [item["path"] for item in quick_files],
                "tokens": quick_tokens,
            },
            "full": {
                "paths": [item["path"] for item in full_files],
                "tokens": full_tokens,
            },
            "guided": {
                "paths": [item["path"] for item in full_files],
                "tokens": full_tokens,
            },
            "measured": {
                "paths": [item["path"] for item in files],
                "tokens": pulsar_tokens,
            },
        },
        "quick_vs_full": {
            "tokens_avoided": avoided,
            "percent_avoided": round(avoided / full_tokens * 100, 1),
        },
        "scope_note": (
            "This measures instruction-context loading only. It does not measure "
            "outcome quality, latency, price, or total tokens for a complete run."
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        type=Path,
        metavar="EVIDENCE_JSON",
        help="verify an existing JSON evidence file instead of printing the measurement",
    )
    args = parser.parse_args()
    result = measurement()

    if args.check:
        expected = json.loads(args.check.read_text(encoding="utf-8"))
        if expected != result:
            raise SystemExit(
                f"{args.check} does not match the current instruction-context measurement"
            )
        print(f"instruction-context evidence matches: {args.check}")
        return 0

    print(json.dumps(result, indent=2) + "\n", end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
