# Evolution history

One row per iteration: what changed, the sample metrics before/after, and the attribution verdict.
Newest at the bottom.

| iter | date | component edited | sample acc | claim_status F1 | verdict |
|---|---|---|---|---|---|
| 0 | 2026-06-19 | seed harness (bootstrap) | — | — | open |

Notes:
- **iter 0** — harness created from the AHE framework; no solution behavior changed. Baseline metrics
  are recorded after the first `/evaluate`, once `code/main.py` produces predictions on the sample set.
