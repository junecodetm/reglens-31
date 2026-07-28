---
name: govern-check
description: Validate the OSCAL component-definition and refresh the NIST AI RMF / M-25-21 crosswalk.
---
Run `oscal-cli validate governance/component-definition.json` (OSCAL 1.1.3). Ensure model_card, data_card, ai_impact_assessment, monitoring_plan, rollback_plan exist and are non-empty.
