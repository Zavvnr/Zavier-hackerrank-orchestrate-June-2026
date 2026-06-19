---
description: Run the solution on a dataset and write predictions to output.csv (the rollout phase).
argument-hint: [--input dataset/claims.csv] [--out output.csv]
---
Run the evidence-review solution end to end (the AHE "rollout"):

```
python code/main.py $ARGUMENTS
```

Default input is `dataset/claims.csv`; default output is `output.csv` at the repo root (the
submission file). Preconditions: `ANTHROPIC_API_KEY` is exported — never read `.env` to get it.
After it finishes, run `/validate output.csv` to confirm the 14-column schema before trusting it.
This costs real tokens, so prefer `/evaluate` (labeled sample) while iterating, and rely on the image
cache so reruns are cheap and deterministic.
