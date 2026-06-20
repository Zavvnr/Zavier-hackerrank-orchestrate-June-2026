# Multi-Modal Evidence Review — Solution

A vision-LLM pipeline that verifies damage claims (car, laptop, package) by analyzing submitted
images against the claim conversation, user history, and minimum evidence requirements.

## Architecture

```
code/
├── main.py              Entry point: claims.csv → output.csv
├── pipeline.py          Per-claim orchestration
├── vlm.py               Claude vision client + disk cache
├── rules_engine.py      Evidence requirements + risk logic
├── schema.py            Allowed values + row validation
├── io_csv.py            CSV read/write
├── .cache/              Disk cache (auto-created, not committed)
└── evaluation/
    └── main.py          Evaluation entry point: sample_claims.csv → scores + report
```

## Setup

```bash
pip install -r requirements.txt
export ANTHROPIC_API_KEY=your_key_here   # or set in environment
```

## Run on test claims

```bash
cd code
python main.py
# Writes ../output.csv
```

## Run evaluation on sample claims

```bash
cd code/evaluation
python main.py
# Writes evaluation_report.md and sample_predictions.csv
```

## How it works

1. **Load context** — reads `user_history.csv` and `evidence_requirements.csv`.
2. **Detect prompt injection** — checks `user_claim` for manipulation attempts; sets
   `text_instruction_present` risk flag if found.
3. **Call Claude claude-sonnet-4-6 vision** — all images for a claim are sent in one message with
   the claim context, evidence requirements, and user history summary. The model returns structured
   JSON with all 14 output fields.
4. **Merge risk flags** — VLM-detected flags + user history flags + injection detection are merged.
5. **Validate output** — every field is checked against allowed values; unknown values fall back
   to safe defaults.
6. **Disk cache** — results are cached by SHA-256(image bytes + context). Reruns are free and
   deterministic (temperature=0).

## Key design decisions

- **One VLM call per claim**: more efficient than per-image calls; gives cross-image context for
  identity-mismatch detection.
- **Images are primary source of truth**: the model is instructed to ignore instructions in claim
  text or image annotations.
- **Graceful degradation**: failed claims produce `not_enough_information` rather than crashing
  the batch.
- **Deterministic**: temperature=0, sorted I/O, content-addressed cache.
