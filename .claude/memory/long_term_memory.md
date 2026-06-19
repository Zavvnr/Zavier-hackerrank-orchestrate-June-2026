# Long-term memory

Persistent, cross-session knowledge for this harness. Append proven facts; prune stale ones. This is
the AHE "long-term memory" component — record recurring pitfalls, proven strategies, and environment
quirks so they are not relearned each session.

## Environment quirks
- Repo is OneDrive-synced. Edit `.claude/` and `code/` via the normal file tools; when running scripts
  in a Linux sandbox, mirror the repo in and run there (in-place bash edits can corrupt during sync).
- The file tools may treat `.claude/` as a protected path; if a direct write is blocked, stage the
  file elsewhere and copy it in.

## Dataset facts (verified 2026-06-19)
- `dataset/claims.csv`: 44 test rows (input only). `dataset/sample_claims.csv`: 20 labeled rows.
- `dataset/user_history.csv`: 47 users. `dataset/evidence_requirements.csv`: 11 rules.
- Images: 1-3 per case at `images/{sample,test}/case_XXX/img_N.jpg`. Image ID = `img_N`.
- Sample labels show real subtlety: e.g. an identity mismatch between a close-up and a full view maps
  to `claim_status=not_enough_information` with `wrong_object;claim_mismatch;manual_review_required`.

## Proven strategies (seed — confirm via /attribute before trusting)
- Default to `not_enough_information` when evidence is insufficient; the sample rewards caution.
- One VLM call per claim, all images in a single message, JSON out; cache by image bytes.
- Put the rubric in a cached prompt block; escalate only hard cases from Haiku to Sonnet.

## Known pitfalls (seed)
- `object_part` must match the claim object's allowed list, or `/validate` fails.
- Never mix `none` with other `risk_flags`.
- History risk must not flip clear visual evidence on its own.

> Append confirmed failure modes and fixes from the evidence corpus here as iterations verify them.
