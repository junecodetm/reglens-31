---
name: ingest-source
description: Add or refresh a data source snapshot. Enforces the allow-list and content-addressing.
---
Only the six allow-listed sources (docs/DATA_SOURCES.md) may be fetched. Snapshot to data/raw/<sha256>/ and write manifest.json (source id, URL, fetch time, SHA-256). Set a User-Agent header for OFAC SLS (403 without). Never fetch anything on the exclusion list.
