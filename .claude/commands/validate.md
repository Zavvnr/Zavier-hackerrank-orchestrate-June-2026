---
description: Validate output.csv (or any predictions CSV) against the exact submission schema.
argument-hint: [path/to/output.csv]
---
Check schema + allowed values before trusting any predictions file:

```
python .claude/skills/eval-harness/scripts/validate_output.py ${ARGUMENTS:-output.csv}
```

Verifies the 14 columns in order, categorical fields in range (`claim_status`, `severity`,
`issue_type`, per-object `object_part`, `risk_flags`), booleans for `evidence_standard_met` /
`valid_image`, well-formed `supporting_image_ids`, and that the row count matches the input. A non-zero
exit code means the file is **not** submittable. Run this after every `/run`.
