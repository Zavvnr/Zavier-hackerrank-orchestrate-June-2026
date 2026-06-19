# Project memory — Multi-Modal Evidence Review (HackerRank Orchestrate, June 2026)

This repo builds a system that verifies **damage claims** about a `car`, `laptop`, or `package`
from submitted **images** + a short **claim conversation** + **user history** + **minimum evidence
requirements**, and emits a structured 14-column verdict per claim. **Images are the primary source
of truth.** Solo 24-hour hackathon; deadline **2026-06-20 11:00 IST**.

## The two contracts this repo obeys
1. **`AGENTS.md` (root) is the binding contract.** It mandates per-turn logging to
   `~/hackerrank_orchestrate/log.txt` and fixed entry points `code/main.py` +
   `code/evaluation/main.py`. Never rename the entry points or disable logging.
2. **This `.claude/` is the *agent harness*** — the model-external, editable scaffolding that makes
   the coding agent effective and continually improvable. It is engineered with the
   **Agentic Harness Engineering (AHE)** framework (Lin et al., 2026). See `rules/harness.md` for the
   operating discipline and `harness/COMPONENTS.md` for the full component map.

## Harness in one breath (AHE → `.claude/`)
Seven editable component types, each a file so the action space is explicit and revertible:
system prompt (`CLAUDE.md` + `rules/`), tool description & implementation (`skills/vlm-client/`,
`skills/eval-harness/scripts/`), middleware (`settings.json` hooks + `hooks/`), skills (`skills/`),
sub-agents (`agents/`), long-term memory (`memory/long_term_memory.md`). Three observability pillars
turn evolution into a measurable loop: **component** (files + git diffs), **experience**
(`harness/evidence/` corpus distilled from sample runs), **decision** (`harness/decision_manifest.md`
pairs every edit with a predicted impact, verified the next round).

## Intended solution layout (you build this in `code/`)
- `code/main.py` — entry point: read `dataset/claims.csv` -> produce `output.csv` (14-col schema).
- `code/evaluation/main.py` — entry point: run on `dataset/sample_claims.csv`, score vs labels,
  write the evidence corpus + `code/evaluation/evaluation_report.md` (operational analysis).
- Suggested modules: `pipeline.py` (per-claim orchestration), `vlm.py` (Claude vision client +
  cache), `extract.py` (claim from conversation), `rules_engine.py` (evidence-requirements + risk
  logic), `schema.py` (allowed values + row validation), `io_csv.py` (robust CSV read/write).

## How to run the harness loop (slash commands)
`/run` (rollout -> output.csv) · `/evaluate` (score sample + build evidence corpus) ·
`/evolve` (evidence + manifest -> edits with predicted impact) · `/attribute` (verify last manifest
vs new deltas, revert losers) · `/validate` (output.csv schema check) · `/review` (code-reviewer
subagent) · `/log` (append the AGENTS.md turn entry).

## Hard constraints (always)
1. **Never read, print, or modify `.env`.** Read secrets from env vars only
   (`ANTHROPIC_API_KEY`, ...). Keep placeholders in committed config.
2. **Never hardcode test labels or file-specific answers.** Decisions come from the images and the
   documented rubric, not memorized rows. Determinism where possible (temperature 0, sorted IO).
3. **All model calls go through the VLM client** (`skills/vlm-client/`) — Anthropic Claude vision.
4. **Preserve the `AGENTS.md` contract**: entry points, append-only logging, secret redaction.
5. **One harness edit = one component file = one commit**, recorded in `harness/decision_manifest.md`
   with a predicted impact. Ineffective edits are reverted at file granularity.

## Rules (read before changing anything)
`rules/harness.md` (the AHE loop), `rules/workflows.md` (build flow + AGENTS.md contract),
`rules/security.md`, `rules/testing.md` (evaluation-as-testing), `rules/code-style.md`,
`rules/preferences.md`.
