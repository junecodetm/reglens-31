# Git Workflow & Commit Conventions

> Decomposed from CLAUDE.md §7 (2026-07-28).

- Trunk-based with short-lived branches; PRs required even solo (CI must pass).
- Conventional Commits (`feat:`, `fix:`, `docs:`, `chore:`, `ci:`, `test:`).
- Signed commits (`git config commit.gpgsign true`); protected `main`; squash merge.
- Semantic versioning; tag releases `vMAJOR.MINOR.PATCH`; each GitHub Release carries the SBOM + cosign attestation + large Parquet assets.
- Every PR runs: ruff, pyright, pytest, the security suite, a11y, and the **eval regression gate** (must not regress F1 below the committed baseline minus tolerance).
- Include `CONTRIBUTING.md` and a short `CODE_OF_CONDUCT.md` (Contributor Covenant) — cheap signal, high credibility.
