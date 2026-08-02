# Changelog

## 2.1.0 — 2026-08-02

- Added persistent, per-lane effort settings for the orchestrator, Luna, Terra, and the
  final reviewer.
- Added a beginner-friendly configuration command with show, partial update, and reset
  behavior.
- Added strict validation for `minimal`, `low`, `medium`, `high`, `xhigh`, `max`, and
  `ultra`, with no silent downgrade when a model rejects a level.
- Made custom worker and reviewer effort values use the exact-process route so native
  profile defaults cannot override them.

## 2.0.0 — 2026-08-02

- Changed Guided and Careful modes into strict model-routed orchestration.
- Added pinned Luna XHigh and Terra XHigh implementation profiles.
- Added a pinned Sol High read-only review profile.
- Added exact-copy profile installation, verification, and conflict-safe removal.
- Added allowlisted runtime route inspection without an extra JSON package.
- Added a clear Python 3.11+ setup preflight.
- Added an exact-process launcher for hosts without native custom-agent selection.
- Updated setup and non-technical documentation for the new Sol High prerequisite.

## 1.0.0 — 2026-08-02

- Introduced the shareable Project Pilot marketplace plugin.
- Added Quick, Guided, and Careful risk-aware delivery modes.
- Added optional generic delegation, verification, and honest review labeling.
