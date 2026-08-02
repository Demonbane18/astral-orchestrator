# Project Pilot tasks

## 1. Contract tests

- [x] Add tests before implementation.
  - Acceptance: tests cover plugin structure, plain-language modes, fallbacks,
    safety, docs, setup dry run, and MIT attribution.
  - Verify: `python3 -m unittest discover -s tests -v` fails only because the
    implementation files do not exist yet.
  - Files: `tests/test_project_pilot.py`

## 2. Plugin foundation

- [x] Scaffold the marketplace, plugin manifest, and skill metadata.
  - Acceptance: names and relative paths are consistent and contain no placeholders.
  - Verify: JSON parses and official validators can discover the package.
  - Files: `.agents/plugins/marketplace.json`, `plugins/project-pilot/**`
  - Dependencies: Task 1

## 3. Workflow

- [x] Implement Quick, Guided, and Careful execution with risk-based review.
  - Acceptance: no named model or custom-agent dependency; delegation is optional;
    requested independent review is never silently downgraded.
  - Verify: contract tests and skill validation pass.
  - Files: `plugins/project-pilot/skills/project-pilot/**`
  - Dependencies: Task 2

## 4. Helpers

- [x] Add deterministic verification and one-command local setup.
  - Acceptance: verification is dependency-free; setup has `--help` and `--dry-run`;
    neither path overwrites unrelated configuration.
  - Verify: shell syntax, dry run, and contract tests pass.
  - Files: `plugins/project-pilot/scripts/verify.sh`, `scripts/setup.sh`
  - Dependencies: Tasks 2–3

## 5. Documentation and attribution

- [x] Add beginner-first usage and sharing docs plus the design review.
  - Acceptance: README covers install, use, update, share, remove, troubleshooting;
    original MIT notice is preserved.
  - Verify: contract tests and a manual plain-language read-through pass.
  - Files: `README.md`, `LICENSE`, `NOTICE.md`, `docs/IMPROVEMENTS.md`
  - Dependencies: Tasks 2–4

## 6. Final validation

- [x] Run official validators and forward-test realistic usage.
  - Acceptance: all checks pass; forward tests expose no blocking ambiguity.
  - Verify: commands in `AGENTS.md` and `docs/SPEC.md` complete successfully.
  - Files: only targeted fixes found during validation
  - Dependencies: Tasks 1–5
