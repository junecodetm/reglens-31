---
name: govern-check
description: Verify the governance artifacts under governance/ exist and are non-empty, and that the NIST AI RMF / M-25-21 crosswalk in docs/GOVERNANCE.md still matches them.
---
Ensure governance/model_card.md, data_card.md, ai_impact_assessment.md, monitoring_plan.md, and rollback_plan.md exist and are non-empty, and that docs/GOVERNANCE.md's crosswalk references them accurately. OSCAL component-definition validation is de-scoped (docs/CHECKLIST.md) — do not add it.
