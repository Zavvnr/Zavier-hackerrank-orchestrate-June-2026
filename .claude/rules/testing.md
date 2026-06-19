---
description: Testing = evaluation. Score on the labeled sample before trusting the test predictions.
---

# Testing / Evaluation

There is no big unit-test suite to chase here; **evaluation is the test**. The labeled
`dataset/sample_claims.csv` is the oracle.

## What "passing" means
1. **Schema validity (blocking):** `output.csv` has the exact 14 columns in order, every categorical
   field uses an allowed value, `claim_status`/`severity`/`issue_type`/`object_part`/`risk_flags` are
   in range, and image IDs are well-formed. Run `/validate`
   (`skills/eval-harness/scripts/validate_output.py`).
2. **Sample accuracy:** `/evaluate` scores predictions on `sample_claims.csv` against the expected
   columns and reports per-field accuracy plus macro-F1 for `claim_status`. A change is done only when
   sample metrics hold or improve **and** the schema validates.
3. **Determinism:** same inputs -> same outputs (temperature 0, sorted iteration, cached image calls).
   Re-running `/evaluate` twice should give identical scores.

## Unit-test the deterministic glue
The non-model code *should* have small stdlib `unittest`s: CSV round-trip, `image_paths` splitting on
`;`, image-ID extraction (`img_1`), evidence-requirement matching, risk-flag / severity mapping, and
schema validation. Mock the VLM client so these run offline and free.

## Guardrails the scorer must keep (controllability)
- The scorer and the expected labels are **read-only** to the evolve step. Do not relax the scorer or
  the schema to make a number go up.
- Never hardcode per-row answers. If sample accuracy looks suspiciously high, check for label leakage.

## OneDrive gotcha
When running scripts in the Linux sandbox, mirror the repo in first and run there — don't bash-edit
the OneDrive copy (sync can corrupt files). Edit via the normal file tools.
