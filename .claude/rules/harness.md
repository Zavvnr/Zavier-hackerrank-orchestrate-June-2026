---
description: How this .claude/ harness is engineered and evolved (Agentic Harness Engineering). Read before editing any harness component.
---

# Harness rules — Agentic Harness Engineering (AHE)

This `.claude/` directory is the agent's **harness**: the model-external, editable components that
mediate how the agent uses tools and the environment. We engineer it with the AHE method
(Lin et al., 2026, *Agentic Harness Engineering: Observability-Driven Automatic Evolution of
Coding-Agent Harnesses*): make the harness **observable** so it improves by measurement, not guesswork.

## The three pillars (what makes evolution safe)
1. **Component observability** — every editable thing is its own file with a fixed home, so each
   failure pattern maps to one component class and every change is a localized, revertible git diff.
   The map lives in `harness/COMPONENTS.md`. **One logical edit = one component file = one commit.**
2. **Experience observability** — we do not eyeball raw run logs to decide changes. `/evaluate`
   distills sample runs into a layered **evidence corpus** under `harness/evidence/`: one root-cause
   report per mismatched case plus an aggregated `overview.md`. Decisions start from the overview and
   drill down (progressive disclosure), so the evolve step consumes root causes, not raw tokens.
3. **Decision observability** — every edit ships a **prediction**. Before applying a change, append an
   entry to `harness/decision_manifest.md` naming the evidence, the inferred root cause, the targeted
   fix, the component touched, and the *predicted impact* (cases expected to flip to correct + cases at
   risk of regressing). The next `/evaluate` + `/attribute` verifies it. An edit is a falsifiable
   contract, not a rationale.

## The seven editable component types (pick the right level)
See `harness/COMPONENTS.md` for the file map. When fixing a failure, consider **all** levels before
choosing where to act:

- **system prompt** -> `CLAUDE.md`, `rules/` (behavioral rules, workflow guidance)
- **tool description** -> `skills/*/SKILL.md` (clarify usage, examples, pitfalls)
- **tool implementation** -> `skills/*/scripts/` (capabilities, error handling, output shape)
- **middleware** -> `settings.json` hooks + `hooks/` (intercept/transform in the agent loop)
- **skill** -> `skills/` (on-demand reusable workflow + domain knowledge)
- **sub-agent** -> `agents/` (delegated, isolated-context subtask)
- **long-term memory** -> `memory/long_term_memory.md` (recurring pitfalls, proven strategies, quirks)

**Anti-pattern:** if the same failure class survives 2+ iterations of edits at one level, that level is
probably wrong — revert and re-approach from a different component.

## The evolve loop (one iteration)
1. **/run** or **/evaluate** — produce trajectories (rollout). Use `/evaluate` on `sample_claims.csv`
   because it carries ground-truth labels.
2. **/attribute** — if a prior manifest entry is open, intersect its predicted fixes/regressions with
   the observed per-case deltas -> a verdict (confirmed / rejected / mixed). Roll back rejected edits.
3. **distill** — `/evaluate` writes the evidence corpus (`harness/evidence/`): per-case reports +
   `overview.md`.
4. **/evolve** — read the overview, choose the smallest edit that addresses the top root cause, write
   the manifest entry *with its prediction*, then apply the edit to exactly one component file.
5. **commit** — one commit per edit, tagged with the iteration, so rollback is free. Append the
   round summary to `harness/evolution_history.md`.

## Controllability (what the evolve step may NOT touch)
So every measured gain is attributable to harness edits, not to weakening the test:
- **Read-only:** `dataset/`, the expected labels, and the scoring/validation scripts in
  `skills/eval-harness/scripts/`. Never relax the scorer or the schema to "pass."
- **Never** hardcode per-row answers or read expected labels inside the solution.
- Keep the AGENTS.md entry points and logging intact (`rules/workflows.md`).

The harness improves the *reasoning*; it never edits the *test*.
