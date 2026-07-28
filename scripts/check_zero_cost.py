#!/usr/bin/env python3
"""Zero-cost invariant check (CLAUDE.md §2, invariant 1).

PLACEHOLDER — Phase 0 work (docs/BUILD_PLAN.md): the real check must fail if a
dependency, GitHub Action, or service outside the docs/STACK.md free/no-card
allow-list appears in pyproject.toml, uv.lock, .github/workflows/, or configs.

Failure mode: currently NEVER fails (exit 0) so `just check-cost` and the Stop
hook run cleanly before Phase 0. It verifies nothing — do not treat a green run
as a zero-cost audit until the allow-list check is implemented.
"""

import sys


def main() -> int:
    print(
        "check_zero_cost: PLACEHOLDER — allow-list check not yet implemented "
        "(Phase 0, docs/BUILD_PLAN.md). Nothing was verified."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
