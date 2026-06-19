#!/usr/bin/env python3
"""Validate a predictions CSV against the Multi-Modal Evidence Review submission schema.

Usage: python validate_output.py [output.csv] [--input dataset/claims.csv]
Exit code 0 = valid (submittable); non-zero = schema/value errors found.
Stdlib only. Allowed-value lists mirror problem_statement.md / evidence-review/reference/schema.md.
"""
import argparse
import csv
import re
import sys

REQUIRED_COLUMNS = [
    "user_id", "image_paths", "user_claim", "claim_object",
    "evidence_standard_met", "evidence_standard_met_reason", "risk_flags",
    "issue_type", "object_part", "claim_status", "claim_status_justification",
    "supporting_image_ids", "valid_image", "severity",
]
CLAIM_OBJECTS = {"car", "laptop", "package"}
BOOLS = {"true", "false"}
CLAIM_STATUS = {"supported", "contradicted", "not_enough_information"}
SEVERITY = {"none", "low", "medium", "high", "unknown"}
ISSUE_TYPES = {
    "dent", "scratch", "crack", "glass_shatter", "broken_part", "missing_part",
    "torn_packaging", "crushed_packaging", "water_damage", "stain", "none", "unknown",
}
RISK_FLAGS = {
    "none", "blurry_image", "cropped_or_obstructed", "low_light_or_glare", "wrong_angle",
    "wrong_object", "wrong_object_part", "damage_not_visible", "claim_mismatch",
    "possible_manipulation", "non_original_image", "text_instruction_present",
    "user_history_risk", "manual_review_required",
}
OBJECT_PARTS = {
    "car": {"front_bumper", "rear_bumper", "door", "hood", "windshield", "side_mirror",
            "headlight", "taillight", "fender", "quarter_panel", "body", "unknown"},
    "laptop": {"screen", "keyboard", "trackpad", "hinge", "lid", "corner", "port",
               "base", "body", "unknown"},
    "package": {"box", "package_corner", "package_side", "seal", "label", "contents",
                "item", "unknown"},
}
IMAGE_ID = re.compile(r"^[A-Za-z0-9_.\-]+$")


def _split(value):
    """Split a ';'-joined cell into trimmed, non-empty tokens."""
    return [t.strip() for t in value.split(";") if t.strip()]


def validate(path, input_path=None):
    """Return a list of human-readable error strings (empty list = valid)."""
    errors = []
    with open(path, newline="", encoding="utf-8") as fh:
        rows = list(csv.reader(fh))
    if not rows:
        return [f"{path}: file is empty"]

    if rows[0] != REQUIRED_COLUMNS:
        errors.append("header mismatch:\n    expected: " + ",".join(REQUIRED_COLUMNS)
                      + "\n    found:    " + ",".join(rows[0]))
        return errors  # positions unreliable; stop

    col = {name: i for i, name in enumerate(REQUIRED_COLUMNS)}
    for n, row in enumerate(rows[1:], start=2):
        if len(row) != len(REQUIRED_COLUMNS):
            errors.append(f"row {n}: {len(row)} fields, expected {len(REQUIRED_COLUMNS)}")
            continue
        cell = lambda name: row[col[name]].strip()

        obj = cell("claim_object")
        if obj not in CLAIM_OBJECTS:
            errors.append(f"row {n}: claim_object '{obj}' invalid")
        if cell("evidence_standard_met").lower() not in BOOLS:
            errors.append(f"row {n}: evidence_standard_met '{cell('evidence_standard_met')}' not true/false")
        if cell("valid_image").lower() not in BOOLS:
            errors.append(f"row {n}: valid_image '{cell('valid_image')}' not true/false")
        if cell("claim_status") not in CLAIM_STATUS:
            errors.append(f"row {n}: claim_status '{cell('claim_status')}' invalid")
        if cell("issue_type") not in ISSUE_TYPES:
            errors.append(f"row {n}: issue_type '{cell('issue_type')}' invalid")
        if cell("severity") not in SEVERITY:
            errors.append(f"row {n}: severity '{cell('severity')}' invalid")

        part = cell("object_part")
        allowed = OBJECT_PARTS.get(obj)
        if allowed and part not in allowed:
            errors.append(f"row {n}: object_part '{part}' not valid for {obj}")

        flags = _split(cell("risk_flags"))
        if not flags:
            errors.append(f"row {n}: risk_flags empty (use 'none')")
        else:
            for f in flags:
                if f not in RISK_FLAGS:
                    errors.append(f"row {n}: risk_flag '{f}' invalid")
            if "none" in flags and len(flags) > 1:
                errors.append(f"row {n}: risk_flags mixes 'none' with other flags")

        sup = cell("supporting_image_ids")
        if sup and sup != "none":
            for img in _split(sup):
                if not IMAGE_ID.match(img):
                    errors.append(f"row {n}: supporting_image_id '{img}' malformed")

    if input_path:
        try:
            with open(input_path, newline="", encoding="utf-8") as fh:
                n_in = sum(1 for _ in csv.reader(fh)) - 1
            if (len(rows) - 1) != n_in:
                errors.append(f"row count {len(rows) - 1} != input rows {n_in} ({input_path})")
        except OSError as exc:
            errors.append(f"could not read input for row-count check: {exc}")
    return errors


def main(argv=None):
    parser = argparse.ArgumentParser(description="Validate predictions CSV schema.")
    parser.add_argument("path", nargs="?", default="output.csv")
    parser.add_argument("--input", help="optional input CSV for a row-count check")
    args = parser.parse_args(argv)

    errors = validate(args.path, args.input)
    if errors:
        print(f"INVALID: {args.path} — {len(errors)} problem(s):")
        for e in errors[:50]:
            print("  -", e)
        if len(errors) > 50:
            print(f"  ... and {len(errors) - 50} more")
        return 1
    print(f"VALID: {args.path} conforms to the 14-column schema and allowed values.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
