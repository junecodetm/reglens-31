# Evaluation methodology

## Evaluation set

The core evaluation set contains 251 provisions selected deterministically from
the 25-document extraction sample described in
[docs/DATA_SOURCES.md](DATA_SOURCES.md). It has two disclosed strata:

- `base`: seven paragraphs from each sampled document; and
- `ecfr-supplement`: additional paragraphs from the obligation-dense eCFR
  parts.

Pooled precision therefore combines strata with different selection rates.
`web/public/data/eval.json` reports per-stratum results. Each versioned JSONL
record under `reglens/eval/gold/` includes the source SHA, character span,
obligation text and type, affected party, effective date, and
`is_obligation` label.

## Labels and agreement

Two frozen, independent proposal passes by two different frontier models apply
the written guidelines in `docs/ANNOTATION_GUIDELINES.md`. A human adjudicator
resolves proposals to a single label and records the rationale. Machine-proposed
labels are not ground truth. Every published metric retains the runtime label
`Provisional — machine-proposed labels, human-adjudicated: N/M`, with the
adjudicated and total counts substituted for `N` and `M`, until all records are
human-adjudicated.

Reported Cohen's kappa is CROSS-MODEL agreement between two different frontier
models applying the same guidelines. It is not human inter-annotator agreement
and does not establish label correctness. Human inter-annotator kappa is not
reported.

The report uses the Landis and Koch bands (1977, *Biometrics* 33:159–174):
below 0.00, Poor; 0.00–0.20, Slight; 0.21–0.40, Fair; 0.41–0.60, Moderate;
0.61–0.80, Substantial; and 0.81–1.00, Almost perfect. Agreement below 0.61
requires additional review before the statistic can support a reliability
claim.

## Metrics and uncertainty

The core harness reports precision, recall, and F1 for obligation detection.
Citation fidelity is the fraction of accepted claims whose quoted span exactly
matches the source; the provenance gate makes 1.0 the required guardrail.
Published evaluation artifacts do not report end-to-end inference latency or
model-inference cost because the CI harness evaluates committed artifacts. The
CI evaluation itself incurs no paid API cost.

For a binomial metric with `x` successes in `n` trials, `p̂ = x/n` and
`z = 1.96`, the 95 percent Wilson interval is:

```text
center = (p̂ + z²/2n) / (1 + z²/n)
half-width = (z / (1 + z²/n)) × √(p̂(1−p̂)/n + z²/4n²)
```

At `p̂ = 0.90`, representative 95 percent intervals are:

- `n = 150`: approximately `[0.842, 0.938]`;
- `n = 200`: approximately `[0.851, 0.934]`; and
- `n = 384`: approximately `[0.866, 0.926]`.

The value 384 is the conventional sample size for a ±5 percentage-point margin
at `p = 0.5`; the interval is narrower at `p̂ = 0.90`.

Provisions cluster within source documents and rules, so a raw binomial
interval can understate uncertainty. The harness also performs a clustered
bootstrap: it resamples whole clusters with replacement, recomputes the metric,
and reports the 2.5th and 97.5th percentiles. Resamples for which the metric is
undefined are excluded, and the excluded fraction is reported.

The effective sample size uses the design effect:

```text
deff = 1 + (m* − 1) × ICC
m* = Σmᵢ² / Σmᵢ
n_eff = n / deff
```

`m*` is the size-weighted mean cluster size, which accounts for unequal cluster
sizes caused by different stratum sampling rates. The report publishes the
naive Wilson interval and the clustered-bootstrap interval.

## Harness and regression gate

Inspect AI is not adopted. The custom evaluation harness in `reglens/eval/`
owns Wilson intervals, the rule-clustered bootstrap, and Cohen's kappa. Unit
tests exercise those statistics directly. This design avoids an additional
wrapper dependency, but it is less recognizable to reviewers familiar with
Inspect AI and has no third-party validation of the harness.

`.github/workflows/eval.yml` runs the core and OGC-01 gates over committed
artifacts on every pull request. The gate fails when F1 falls below the
committed baseline minus its fixed tolerance or citation fidelity falls below
1.0. The equivalent local command is documented in
[docs/COMMANDS.md](COMMANDS.md).
