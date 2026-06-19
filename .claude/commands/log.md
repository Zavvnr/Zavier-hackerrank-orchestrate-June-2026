---
description: Append the mandatory AGENTS.md per-turn entry to the shared log file.
---
Append a §5.2 entry to the log file — macOS/Linux `~/hackerrank_orchestrate/log.txt`, Windows
`%USERPROFILE%\hackerrank_orchestrate\log.txt` — in the exact format from AGENTS.md §5.2: an ISO-8601
title, the verbatim user prompt (secrets redacted), a 2-5 sentence response summary, the actions taken,
and the context block (tool / branch / repo_root / worktree / parent_agent). Append only — never
rewrite earlier entries. Redact keys, tokens, and PII. Create the file and parent dir if missing. The
`Stop` hook writes a skeleton entry as a backstop; this command writes the real summary.
