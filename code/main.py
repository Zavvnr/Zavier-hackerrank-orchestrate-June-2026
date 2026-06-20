"""Entry point: read dataset/claims.csv -> produce output.csv."""

import pathlib
import sys
import time

ROOT = pathlib.Path(__file__).parent.parent
sys.path.insert(0, str(pathlib.Path(__file__).parent))

import io_csv
import pipeline
import schema

DATASET_DIR = ROOT / "dataset"
CLAIMS_CSV = DATASET_DIR / "claims.csv"
USER_HISTORY_CSV = DATASET_DIR / "user_history.csv"
EVIDENCE_REQ_CSV = DATASET_DIR / "evidence_requirements.csv"
OUTPUT_CSV = ROOT / "output.csv"


def main() -> None:
    """Run the claim verification pipeline on claims.csv and write output.csv."""
    print(f"Reading claims from {CLAIMS_CSV}")
    claims = io_csv.read_claims(CLAIMS_CSV)
    user_history = io_csv.read_lookup(USER_HISTORY_CSV, "user_id")
    evidence_requirements = io_csv.read_list(EVIDENCE_REQ_CSV)

    print(f"Processing {len(claims)} claims...")
    results = []
    for i, row in enumerate(claims, start=1):
        print(f"  [{i}/{len(claims)}] {row['user_id']} | {row['claim_object']}")
        start = time.time()
        prediction = pipeline.process_claim(row, user_history, evidence_requirements)
        elapsed = time.time() - start
        print(f"    -> {prediction['claim_status']} | {elapsed:.1f}s")
        results.append(prediction)

    io_csv.write_output(results, OUTPUT_CSV, schema.OUTPUT_COLUMNS)
    print(f"\nOutput written to {OUTPUT_CSV} ({len(results)} rows)")

    schema_errors = schema.validate_prediction_rows(results)
    if schema_errors:
        print(f"WARNING: {len(schema_errors)} schema violation(s) in output.csv:")
        for err in schema_errors[:5]:
            print("  -", err)
    else:
        print("Schema check: output.csv conforms to the 14-column allowed-value schema.")


if __name__ == "__main__":
    main()
