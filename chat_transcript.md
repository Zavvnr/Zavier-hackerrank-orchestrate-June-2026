# Chat transcript — AI-assisted development log

**Project:** Multi-Modal Evidence Review (HackerRank Orchestrate, June 2026)
**Author:** zvvnr · **Assistant:** Claude (Cowork)
**Scope:** designing the `.claude/` agent harness and building/iterating the `code/` solution.

This is a structured, turn-by-turn record of the AI pair-programming session that produced this
submission. It documents the requests, the decisions, and the measured outcomes.

---

## Summary of the final state

- **Solution** (`code/`): a Claude-vision pipeline that reads each claim's images + conversation +
  user history + evidence requirements and emits the 14-column verdict. Modules: `main.py`,
  `pipeline.py`, `vlm.py` (Claude client + disk cache), `rules_engine.py`, `consistency.py`,
  `schema.py`, `io_csv.py`, `evaluation/main.py`, `tests/`.
- **Harness** (`.claude/`): the seven AHE component types mapped to files + three observability
  artifacts (component map, decision manifest, evidence corpus), per Lin et al. 2026.
- **Toggles** (env vars, all measured on the labeled sample): `EVR_BEST_OF_N` (diverse-lens
  ensemble + verifier), `EVR_FEWSHOT`, `EVR_CALIB`, `EVR_CONSISTENCY`.
- **Best measured config:** base prompt + consistency ON, with the ensemble (`EVR_BEST_OF_N=3`) for
  the final one-shot run. Calibration and few-shot were tested and **rejected** (they hurt the
  decision). claim_status macro-F1 on the 20-row sample ranged ~0.86–0.95 across runs; descriptive
  fields (severity/issue_type/risk_flags) stayed weak and noisy at n=20.

---

## Turn-by-turn log

1. **Confirm materials + design the harness.** Read `problem_statement.md`, `AGENTS.md`, the dataset
   (44 test rows, 20 labeled sample, 47 users, 11 evidence rules), and the AHE paper. Clarified:
   build in `hackerrank-orchestrate-june26/.claude`, reuse the existing skeleton with rewritten
   content, target Anthropic Claude vision, full AHE scope.

2. **Built the `.claude/` harness.** Mapped the 7 AHE component types (system prompt, tool
   description, tool implementation, middleware, skill, sub-agent, long-term memory) onto
   `CLAUDE.md` + `rules/`, `skills/` (evidence-review, eval-harness, vlm-client), `agents/`
   (code-reviewer, evidence-reviewer, eval-debugger), `settings.json` hooks + `hooks/`, and
   `memory/`. Added the 3 observability artifacts: `harness/COMPONENTS.md`,
   `harness/decision_manifest.md`, `harness/evidence/`. Enforced the AGENTS.md contract (env-only
   secrets, entry points, per-turn logging) and verified everything.

3. **Push question.** Confirmed `origin` pointed at the upstream starter repo; gave steps to point it
   at the participant's own repo. (A sandbox git operation earlier corrupted `.git/index` — flagged
   it as a one-time Windows fix: `del .git\index.lock` & `del .git\index`, then `git reset`.)

4. **Code analysis.** Reviewed the cloned solution: only third-party dep is the `anthropic` SDK; the
   rest is stdlib; "vision" is Claude, not a local model. Walked through the workflow. Advised
   **against** building vision nets from scratch in PyTorch (tiny data, wrong tool, can't fine-tune a
   hosted VLM) and explained when it would make sense.

5. **Applied safe hardening.** `schema.py`: stopped `coerce_row` mixing `none` with real flags; added
   `validate_prediction_rows`. `vlm.py`: env-key guard, full-text cache key. Added
   `code/requirements.txt`; wired schema validation into `main.py` + the eval. Kept `code/`
   self-contained for the `code.zip` submission.

6. **Aligned the scorers.** Switched the eval's set-field scoring to exact-set match (matching the
   harness scorer) with a Jaccard partial-credit diagnostic; verified the two scorers report
   identical numbers on a perturbed set.

7. **Accuracy brainstorm.** Grounded ideas in the sample label distribution (supported 12 /
   contradicted 5 / NEI 3; severity mostly medium; manual_review 8/20). Identified the prompt's
   supported-bias and the descriptive-field weakness as the targets.

8. **Paper: Diffusion Model Predictive Control.** Concluded its literal method (diffusion + learned
   dynamics + MPC) doesn't fit a one-shot perception task, but its propose-and-select pattern
   transfers → implemented **best-of-N + verifier** (toggleable, gated to low-confidence rows) plus
   JSON-repair salvage.

9. **Paper: Multi-Signal Control (ensemble of monitors).** Adopted the diverse-prompt insight →
   upgraded best-of-N candidates to **diverse "monitor lenses"** (neutral, high-precision,
   authenticity/identity) at temperature 0, verifier-selected.

10. **Consistency layer.** Verified the rubric invariants on the sample (NEI⟺evidence=false;
    NEI→severity=unknown; supported/contradicted→evidence=true; supported→severity in
    {low,medium,high}) and implemented `consistency.py` (status-primary; additive
    `manual_review_required` on safe triggers). Added 15 offline unit tests; a status/evidence
    conflict test caught a policy bug (made status primary). All tests pass.

11. **Windows setup fixes.** Diagnosed the `puccinialin` pip error as an old Python (< 3.9) →
    recreate the venv on Python 3.10+. Explained how to export `ANTHROPIC_API_KEY` via the
    environment (never `.env`).

12. **Two caching bugs fixed.** Cache filenames used `|` (illegal on Windows) → changed to `-`. The
    top-level cache key ignored the mode → added `best_of_n` / `use_fewshot` / `use_calib` so each
    configuration caches separately and the A/B is valid.

13. **Baseline eval.** macro-F1 0.856, claim_status 0.90; the two misses were both "should have been
    contradicted." Per-field drill-down: severity 0.40 (systematically medium-called-high),
    risk_flags 0.45 (over-flagging), supporting_image_ids missing on contradicted rows.

14. **Severity calibration** added as a measured toggle (`EVR_CALIB`).

15. **A/B results (20-row sample).** Calibration → macro-F1 0.677; few-shot → 0.708; ensemble
    (N=3) → 0.915; consistency-off → 0.950 (note: consistency doesn't affect claim_status);
    calib+few-shot → 0.611. **Conclusions:** added prompt text (calibration, few-shot) reliably
    *hurt* the decision and were rejected; the base model on a clean run is already ~0.95; the
    ensemble adds robustness for the one-shot test run; run-to-run variance at n=20 is large and
    dominates several gaps. Recommended config: base + consistency ON, calibration/few-shot OFF,
    ensemble for the final test run.

16. **Wrap-up (this turn).** Produced this transcript and prepared the repo for pushing to the
    participant's own repository. (Decision-manifest/README "recording" deferred to the next day,
    before the recording deadline.)

---

## Open items (deferred to before the recording deadline)

- Record this evolution round in `.claude/harness/decision_manifest.md` (calibration & few-shot:
  rejected; ensemble: kept) and note the recommended config in the README.
- Re-establish a clean fresh baseline on the current code for an apples-to-apples reference.
