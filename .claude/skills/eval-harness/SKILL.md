---
name: eval-harness
description: How to score the solution on the labeled sample, validate the output schema, and distill the evidence corpus that drives harness evolution. Use during /evaluate and /validate.
---

# Eval harness (experience observability)

Turns runs into the structured evidence the evolve loop consumes. Two scripts (stdlib only, no model):

- `scripts/validate_output.py [csv] [--input dataset/claims.csv]` — schema + allowed-value check
  (blocking gate). Mirrors `evidence-review/reference/schema.md`.
- `scripts/score.py predictions.csv --gold dataset/sample_claims.csv` — per-field accuracy, macro-F1
  for `claim_status`, set-overlap for `risk_flags` / `supporting_image_ids`, and a per-case
  wrong-field list. Join key is `image_paths` (falls back to row order). `--json` writes the full
  result for the corpus.

## Building the evidence corpus (the `/evaluate` distillation)
After scoring, for every row whose prediction != expected, write `harness/evidence/case_<id>.md`
(use the `eval-debugger` subagent): the differing fields, the causal field, what the deciding image
actually shows, the root-cause bucket, and the single component most likely at fault. Then write
`harness/evidence/overview.md`: total accuracy + macro-F1, a ranked table of failure clusters
(root-cause bucket -> count -> suspected component), and the top 1-2 fixes to try next. **Start from
the overview, then drill into cases** — never paste raw model logs into the evolve step.

## Operational analysis (`code/evaluation/evaluation_report.md`)
Record: model calls (sample vs full test), input/output tokens, images processed, estimated cost with
the pricing assumptions from the `vlm-client` skill, runtime/latency, and the TPM/RPM + batching /
caching / retry strategy. Re-run `score.py` twice to confirm determinism.

## Do not weaken the test
The scorer and the expected labels are read-only to the evolve step. Improve the solution's reasoning,
never the scorer or the schema.
