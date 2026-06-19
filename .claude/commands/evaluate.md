---
description: Score the solution on the labeled sample set and distill an evidence corpus (experience observability).
argument-hint: [--limit N]
---
Run + score on the labeled sample and build the layered evidence corpus:

```
python code/evaluation/main.py $ARGUMENTS
```

This should:
1. Run the pipeline on `dataset/sample_claims.csv` (deterministic; cached image calls).
2. Score predictions vs the expected columns with `skills/eval-harness/scripts/score.py` — per-field
   accuracy + macro-F1 for `claim_status`.
3. Write the **evidence corpus** to `harness/evidence/`: one `case_XXX.md` root-cause report per
   mismatch (predicted vs expected, the deciding image(s), the component likely at fault) and an
   aggregated `overview.md` that ranks failure clusters.
4. Write/refresh `code/evaluation/evaluation_report.md` with the operational analysis (model calls,
   tokens, images, cost, latency, TPM/RPM) — see the `vlm-client` skill for current pricing.

Read `overview.md` first, then drill into the per-case reports. This corpus is the input to `/evolve`.
