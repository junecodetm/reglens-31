---
name: eval-gate
description: Run the custom eval harness (reglens/eval/) over the gold set/fixtures and report P/R/F1 with Wilson + clustered-bootstrap CIs.
---
Run against cached fixtures ($0). Compute Wilson 95% CIs and a clustered bootstrap by rule; report n_eff via the design effect. Fail if F1 < baseline - tolerance or citation-fidelity < 1.0.
