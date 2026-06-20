"""Evaluation entry point: score predictions on sample_claims.csv and write report."""

import collections
import csv
import io
import pathlib
import sys
import time

ROOT = pathlib.Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT / "code"))

import io_csv
import pipeline
import schema

DATASET_DIR = ROOT / "dataset"
SAMPLE_CSV = DATASET_DIR / "sample_claims.csv"
USER_HISTORY_CSV = DATASET_DIR / "user_history.csv"
EVIDENCE_REQ_CSV = DATASET_DIR / "evidence_requirements.csv"

EVAL_DIR = pathlib.Path(__file__).parent
PREDICTIONS_CSV = EVAL_DIR / "sample_predictions.csv"
REPORT_MD = EVAL_DIR / "evaluation_report.md"

# Fields used for accuracy scoring.
SCORED_FIELDS = [
    "evidence_standard_met",
    "risk_flags",
    "issue_type",
    "object_part",
    "claim_status",
    "supporting_image_ids",
    "valid_image",
    "severity",
]


def _norm(value: str) -> str:
    """Normalize a scalar field for exact comparison (matches the harness scorer)."""
    return (value or "").strip().lower()


def _as_set(value: str) -> frozenset:
    """A semicolon-separated field as a lowercased token set (matches the harness scorer)."""
    return frozenset(t.strip().lower() for t in (value or "").split(";") if t.strip())


def _jaccard(a: str, b: str) -> float:
    """Jaccard overlap for a multi-value field (diagnostic partial-credit only)."""
    sa, sb = _as_set(a), _as_set(b)
    if not sa and not sb:
        return 1.0
    return len(sa & sb) / len(sa | sb)


def score_predictions(sample_rows: list[dict], predictions: list[dict]) -> dict:
    """Compute per-field accuracy and claim_status macro-F1.

    Set-valued fields (risk_flags, supporting_image_ids) use EXACT-set match for the headline
    accuracy, so this agrees with the harness scorer
    (.claude/skills/eval-harness/scripts/score.py). A Jaccard partial-credit score is also
    returned per set field as a diagnostic.
    """
    assert len(sample_rows) == len(predictions), "Row count mismatch"
    n = len(sample_rows)
    field_correct: dict[str, float] = collections.defaultdict(float)
    field_partial: dict[str, float] = collections.defaultdict(float)  # Jaccard, diagnostic only

    # claim_status confusion matrix for F1.
    labels = list(schema.CLAIM_STATUS)
    confusion: dict[str, dict[str, int]] = {
        l: {l2: 0 for l2 in labels} for l in labels
    }

    for gold, pred in zip(sample_rows, predictions):
        for field in SCORED_FIELDS:
            gv = gold.get(field, "")
            pv = pred.get(field, "")
            if field in {"risk_flags", "supporting_image_ids"}:
                # Exact-set match for the headline (matches the harness scorer).
                field_correct[field] += 1.0 if _as_set(gv) == _as_set(pv) else 0.0
                field_partial[field] += _jaccard(gv, pv)
            else:
                field_correct[field] += 1.0 if _norm(gv) == _norm(pv) else 0.0

        # Confusion matrix for claim_status F1.
        g_status = _norm(gold.get("claim_status", "not_enough_information"))
        p_status = _norm(pred.get("claim_status", "not_enough_information"))
        if g_status in confusion and p_status in labels:
            confusion[g_status][p_status] += 1

    # Per-field accuracy (exact). Set fields also get a Jaccard partial-credit diagnostic.
    accuracies = {f: field_correct[f] / n for f in SCORED_FIELDS}
    partials = {f: field_partial[f] / n for f in ("risk_flags", "supporting_image_ids")}

    # Macro-F1 for claim_status.
    f1s = []
    for label in labels:
        tp = confusion[label][label]
        fp = sum(confusion[other][label] for other in labels if other != label)
        fn = sum(confusion[label][other] for other in labels if other != label)
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0
        f1s.append(f1)
    macro_f1 = sum(f1s) / len(f1s)

    return {"per_field": accuracies, "per_field_partial": partials,
            "claim_status_macro_f1": macro_f1}


def main() -> None:
    """Run evaluation on sample_claims.csv and write report."""
    print(f"Reading sample claims from {SAMPLE_CSV}")
    sample_rows = io_csv.read_claims(SAMPLE_CSV)
    user_history = io_csv.read_lookup(USER_HISTORY_CSV, "user_id")
    evidence_requirements = io_csv.read_list(EVIDENCE_REQ_CSV)

    n = len(sample_rows)
    print(f"Processing {n} sample claims...")

    predictions = []
    total_time = 0.0
    for i, row in enumerate(sample_rows, start=1):
        print(f"  [{i}/{n}] {row['user_id']} | {row['claim_object']}")
        t0 = time.time()
        pred = pipeline.process_claim(row, user_history, evidence_requirements)
        elapsed = time.time() - t0
        total_time += elapsed
        print(f"    -> {pred['claim_status']} (gold: {row.get('claim_status', '?')}) | {elapsed:.1f}s")
        predictions.append(pred)

    # Save predictions CSV.
    io_csv.write_output(predictions, PREDICTIONS_CSV, schema.OUTPUT_COLUMNS)

    # Schema gate: same strict checks as the harness /validate (kept in code/ so the submission is standalone).
    schema_errors = schema.validate_prediction_rows(predictions)
    schema_status = "PASS" if not schema_errors else f"{len(schema_errors)} violation(s)"
    print(f"  schema: {schema_status}")
    for err in schema_errors[:5]:
        print("    -", err)

    # Score.
    scores = score_predictions(sample_rows, predictions)
    per_field = scores["per_field"]
    per_field_partial = scores["per_field_partial"]
    macro_f1 = scores["claim_status_macro_f1"]

    # Per-case breakdown.
    case_lines = []
    for row, pred in zip(sample_rows, predictions):
        g = row.get("claim_status", "?")
        p = pred.get("claim_status", "?")
        match = "OK" if g == p else "MISS"
        case_lines.append(f"| {row['user_id']} | {row['claim_object']} | {g} | {p} | {match} |")

    # Count model calls (each prediction = 1 call, minus cache hits).
    cache_dir = ROOT / "code" / ".cache"
    cache_count = len(list(cache_dir.glob("*.json"))) if cache_dir.exists() else 0

    # Estimate costs (claude-sonnet-4-6: $3/MTok in, $15/MTok out, approx).
    avg_input_tokens = 3000   # ~2 images + context per claim
    avg_output_tokens = 300
    total_claims_est = n + 44  # sample + test
    cost_in = total_claims_est * avg_input_tokens / 1_000_000 * 3.0
    cost_out = total_claims_est * avg_output_tokens / 1_000_000 * 15.0
    cost_total = cost_in + cost_out

    report = f"""# Evaluation Report

## Scores on sample_claims.csv (n={n})

**claim_status macro-F1: {macro_f1:.3f}**  ·  **schema: {schema_status}**

### Per-field accuracy
| Field | Accuracy |
|-------|----------|
"""
    for field, acc in sorted(per_field.items()):
        report += f"| {field} | {acc:.3f} |\n"
    report += (
        "\n*Set fields (`risk_flags`, `supporting_image_ids`) use exact-set match above, which "
        "agrees with the harness `/evaluate` scorer. Jaccard partial-credit diagnostic — "
        f"risk_flags: {per_field_partial['risk_flags']:.3f}, "
        f"supporting_image_ids: {per_field_partial['supporting_image_ids']:.3f}.*\n"
    )

    report += f"""
## Per-case breakdown
| user_id | object | gold | pred | result |
|---------|--------|------|------|--------|
"""
    report += "\n".join(case_lines)

    report += f"""

## Operational analysis

| Metric | Value |
|--------|-------|
| Model | claude-sonnet-4-6 |
| Sample claims processed | {n} |
| Test claims to process | 44 |
| Total claims (sample + test) | {total_claims_est} |
| Avg latency per claim | {total_time/n:.1f}s |
| Total sample run time | {total_time:.1f}s |
| Disk cache entries present | {cache_count} |
| Est. avg input tokens/claim | ~{avg_input_tokens:,} |
| Est. avg output tokens/claim | ~{avg_output_tokens:,} |
| Est. total input tokens | ~{total_claims_est*avg_input_tokens:,} |
| Est. total output tokens | ~{total_claims_est*avg_output_tokens:,} |
| Est. total cost (USD) | ~${cost_total:.2f} |

**Pricing assumptions:** claude-sonnet-4-6 at $3.00/MTok input, $15.00/MTok output (Anthropic list pricing, June 2026).
Images are encoded as JPEG base64; each image adds ~1000–2500 input tokens depending on resolution.

## Batching, caching, and rate-limit strategy

- **Disk cache:** Each claim is hashed (SHA-256 over image bytes + context JSON). Reruns skip cached claims entirely, making reruns free and deterministic.
- **One call per claim:** All images for a claim are submitted in a single multi-image message. This minimizes RPM usage and gives the model cross-image context for identity-mismatch detection.
- **Temperature 0:** All calls use temperature=0 for determinism.
- **Retry with exponential backoff:** Up to 4 retries on rate-limit (429) and server errors (5xx), starting at 8s doubling each attempt.
- **Graceful degradation:** If a call fails after all retries, the claim row uses safe defaults (`not_enough_information`, `severity=unknown`) rather than crashing the batch.
- **TPM/RPM headroom:** With ~{total_claims_est} claims and ~{avg_input_tokens} input tokens each, peak throughput is ~{total_claims_est*avg_input_tokens//60:,} TPM — well within claude-sonnet-4-6 limits. Sequential processing keeps RPM low (~1 RPM), avoiding burst throttling.
"""

    REPORT_MD.write_text(report, encoding="utf-8")
    print(f"\n--- Scores ---")
    print(f"claim_status macro-F1: {macro_f1:.3f}")
    for field, acc in sorted(per_field.items()):
        print(f"  {field}: {acc:.3f}")
    print(f"  (set-field Jaccard diagnostic — risk_flags: {per_field_partial['risk_flags']:.3f}, "
          f"supporting_image_ids: {per_field_partial['supporting_image_ids']:.3f})")
    print(f"\nReport written to {REPORT_MD}")
    print(f"Predictions written to {PREDICTIONS_CSV}")


if __name__ == "__main__":
    main()
