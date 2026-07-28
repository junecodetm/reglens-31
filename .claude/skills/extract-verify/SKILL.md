---
name: extract-verify
description: Run local LLM extraction with JSON-schema constraint and the fail-closed provenance gate.
---
Use temperature 0 and the pinned local model. Constrain output to reglens/extract/schema.py. For each claim, call provenance.verify_span(); drop any claim whose quote is not an exact normalized substring of the source. Emit accepted + rejected counts.
