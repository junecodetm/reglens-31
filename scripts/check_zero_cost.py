#!/usr/bin/env python3
"""Zero-cost invariant check (CLAUDE.md §2, invariant 1). Stdlib only; exit 1 on violation.

Checks, against the docs/STACK.md allow-list:
1. Every GitHub Actions `uses:` is SHA-pinned and from an allowed owner.
2. Python and web dependencies are exactly the audited allow-list.
3. External URLs in code/config resolve to allow-listed hosts only.

Failure mode: prints each violation and exits non-zero — the build fails closed.
"""

import json
import re
import sys
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

ALLOWED_ACTION_OWNERS = {"actions", "astral-sh", "cloudflare", "github"}

ALLOWED_PYTHON_DEPS = {
    "httpx",
    "pydantic",
    "pydantic-settings",
    "structlog",
    "hypothesis",
    "pyright",
    "pytest",
    "respx",
    "ruff",
}

ALLOWED_WEB_DEPS = {
    "@trussworks/react-uswds",
    "next",
    "react",
    "react-dom",
    "@types/node",
    "@types/react",
    "@types/react-dom",
    "typescript",
}

ALLOWED_HOSTS = {
    # docs/DATA_SOURCES.md fetch set
    "www.federalregister.gov",
    "www.ecfr.gov",
    "www.govinfo.gov",
    "sanctionslistservice.ofac.treas.gov",
    "www.gleif.org",
    "data.opensanctions.org",
    "api.fiscaldata.treasury.gov",
    # local inference + project surfaces (all free/no-card)
    "localhost",
    "github.com",
    "reglens-31.pages.dev",
}

# tests/ is excluded: allow-list tests intentionally contain refused example URLs.
SCAN_GLOBS = [
    "reglens/**/*.py",
    "scripts/*.py",
    ".github/workflows/*.yml",
    "web/app/**/*.tsx",
    "web/app/**/*.ts",
    "web/app/**/*.css",
    "web/*.json",
    "web/*.mjs",
    "justfile",
    "pyproject.toml",
]

URL_PATTERN = re.compile(r"https?://([A-Za-z0-9.-]+)")
USES_PATTERN = re.compile(r"^\s*-?\s*uses:\s*([\w./-]+)@([\w.-]+)", re.MULTILINE)


def check_actions(violations: list[str]) -> None:
    for workflow in sorted(ROOT.glob(".github/workflows/*.yml")):
        for action, ref in USES_PATTERN.findall(workflow.read_text()):
            owner = action.split("/")[0]
            if owner not in ALLOWED_ACTION_OWNERS:
                violations.append(f"{workflow.name}: action owner not allow-listed: {action}")
            if not re.fullmatch(r"[0-9a-f]{40}", ref):
                violations.append(f"{workflow.name}: action not SHA-pinned: {action}@{ref}")


def check_python_deps(violations: list[str]) -> None:
    pyproject = tomllib.loads((ROOT / "pyproject.toml").read_text())
    names = {
        re.split(r"[<>=\[ ]", dep)[0]
        for dep in (
            pyproject["project"]["dependencies"]
            + pyproject.get("dependency-groups", {}).get("dev", [])
        )
    }
    for name in sorted(names - ALLOWED_PYTHON_DEPS):
        violations.append(f"pyproject.toml: dependency not on the audited allow-list: {name}")


def check_web_deps(violations: list[str]) -> None:
    package = json.loads((ROOT / "web" / "package.json").read_text())
    names = set(package.get("dependencies", {})) | set(package.get("devDependencies", {}))
    for name in sorted(names - ALLOWED_WEB_DEPS):
        violations.append(f"web/package.json: dependency not on the audited allow-list: {name}")


def check_urls(violations: list[str]) -> None:
    for pattern in SCAN_GLOBS:
        for path in sorted(ROOT.glob(pattern)):
            if path.name == "package-lock.json":
                continue  # npm registry URLs; registry access is free
            for host in URL_PATTERN.findall(path.read_text(errors="replace")):
                if host not in ALLOWED_HOSTS:
                    violations.append(
                        f"{path.relative_to(ROOT)}: external host not allow-listed: {host}"
                    )


def main() -> int:
    violations: list[str] = []
    check_actions(violations)
    check_python_deps(violations)
    if (ROOT / "web" / "package.json").is_file():
        check_web_deps(violations)
    check_urls(violations)
    if violations:
        print("check_zero_cost: FAIL")
        for violation in violations:
            print(f"  {violation}")
        return 1
    print("check_zero_cost: OK (actions SHA-pinned, deps and hosts on the allow-list)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
