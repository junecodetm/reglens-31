# Rollback Plan — RegLens-31

**Deployed site:** Cloudflare Pages keeps every deployment immutable. Rollback = promote the last-good deployment in the Pages dashboard, or `git revert` the offending commit and push (CI redeploys). The static export has no state to migrate.

**Pipeline:** raw snapshots are immutable and content-addressed; any processed artifact can be regenerated from a known-good snapshot + the pinned model tag recorded in each claim's `run` metadata. To roll back a bad extraction: `git revert` the commit that changed `data/processed/` / `web/public/data/` and rebuild.

**Model:** the model tag is pinned in config; rolling back a model change is a one-line revert plus `just extract && just eval` — the eval gate blocks the rollback if it regresses metrics.

**Secrets:** the only secret anywhere is the Cloudflare Pages deploy token (GitHub Actions secret, Pages:Edit scope). Compromise response: roll the token in the Cloudflare dashboard and update the repo secret; nothing else is affected.
