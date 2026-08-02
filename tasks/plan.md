# Implementation Plan: Project Pilot

## Overview

Build a repository-local Codex marketplace containing one dependency-free plugin. The
core skill will convert a request into a small work card, choose a proportional mode,
perform or delegate the work, verify the result, and scale review depth with risk.

## Architecture Decisions

- Use `project-pilot` as neutral branding so recipients do not confuse this with the
  original Sol Advisor project.
- Preserve the original MIT notice and document the inspiration explicitly.
- Replace hard model pins and separately installed custom agents with optional native
  delegation and a compatible primary-session fallback.
- Offer three human-readable modes: Quick, Guided (default), and Careful.
- Keep the runtime skill concise; store detailed work/review templates in one-level references.
- Test the plugin as data and behavior contracts rather than introducing a build system.

## Dependency Order

```text
Behavior contract tests
        |
Marketplace + plugin scaffold
        |
Core skill + reference templates
        |
Setup/verification helpers
        |
Plain-language docs + attribution
        |
Official validation + forward test
```

## Task List

### Phase 1: Contract and scaffold

- [ ] Write failing tests for the required marketplace, manifest, workflow, safety, and docs contracts.
- [ ] Scaffold the repository marketplace and `project-pilot` plugin with the official helpers.
- [ ] Initialize the `project-pilot` skill with the official skill helper.

### Checkpoint: Foundation

- [ ] The initial tests fail for missing implementation rather than test errors.
- [ ] Generated JSON parses and folder names match manifest names.

### Phase 2: Runtime workflow

- [ ] Implement the concise core skill and mode/risk reference.
- [ ] Add work-card, delegation, verification, and fresh-review templates.
- [ ] Add dependency-free package verification.

### Checkpoint: Runtime

- [ ] Tests pass for mode selection, safe fallback, and review honesty.
- [ ] Official skill and plugin validators pass.

### Phase 3: Human handoff

- [ ] Add plain-language install, use, update, share, remove, and troubleshooting instructions.
- [ ] Add one-command local setup with a non-mutating dry run.
- [ ] Add attribution, license, design comparison, and improvement notes.
- [ ] Forward-test realistic Quick, Guided, and Careful requests in a fresh context.

### Checkpoint: Complete

- [ ] Every success criterion in `docs/SPEC.md` is met.
- [ ] Tests and verification are clean from a fresh checkout layout.
- [ ] No placeholder metadata, secret, named-model dependency, or unexplained setup step remains.

## Risks and Mitigations

| Risk | Impact | Mitigation |
|---|---|---|
| Native agent types vary by Codex version | Medium | Detect availability and fall back without misrepresenting independence |
| Simplification weakens the original's strict routing guarantees | Medium | State the tradeoff and retain risk-based verification/review gates |
| Non-technical users still need an initial plugin install | Medium | Provide one setup command and a paste-ready install request for sharing |
| Remote install commands need a future repository URL | Low | Keep local commands exact and mark publishing as the only remaining owner decision |
| Derivative attribution is lost during sharing | High | Include the original copyright in `LICENSE` and a clear `NOTICE.md` |

## Open Questions

- No blocking questions. Publisher name and remote URL can be customized after the local package works.
