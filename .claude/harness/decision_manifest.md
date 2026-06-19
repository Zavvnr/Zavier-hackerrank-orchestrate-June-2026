# Decision manifest (decision observability)

Every harness edit is a falsifiable contract: a prediction recorded **before** the edit, verified by
the next `/evaluate` + `/attribute`. Append entries; never rewrite a verdict — add a follow-up instead.

## Entry template
```
### [iteration N] <short title>  (<date>)
- component: <the one file edited>
- evidence: <which evidence-corpus cases / overview cluster motivated this>
- root_cause: <one line>
- fix: <what the edit does>
- predicted_fixes: <case ids expected to flip to correct>
- predicted_regressions: <case ids at risk>
- commit: <git sha or tag>
- verdict: open | confirmed | rejected | mixed     (set by /attribute next round)
- observed: <actual per-case deltas once verified>
```

## Entries

### [iteration 0] Seed harness created  (2026-06-19)
- component: entire `.claude/` (bootstrap; every subsequent edit touches exactly one file)
- evidence: n/a — built from `problem_statement.md` + `AGENTS.md` + the AHE paper
- root_cause: no harness existed; the build agent had no explicit action space or measured eval loop
- fix: instantiated the 7 AHE component types + the 3 observability artifacts, mapped onto `.claude/`
- predicted_fixes: enables measurable iteration; first real metrics arrive with the first `/evaluate`
- predicted_regressions: none (no solution behavior changed yet)
- commit: <fill on commit>
- verdict: open
- observed: pending the first `/evaluate` (needs `code/main.py`)
