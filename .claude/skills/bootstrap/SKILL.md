---
name: bootstrap
description: Decompose this CLAUDE.md master spec into component files per the TARGET tags, then trim CLAUDE.md to a short core with @-imports.
---
Read CLAUDE.md. For each section tagged `TARGET: <path>`, create that file with the section body. Then replace CLAUDE.md with the core sections (0,1,2,5-short,21) plus `@docs/...` imports. Do not invent content; only move existing content. Run `just ci` after.
