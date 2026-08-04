# Astral release surfaces

## Evidence order

Prefer direct, current evidence in this order:

1. The public surface itself.
2. The provider's authenticated dashboard or official CLI.
3. A repository artifact or local command that proves only the local state.
4. Prose documentation, which never overrides a manifest or public page.

Do not infer one surface from another.

## Surface contracts

| Surface | Final status | Sufficient evidence | Common false proof |
|---|---|---|---|
| `source` | `verified` | Plugin manifest version plus tested commit | README version alone |
| `github_release` | `published` | Public tag/release URL and release metadata | Local tag only |
| `github_marketplace` | `installable` | Public marketplace JSON and plugin manifest at the documented ref | Commands written in README only |
| `vercel` | `deployed` | Production alias serves the target version; retain deployment ID | Successful preview build |
| `openai_submission` | `draft`, `submitted`, or `approved` | OpenAI Platform submission status | Uploaded ZIP alone |
| `openai_directory` | `published` | Public ChatGPT/Codex plugin page shows the target version | Submission approval or dashboard version |

## Recommended read-only checks

Use available official tools and preserve their outputs as evidence:

```sh
git rev-parse HEAD
git tag --points-at HEAD
gh release view v<version> --repo Demonbane18/astral-orchestrator
vercel inspect <production-deployment-url>
```

Inspect the production site and OpenAI public directory in Opera GX. Use the OpenAI Platform dashboard for submission state only. The OpenAI directory and Codex share the official public plugin listing, but publication can lag behind GitHub and Vercel.

## Transition rules

- Add a `draft` OpenAI submission event when the package exists in the portal.
- Add `submitted` only after the portal accepts the review submission.
- Add `approved` only when OpenAI reports approval.
- Add `published` to `openai_directory` only after the public page changes.
- Add `failed` without deleting the preceding event when a deployment, review, or verification fails.
- Add `superseded` when a newer target intentionally replaces an unfinished release.

## Release handoff

Always include:

- target version and source commit;
- GitHub release URL and asset digest;
- production deployment URL and deployment ID;
- exact marketplace install commands;
- OpenAI submission state;
- OpenAI public directory version;
- every remaining lag or human confirmation gate.
