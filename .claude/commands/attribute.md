---
description: Verify the previous manifest entry against the latest eval deltas; revert edits that did not pay off.
---
Attribute the last open `harness/decision_manifest.md` entry against the newest `/evaluate` results:

1. Compare per-case correctness from the two most recent runs (the evidence corpus records each run's
   per-case status).
2. Intersect the entry's **predicted fixes** and **predicted regressions** with the observed deltas:
   - **confirmed:** predicted fixes landed and no surprise regressions -> keep; set `verdict: confirmed`.
   - **rejected:** net-negative, or the predicted fixes did not land -> `git revert` that edit's commit;
     set `verdict: rejected`.
   - **mixed:** partial -> keep but note the residual; consider a different component next round.
3. Record the verdict + observed deltas back in the manifest entry, and update `evolution_history.md`.

Attribution runs **before** the next `/evolve`, so every edit is judged as a contract, not a rationale.
