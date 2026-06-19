---
description: Run MATE's unit + integration test suite and report results.
---
Run the full suite from the repo root:

```
python -m unittest discover -s tests -t . -p "*_test.py" -v
```

If imports fail because of the OneDrive sync issue, mirror the repo into the Linux sandbox and run
there (see `CLAUDE.md` -> "Testing workflow"). Report how many tests passed and list any failures with
`file:line` and the assertion that failed. Do not change application code just to make a test pass
without explaining why.
