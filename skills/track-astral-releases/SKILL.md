---
name: track-astral-releases
description: Track and reconcile Astral Orchestrator versions across the source manifest, GitHub tag and release, GitHub marketplace installation, Vercel production site, OpenAI submission, and the public ChatGPT/Codex plugin directory. Use for every version bump, release, deployment, marketplace update, OpenAI plugin submission, public-version check, release-status request, or investigation of mismatched Astral versions.
---

# Track Astral Releases

Maintain one evidence-backed release ledger. Treat every publication surface as independent: a source version, GitHub release, or uploaded OpenAI draft does not prove that the public directory has changed.

## Start every update

1. Read `release/astral-release-ledger.json` from the repository root.
2. Read [release-surfaces.md](references/release-surfaces.md) before checking or changing a publication surface.
3. Resolve the target version from `plugins/astral-orchestrator/.codex-plugin/plugin.json`; never infer it from prose.
4. Run:

   ```sh
   python3 skills/track-astral-releases/scripts/release-ledger.py status \
     --ledger release/astral-release-ledger.json \
     --expected-version <version> --format markdown
   ```

5. Report existing lags before mutating anything.

## Record evidence

After each observed state change, append an event with the bundled script. Supply an explicit RFC 3339 timestamp and concrete evidence.

```sh
python3 skills/track-astral-releases/scripts/release-ledger.py record \
  --ledger release/astral-release-ledger.json \
  --surface github_release \
  --version 3.2.0 \
  --status published \
  --observed-at 2026-08-04T15:15:13+08:00 \
  --url https://github.com/Demonbane18/astral-orchestrator/releases/tag/v3.2.0 \
  --evidence "GitHub release page and gh release view"
```

The command is idempotent for an identical event. Add a new event when a state changes; never rewrite history merely to hide a lag.

Use only these surfaces:

- `source`
- `github_release`
- `github_marketplace`
- `vercel`
- `openai_submission`
- `openai_directory`

Use only these statuses: `draft`, `verified`, `submitted`, `approved`, `published`, `installable`, `deployed`, `failed`, or `superseded`.

## Publication gates

- Ask before pushing, publishing, deploying, or changing global Codex configuration unless the user already authorized that exact action.
- Never accept OpenAI legal or policy attestations for the user. Stop at the checkbox and request explicit confirmation.
- Record `openai_submission` separately from `openai_directory`.
- Record the public directory version only after observing the public ChatGPT/Codex plugin page.
- Record the Vercel version only after inspecting the production alias, not merely a preview deployment.
- Record the marketplace as `installable` only after the public repository ref and manifest are reachable. Do not mutate the user's global marketplace merely to test it without authorization.
- Preserve URLs, commit hashes, deployment IDs, review states, and archive digests in evidence when available.

## Completion

Run the strict check only when claiming a release is public everywhere:

```sh
python3 skills/track-astral-releases/scripts/release-ledger.py check \
  --ledger release/astral-release-ledger.json \
  --expected-version <version> \
  --manifest plugins/astral-orchestrator/.codex-plugin/plugin.json
```

The strict check requires the source, GitHub release, GitHub marketplace, Vercel production site, and OpenAI public directory to match the target version with their final statuses. An OpenAI draft, submitted review, or approval is not a public directory release.

If any surface lags, finish with a release matrix that states the latest observed version, status, evidence, and next action. Say `partially released`, not `released`, until the strict check passes.
