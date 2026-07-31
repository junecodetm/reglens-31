# Repository Workflow

- Create a short-lived branch and submit all changes to `main` through a pull request.
- Use Conventional Commits (`feat:`, `fix:`, `docs:`, `chore:`, `ci:`, or `test:`).
- Squash-merge each approved pull request after all required CI checks pass.
- Commit signing is outside the project scope and is not required.

Pull-request CI enforces Python formatting and linting, strict type checking, tests, deterministic export replay, the zero-cost invariant, the web build and test suite, disclaimer and framing checks, design-quality checks, evaluation regression gates, CodeQL, dependency and secret scans, Semgrep, and SBOM generation. Local commands are documented in [COMMANDS.md](COMMANDS.md).
