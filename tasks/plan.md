# Implementation Plan: Project Pilot v2

## Goal

Upgrade Project Pilot into a real model-routed orchestrator with Sol High in charge,
Luna XHigh and Terra XHigh implementation lanes, and a fresh Sol High reviewer.

## Dependency order

```text
Failing v2 contract tests
        |
Pinned agent profiles + safe installer
        |
Strict routing skill + runtime evidence
        |
Beginner setup, removal, and documentation
        |
Validation + local installation + new-task forward test
```

## Checkpoints

### Contract

- [x] Replace v1 fallback tests with exact route and profile tests.
- [x] Confirm the new tests fail for missing v2 behavior.

### Runtime

- [x] Add namespaced Luna XHigh, Terra XHigh, and Sol High reviewer profiles.
- [x] Add conflict-safe install, exact-check, and safe-remove behavior.
- [x] Add allowlisted runtime evidence without an extra JSON package.
- [x] Route work by complexity with strict no-substitution behavior.

### Handoff

- [x] Update the setup helper and beginner documentation.
- [x] Update specification, attribution, comparison, and changelog.
- [ ] Run repository tests, package verification, and official validators.
- [ ] Install v2 locally and confirm exact cached profiles.
- [ ] Forward-test the workflow from a new task that discovers the custom roles.

## Risks

| Risk | Mitigation |
|---|---|
| Recipient lacks one required model | Preflight stops with a plain corrective action |
| Existing custom profile shares a filename | Namespaced filenames and no-overwrite installer |
| Host broadens reviewer sandbox | Inspect effective route and block Careful `ship` claims |
| Runtime metadata format changes | Reject missing fields; never guess model identity |
| Parallel workers conflict | Exact non-overlapping ownership or serial execution |
