# Changelog

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
