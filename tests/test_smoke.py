"""Package smoke test: the distribution imports and declares a semver version."""

import re

import reglens


def test_version_is_semver() -> None:
    assert re.fullmatch(r"\d+\.\d+\.\d+", reglens.__version__)
