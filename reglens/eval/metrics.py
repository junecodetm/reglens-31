"""Statistical metrics for the evaluation harness (docs/EVALUATION.md).

Inputs: outcome counts or per-item outcomes grouped by document. Outputs:
point estimates with 95% confidence intervals. Failure mode: ``ValueError`` on
empty or malformed inputs — no metric is ever silently reported from no data.

All functions are pure and deterministic (bootstrap uses a fixed seed).
"""

import math
import random
from collections.abc import Callable, Sequence


def wilson_interval(successes: int, trials: int, z: float = 1.96) -> tuple[float, float]:
    """95% Wilson score interval for a binomial proportion.

    center = (p̂ + z²/2n) / (1 + z²/n);
    half-width = (z / (1 + z²/n)) · √(p̂(1-p̂)/n + z²/4n²).
    """
    if trials <= 0:
        raise ValueError("wilson_interval requires trials > 0")
    if not 0 <= successes <= trials:
        raise ValueError("successes must be within [0, trials]")
    p_hat = successes / trials
    z_sq_over_n = z * z / trials
    center = (p_hat + z_sq_over_n / 2) / (1 + z_sq_over_n)
    half_width = (z / (1 + z_sq_over_n)) * math.sqrt(
        p_hat * (1 - p_hat) / trials + z * z / (4 * trials * trials)
    )
    return (max(0.0, center - half_width), min(1.0, center + half_width))


def precision_recall_f1(
    true_positives: int, false_positives: int, false_negatives: int
) -> tuple[float, float, float]:
    """Standard P/R/F1; zero denominators yield 0.0 rather than raising."""
    precision = (
        true_positives / (true_positives + false_positives)
        if true_positives + false_positives
        else 0.0
    )
    recall = (
        true_positives / (true_positives + false_negatives)
        if true_positives + false_negatives
        else 0.0
    )
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    return precision, recall, f1


def clustered_bootstrap_ci[T](
    clusters: Sequence[Sequence[T]],
    statistic: Callable[[Sequence[T]], float],
    *,
    n_resamples: int = 2000,
    seed: int = 31,
    confidence: float = 0.95,
) -> tuple[float, float]:
    """CI by resampling whole clusters (documents) with replacement.

    Provisions cluster within documents, so raw binomial CIs are too narrow;
    this resamples at the document level (docs/EVALUATION.md, correlated-samples
    correction). Deterministic for a fixed seed.
    """
    if not clusters or all(len(cluster) == 0 for cluster in clusters):
        raise ValueError("clustered_bootstrap_ci requires at least one non-empty cluster")
    rng = random.Random(seed)
    stats: list[float] = []
    for _ in range(n_resamples):
        resampled: list[T] = []
        for _ in range(len(clusters)):
            resampled.extend(rng.choice(clusters))
        stats.append(statistic(resampled))
    stats.sort()
    alpha = (1 - confidence) / 2
    lower_index = int(alpha * n_resamples)
    upper_index = min(n_resamples - 1, int((1 - alpha) * n_resamples))
    return (stats[lower_index], stats[upper_index])


def cohens_kappa(labels_a: Sequence[str], labels_b: Sequence[str]) -> float:
    """Cohen's kappa for two aligned annotation passes.

    Failure mode: ``ValueError`` on length mismatch or empty input. Returns 1.0
    when both passes agree perfectly with zero expected-agreement variance.
    """
    if len(labels_a) != len(labels_b):
        raise ValueError("annotation passes must be aligned")
    if not labels_a:
        raise ValueError("cohens_kappa requires at least one item")
    n = len(labels_a)
    observed = sum(1 for a, b in zip(labels_a, labels_b, strict=True) if a == b) / n
    categories = set(labels_a) | set(labels_b)
    expected = sum(
        (sum(1 for a in labels_a if a == cat) / n) * (sum(1 for b in labels_b if b == cat) / n)
        for cat in categories
    )
    if expected == 1.0:
        return 1.0 if observed == 1.0 else 0.0
    return (observed - expected) / (1 - expected)


def design_effect(mean_cluster_size: float, intra_cluster_correlation: float) -> float:
    """deff = 1 + (m̄ - 1)·ICC (docs/EVALUATION.md)."""
    return 1 + (mean_cluster_size - 1) * intra_cluster_correlation


def effective_sample_size(n: int, deff: float) -> float:
    """n_eff = n / deff; ``ValueError`` if deff is not positive."""
    if deff <= 0:
        raise ValueError("design effect must be positive")
    return n / deff


def binary_icc(clusters: Sequence[Sequence[bool]]) -> float:
    """One-way ANOVA intra-cluster correlation for binary outcomes, clipped to [0, 1].

    Failure mode: ``ValueError`` with fewer than two clusters or no variation
    denominator; degenerate (zero-variance) data yields 0.0.
    """
    sizes = [len(cluster) for cluster in clusters if cluster]
    if len(sizes) < 2:
        raise ValueError("binary_icc requires at least two non-empty clusters")
    values = [[1.0 if item else 0.0 for item in cluster] for cluster in clusters if cluster]
    n_total = sum(sizes)
    k = len(values)
    grand_mean = sum(sum(cluster) for cluster in values) / n_total
    ss_between = sum(len(c) * (sum(c) / len(c) - grand_mean) ** 2 for c in values)
    ss_within = sum(sum((x - sum(c) / len(c)) ** 2 for x in c) for c in values)
    ms_between = ss_between / (k - 1)
    denominator = n_total - k
    if denominator <= 0:
        raise ValueError("binary_icc requires clusters with more than one item overall")
    ms_within = ss_within / denominator
    m_bar = (n_total - sum(size * size for size in sizes) / n_total) / (k - 1)
    denominator_ms = ms_between + (m_bar - 1) * ms_within
    if denominator_ms == 0:
        return 0.0
    return max(0.0, min(1.0, (ms_between - ms_within) / denominator_ms))
