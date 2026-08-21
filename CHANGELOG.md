# Changelog

## 3.6.0 — 2026-08-21

### Added

- Added explicit opt-in Singularity: one verified Sol primary session for meaningful
  low- or medium-risk work, with no subagents or fresh reviewer and one proportional
  self-review. Event Horizon still takes over for high-risk work or when its safeguards
  are required.
- Added the documented attribution for Singularity's scope-control and verification
  patterns to Single-Agent Skills; its external plugin and runtime are not bundled or
  required.

### Changed

- Renamed the primary modes to Comet, Orbit, Event Horizon, and Pulsar. Orbit remains
  the default; Comet remains the tiny Sol-only route; Event Horizon retains high-risk
  confirmation gates and read-only review requirements; Pulsar remains explicit opt-in
  for evidence-oriented work.
- Kept Quick, Guided, Careful, and Measured as advisory prompt aliases so existing prompts
  map to the same behavior while new documentation, starter prompts, and package metadata
  use the cosmic taxonomy.
- Renamed the active evidence-route reference to `pulsar-mode.md`; its legacy local state
  directory name remains compatible with resumable runs.

## 3.5.0 — 2026-08-16

### Added

- Added native Codex MultiAgentsV2 routing with explicit agent type, unique task name,
  model, reasoning effort, and isolated child context on every worker and reviewer spawn.
- Added safe migration for byte-exact v3.4.0 companion profiles while preserving any
  user-customized profile unchanged.

### Changed

- Changed the default worker efforts to Luna Max and Terra High while keeping all four
  lane efforts independently configurable.
- Kept the bundled process launcher as a compatibility fallback only for hosts without
  the required native-v2 controls.

### Fixed

- Astral Status is now always emitted as an unfenced GitHub-flavored Markdown table,
  including requested-versus-observed role, model, effort, state, and evidence fields.
- Expanded the privacy notice with explicit retention and user-control information.

## 3.4.0 — 2026-08-13

### Added

- Added a live Astral status panel to substantive progress updates so users can see each
  primary, worker, and reviewer lane's role, requested and observed model and effort,
  lifecycle state, and allowlisted route evidence while work is running.
- Added copy-ready README prompts for Quick, Guided, Careful, Measured, Morph, and
  Constellation modes.

### Changed

- Clarified that Constellation uses Sol High by default and does not require Sol Ultra.
- Documented and tested the custom Morph worker sequence: dry-run the exact route, launch
  that same route, then require matching runtime evidence before accepting the worker.

### Security

- Status panels exclude prompts, packet contents, messages, tool arguments, credentials,
  secrets, personal data, and arbitrary file contents.

## 3.3.1 — 2026-08-09

### Fixed

- Exact-process and Morph launchers now select the first Codex runtime that can parse the
  active user configuration and model catalog instead of trusting PATH order alone.
- Dry runs now prove runtime compatibility before inference and report allowlisted runtime
  source, version, and configuration-probe evidence.

### Security

- Runtime hints now require absolute executable regular files, reject Unicode control
  characters, deduplicate resolved paths, time out closed, and never expose probe output,
  configuration contents, credentials, or private worker packets in failure evidence.

## 3.3.0 — 2026-08-09

### Added

- Added automatic local primary-route verification for Codex before fixed-mode delegation.
- Added explicit opt-in Morph and capacity-aware Constellation worker routes while preserving
  all six modes: Quick, Guided, Careful, Measured, Morph, and Constellation.
- Added an additive portable package manifest and capability boundary for non-Codex hosts;
  skill discovery does not claim portable orchestration, model routing, or concurrency.

### Changed

- Clarified that cross-host Morph and Constellation require observed model, worker-context,
  concurrency where applicable, and fresh-reviewer capabilities before use.

## 3.2.0 — 2026-08-04

### Added

- Added explicit opt-in Measured mode: a deliberately slower, evidence-oriented route
  with one frozen work card, deterministic lane selection, and fresh review evidence.
- Added private non-secret owner-only local state keyed by effective UID plus independent
  repository-root and frozen-card SHA-256 prefixes, with safe resume/archive handling.
- Added 2026-08-04 instruction-context evidence for core, Quick, Guided, and Measured
  bundles while preserving historical v3.1.4 evidence.

### Changed

- Documented the two-command GitHub marketplace install: `codex plugin marketplace add
  Demonbane18/astral-orchestrator --ref main`, then `codex plugin add
  astral-orchestrator@astral-orchestrator`. This route uses bundled exact processes;
  cloning and `scripts/setup.sh` remain the optional faster native-profile route.
- Clarified that official ChatGPT/Codex directory publication is a separate surface and
  may lag until the v3.2.0 directory upload is published.

## 3.1.4 — 2026-08-03

### Documentation

- Documented the published, installable, open-source v3.1.4 plugin and added reproducible
  `tiktoken` instruction-context footprint evidence without changing runtime dependencies.
- Replaced the README Mermaid diagrams with GitHub-renderable SVGs and editable Excalidraw
  sources for routing and the separate outcome scorecard.

### Changed

- Updated the plugin repository metadata to the marketplace-compatible canonical repository
  URL.

### Security

- The exact-process launcher now rejects prompt packets with group or other permission bits
  before Codex lookup or execution.

## 3.1.3 — 2026-08-03

### Fixed

- Included the canonical MIT `LICENSE` and Sol Advisor `NOTICE.md` attribution in the
  distributable plugin bundle.
- Added package verification and regression coverage that reject missing or modified
  distributable notices.

## 3.1.2 — 2026-08-02

### Changed

- Added official plugin-directory icon metadata and brand color alongside the packaged
  Astral Orchestrator logo.

## 3.1.1 — 2026-08-02

### Changed

- Added the Astral Orchestrator brand mark to the plugin interface, with small and
  large icon metadata pointing at the packaged logo asset.

## 3.1.0 — 2026-08-02

### Added

- A local, standard-library benchmark scorecard for repeated Astral and single-Sol trial
  records, with route evidence and comparable acceptance checks.

### Changed

- Explained the routing heuristic, configurable reasoning effort, and its limits in
  plain language, with GitHub-rendered routing and benchmark diagrams.

## 3.0.0 — 2026-08-02

### Changed

- **Breaking identity migration:** renamed the product from the former name, Project
  Pilot, to Astral Orchestrator.
- Renamed the plugin, marketplace, skill, profile filenames, and TOML agent names to
  astral-orchestrator / astral_orchestrator.
- Renamed the launcher route-evidence prefix to ASTRAL_ORCHESTRATOR_ROUTE.
- Moved persistent effort settings to ~/.codex/astral-orchestrator/effort-levels.toml
  (or the equivalent directory under CODEX_HOME).
- Added the repository and homepage metadata for
  https://github.com/Demonbane18/astral-orchestrator.

### Migration

Install Astral Orchestrator as a new plugin. Remove the former Project Pilot plugin and
profiles only when you no longer use them. The old effort-settings file is deliberately
not read or copied: use configure-effort.sh to choose the desired values for the new
namespaced profile.

## Former-name history: Project Pilot 2.1.0 — 2026-08-02

- Added persistent, per-lane effort settings for the orchestrator, Luna, Terra, and the
  final reviewer.
- Added a beginner-friendly configuration command with show, partial update, and reset
  behavior.
- Added strict validation for minimal, low, medium, high, xhigh, max, and ultra, with no
  silent downgrade when a model rejects a level.
- Made custom worker and reviewer effort values use the exact-process route so native
  profile defaults cannot override them.

## Former-name history: Project Pilot 2.0.0 — 2026-08-02

- Changed Guided and Careful modes into strict model-routed orchestration.
- Added pinned Luna XHigh and Terra XHigh implementation profiles.
- Added a pinned Sol High read-only review profile.
- Added exact-copy profile installation, verification, and conflict-safe removal.
- Added allowlisted runtime route inspection without an extra JSON package.
- Added a clear Python 3.11+ setup preflight.
- Added an exact-process launcher for hosts without native custom-agent selection.

## Former-name history: Project Pilot 1.0.0 — 2026-08-02

- Introduced the shareable marketplace plugin.
- Added Quick, Guided, and Careful risk-aware delivery modes.
- Added optional generic delegation, verification, and honest review labeling.
