---
description: Invoke the code-reviewer subagent on the pending change.
---
Use the `code-reviewer` subagent (`agents/code-reviewer.md`) to review the change just made. It checks
the hard constraints (no `.env` access, env-only secrets, entry points intact, no hardcoded labels,
schema correctness), correctness, determinism, evidence-grounding, and style, then returns
**APPROVED / CHANGES REQUIRED / BLOCKED** with `file:line` findings. Invoke for non-trivial changes;
skip for typos.
