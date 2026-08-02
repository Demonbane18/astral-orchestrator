# Implementation Plan: Astral Orchestrator v3

## Goal

Deliver Astral Orchestrator as a shareable Codex marketplace plugin with Sol High in
charge, Luna XHigh and Terra XHigh implementation lanes, configurable reasoning effort,
strict route proof, and a fresh Sol High reviewer.

## Dependency order

~~~text
Rebrand contract tests
        |
Namespaced profiles and safe installer
        |
Strict routing and route evidence
        |
Beginner setup, configuration, removal, and documentation
        |
Validation
~~~

## Checkpoints

### Identity

- [x] Rename the product, plugin, marketplace, skill, profiles, and launcher evidence
  prefix to Astral Orchestrator.
- [x] Move persistent effort settings into the astral-orchestrator namespace.
- [x] Release v3.0.0 with a clear former-name migration note and real repository metadata.

### Runtime

- [x] Preserve namespaced Luna XHigh, Terra XHigh, and Sol High reviewer profiles.
- [x] Preserve conflict-safe install, exact-check, and safe-remove behavior.
- [x] Preserve allowlisted runtime evidence without an extra JSON package.
- [x] Preserve configurable effort settings and strict no-substitution routing.

### Handoff

- [x] Put Quick Install immediately near the README top and document the complete
  beginner journey.
- [x] Update specifications, attribution, comparison, and contributor guidance.
- [x] Run repository tests, package verification, setup dry-run, and whitespace checks.

## Risks

| Risk | Mitigation |
|---|---|
| Recipient lacks one required model | Preflight stops with a plain corrective action |
| Existing custom profile shares a filename | Namespaced filenames and no-overwrite installer |
| Host broadens reviewer sandbox | Inspect effective route and block Careful ship claims |
| Runtime metadata format changes | Reject missing fields; never guess model identity |
| Native spawn lacks exact custom-agent selection | Use a separately pinned Codex process and verify its runtime metadata |
| Parallel workers conflict | Exact non-overlapping ownership or serial execution |
