---
description: Propose and apply ONE harness edit from the evidence corpus, with a recorded predicted impact (decision observability).
---
Close the AHE loop with one evidence-driven edit:

1. Read `harness/evidence/overview.md` and the top failure cluster's per-case reports.
2. Decide the **single** component (see `rules/harness.md` + `harness/COMPONENTS.md`) whose edit best
   addresses the top root cause. Smallest viable change.
3. **Before editing**, append an entry to `harness/decision_manifest.md` using the template there:
   evidence, root cause, fix, component/file, and predicted impact (cases expected to flip to correct
   + cases at risk of regressing).
4. Apply the edit to exactly that one file.
5. Commit just that file (`git add <file> && git commit`) tagged with the iteration; append a line to
   `harness/evolution_history.md`.

Then run `/evaluate` and, next round, `/attribute` to verify the prediction. Never bundle multiple
edits — one falsifiable change per iteration, so attribution stays clean.
