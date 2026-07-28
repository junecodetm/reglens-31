"""Metrics validated against the worked values in docs/EVALUATION.md."""

from collections.abc import Sequence

import pytest

from reglens.eval.metrics import (
    binary_icc,
    clustered_bootstrap_ci,
    cohens_kappa,
    design_effect,
    effective_sample_size,
    kappa_band,
    precision_recall_f1,
    wilson_interval,
)


@pytest.mark.parametrize(
    ("trials", "expected_low", "expected_high"),
    [(150, 0.842, 0.938), (200, 0.851, 0.934), (384, 0.866, 0.926)],
)
def test_wilson_matches_documented_worked_intervals(
    trials: int, expected_low: float, expected_high: float
) -> None:
    low, high = wilson_interval(round(0.90 * trials), trials)
    assert low == pytest.approx(expected_low, abs=2e-3)
    assert high == pytest.approx(expected_high, abs=2e-3)


def test_wilson_rejects_empty_trials() -> None:
    with pytest.raises(ValueError, match="trials"):
        wilson_interval(0, 0)


def test_wilson_bounds_stay_in_unit_interval() -> None:
    low, high = wilson_interval(0, 5)
    assert low == 0.0 and 0 < high < 1
    low, high = wilson_interval(5, 5)
    assert high == 1.0 and 0 < low < 1


def test_precision_recall_f1() -> None:
    precision, recall, f1 = precision_recall_f1(8, 2, 2)
    assert precision == pytest.approx(0.8)
    assert recall == pytest.approx(0.8)
    assert f1 == pytest.approx(0.8)
    assert precision_recall_f1(0, 0, 0) == (0.0, 0.0, 0.0)


def test_clustered_bootstrap_is_deterministic_and_covers_point_estimate() -> None:
    clusters: list[list[bool]] = [
        [True] * 9 + [False],
        [True] * 7 + [False] * 3,
        [True] * 8 + [False] * 2,
        [True] * 10,
        [True] * 6 + [False] * 4,
    ]

    def accuracy(items: Sequence[bool]) -> float:
        return sum(items) / len(items)

    first = clustered_bootstrap_ci(clusters, accuracy)
    second = clustered_bootstrap_ci(clusters, accuracy)
    assert first == second
    point = accuracy([item for cluster in clusters for item in cluster])
    assert first.low <= point <= first.high
    assert first.undefined_fraction == 0.0


def test_clustered_bootstrap_skips_undefined_resamples() -> None:
    # Precision-like statistic: undefined (None) when a resample draws only cluster B.
    clusters: list[list[bool]] = [[True, True, False], [False, False, False]]

    def precision_like(items: Sequence[bool]) -> float | None:
        positives = sum(items)
        return positives / len(items) if positives else None

    result = clustered_bootstrap_ci(clusters, precision_like)
    # Undefined resamples are excluded and reported, never scored as 0.0.
    assert 0.0 < result.undefined_fraction < 0.5
    assert result.low > 0.0


def test_clustered_bootstrap_rejects_empty() -> None:
    with pytest.raises(ValueError, match="non-empty"):
        clustered_bootstrap_ci([], lambda items: 0.0)


def test_cohens_kappa_known_values() -> None:
    assert cohens_kappa(["y", "n"], ["y", "n"]) == 1.0
    # Balanced marginals, 8/10 observed agreement: pe = 0.5 -> kappa = 0.6 exactly.
    a = ["y"] * 5 + ["n"] * 5
    b = ["y", "y", "y", "y", "n", "y", "n", "n", "n", "n"]
    assert cohens_kappa(a, b) == pytest.approx(0.6)


def test_kappa_bands() -> None:
    assert kappa_band(0.95) == "Almost perfect"
    assert kappa_band(0.7) == "Substantial"
    assert kappa_band(0.5) == "Moderate"
    assert kappa_band(0.3) == "Fair"
    assert kappa_band(0.1) == "Slight"
    assert kappa_band(-0.2) == "Poor"


def test_cohens_kappa_rejects_misaligned() -> None:
    with pytest.raises(ValueError, match="aligned"):
        cohens_kappa(["y"], ["y", "n"])


def test_design_effect_and_effective_n() -> None:
    deff = design_effect(mean_cluster_size=5, intra_cluster_correlation=0.2)
    assert deff == pytest.approx(1.8)
    assert effective_sample_size(180, deff) == pytest.approx(100.0)


def test_binary_icc_bounds() -> None:
    # Perfectly homogeneous clusters -> ICC near 1; mixed clusters -> lower.
    homogeneous = [[True] * 5, [False] * 5, [True] * 5, [False] * 5]
    mixed = [[True, False, True, False, True]] * 4
    assert binary_icc(homogeneous) > 0.9
    assert binary_icc(mixed) == 0.0
