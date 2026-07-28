# Evaluation Methodology

> Decomposed from CLAUDE.md §11 (2026-07-28).

**Gold-set construction.** Hand-label ≥200 provisions drawn from eCFR Title 31 and Federal Register documents. Each gold item = {source SHA, char span(s), obligation text, obligation type, affected party, effective date, is_obligation (bool)}. Stratify across document types and section lengths. Store in `reglens/eval/gold/` as versioned JSONL with a data card.

**Annotation protocol.** Two independent passes (self + a second labeler if available; otherwise a time-separated re-label). Written guidelines define what counts as an "obligation," how to choose the minimal span, and tie-breaking rules. All disagreements adjudicated to a single gold label with a recorded rationale.

**Inter-annotator agreement.** Report Cohen's kappa. Interpretation bands (Landis & Koch 1977, Biometrics 33:159–174): below 0.00 Poor; 0.00–0.20 Slight; 0.21–0.40 Fair; 0.41–0.60 Moderate; 0.61–0.80 Substantial; 0.81–1.00 Almost perfect. Target ≥0.61 (Substantial) before trusting the metric.

**Metrics.** Precision, recall, F1 for obligation detection; span-level citation-fidelity (fraction of accepted claims whose quote exactly matches source — ≈1.0 by the provenance gate's construction, reported as a guardrail); latency and cost per document (cost ≈ $0 local). Report each with a **95% Wilson score interval**.

**Wilson score interval (formula).** For x successes in n trials, p̂ = x/n, z = 1.96:
center = (p̂ + z²/2n) / (1 + z²/n);
half-width = (z / (1 + z²/n)) · √( p̂(1−p̂)/n + z²/4n² ).
Worked 95% intervals at p̂ = 0.90:
- n = 150 → ≈ [0.842, 0.938]
- n = 200 → ≈ [0.851, 0.934]
- n = 384 → ≈ [0.866, 0.926]
(384 is the classic n for ±5% at p=0.5; at p̂=0.90 the interval is tighter.)

**Correlated-samples correction.** Provisions cluster within documents/rules, so raw binomial CIs are too narrow. Use a **clustered bootstrap resampling by rule** (resample whole documents with replacement, recompute the metric per resample, take the 2.5/97.5 percentiles; resamples where the metric is undefined are excluded and their fraction reported). Report the **effective sample size** via the design effect: deff = 1 + (m* − 1)·ICC, where m* = Σmᵢ²/Σmᵢ is the **size-weighted mean cluster size** (the conservative generalization of the plain mean m̄ for unequal clusters — required here because strata sample documents at different rates) and ICC the intra-cluster correlation; n_eff = n / deff. Report both the naive Wilson CI and the (wider, honest) clustered-bootstrap CI.

**CI regression gate.** `eval.yml` runs Inspect AI over cached fixtures at $0 API cost on every PR; fails if F1 drops below the committed baseline minus a fixed tolerance, or if citation-fidelity < 1.0. `[VERIFY]` whether the pinned Inspect release exposes native CI metrics; if not, `reglens/eval/metrics.py` owns Wilson + bootstrap.
