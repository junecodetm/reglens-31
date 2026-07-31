# Rollback Plan — RegLens-31

## Deployed site

Cloudflare Pages retains immutable deployments. Recovery promotes the last known
good deployment in the Pages dashboard or reverts the responsible commit and
allows CI to redeploy. The static export has no state migration requirement.

## Pipeline

Raw snapshots are immutable and content-addressed. Processed artifacts can be
regenerated from a known-good snapshot and the pinned model tag recorded in each
claim's `run` metadata. Recovery from an invalid extraction reverts the commit
that changed `data/processed/` or `web/public/data/` and rebuilds the static
artifacts.

## Model

The model tag is pinned in configuration. Recovery from an invalid model change
reverts the configuration change, runs `just extract`, and then runs
`just rebuild` so every downstream artifact derives from the restored claims.
The evaluation gate rejects a rollback that regresses metrics.

## Secrets

The static export requires no runtime secret. Deployment and optional
generation use the following credentials:

- `CLOUDFLARE_API_TOKEN` is a GitHub Actions secret with Pages:Edit scope for
  deployment and Pages secret management.
- `GROQ_API_KEY` is a GitHub Actions secret that deployment binds to the
  Cloudflare Pages project for `/api/draft`.
- `REGLENS_GROQ_API_KEY` is the local pipeline setting for Groq-backed draft and
  memorandum generation and belongs only in the gitignored `.env` or process
  environment.

A suspected Cloudflare token compromise requires token rotation and replacement
of the GitHub Actions secret. A suspected Groq key compromise requires provider
rotation, replacement of the GitHub Actions secret, redeployment to replace the
Pages project secret, and replacement of any local value. If the Groq secret is
missing or unavailable, the optional live endpoint returns a typed failure and
the interface falls back to the committed static draft.
