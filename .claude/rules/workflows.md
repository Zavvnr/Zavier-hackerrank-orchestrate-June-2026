---
description: How to work in this repo — the AGENTS.md contract plus the harness build/evolve flow.
---

# Workflow

## Session start (AGENTS.md contract — mandatory)
1. Read root `AGENTS.md` in full. It is the binding contract.
2. Check `~/hackerrank_orchestrate/log.txt`. If it has no `AGREEMENT RECORDED:` line for this repo
   root, run the §3 onboarding (recite the rules, collect `I agree`, record the agreement). Otherwise
   append a `SESSION START` entry (§5.1).
3. Surface time remaining until **2026-06-20 11:00 IST**; if < 2h remain, remind the user to submit.

## Every turn (mandatory)
After responding to each user message, append a §5.2 per-turn entry to the log (use `/log`). The
`Stop` hook writes a skeleton entry as a backstop, but you still write the real summary. **Never**
disable logging, rewrite old entries, or log secrets — redact keys, tokens, and PII.

## Making a change
1. **Understand** — find the component (see `CLAUDE.md` map). Is this a *solution* change (`code/`) or
   a *harness* change (`.claude/`)? Harness changes follow `rules/harness.md` (manifest + prediction).
2. **Change** one thing, following `security.md`, `testing.md`, `code-style.md`, `preferences.md`.
3. **Validate** — `/validate` (output schema) and, for behavior changes, `/evaluate` on the sample
   set. A change is not done until sample metrics hold or improve and the schema validates.
4. **Review** — for non-trivial changes, invoke the `code-reviewer` subagent (`/review`). Skip typos.
5. **Report** what changed, concisely, and log it.

## The submission must always remain evaluable
- `code/main.py` reads `dataset/claims.csv` -> writes `output.csv` (exact 14-col schema, in order).
- `code/evaluation/main.py` runs on `dataset/sample_claims.csv` and writes
  `code/evaluation/evaluation_report.md` (operational analysis: model calls, tokens, images, cost,
  latency, TPM/RPM strategy — see `/evaluate`).
- Secrets from env vars only. Deterministic where possible.

## Not required
No four-stage gate, no restart ceremony, no enterprise load/security theatre. Keep the process
proportional to the change — but never at the cost of the AGENTS.md contract or the manifest discipline.
