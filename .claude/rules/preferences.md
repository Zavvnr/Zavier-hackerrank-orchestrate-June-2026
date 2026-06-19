---
description: General preferences. Superseded by code-style / security / testing on conflict.
---

# Preferences

- **Neat**: consistent indentation, one blank line between logical blocks, two between top-level
  definitions, no trailing whitespace, no dead code.
- **Readable names**: name things for what they mean; avoid abbreviations except universal ones
  (`id`, `url`, `err`, loop `i`).
- **Purposeful comments**: explain *why* in one line; let the code say *what*.
- **Right tool, no over-engineering**: simplest correct approach; prefer the standard library and
  existing helpers over new dependencies; don't add abstraction the hackathon doesn't need.
- **Fail safe**: external calls (the VLM, file IO) degrade gracefully rather than crash the batch — a
  bad row becomes `not_enough_information` / `unknown` with a risk flag, not a stack trace that kills
  the run. Cache image calls so reruns are cheap and deterministic.
