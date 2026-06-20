"""Allowed values, output schema constants, and row validation for the claim system."""

CLAIM_STATUS = frozenset({"supported", "contradicted", "not_enough_information"})

ISSUE_TYPES = frozenset({
    "dent", "scratch", "crack", "glass_shatter", "broken_part",
    "missing_part", "torn_packaging", "crushed_packaging", "water_damage",
    "stain", "none", "unknown",
})

CAR_PARTS = frozenset({
    "front_bumper", "rear_bumper", "door", "hood", "windshield",
    "side_mirror", "headlight", "taillight", "fender", "quarter_panel",
    "body", "unknown",
})

LAPTOP_PARTS = frozenset({
    "screen", "keyboard", "trackpad", "hinge", "lid", "corner",
    "port", "base", "body", "unknown",
})

PACKAGE_PARTS = frozenset({
    "box", "package_corner", "package_side", "seal", "label",
    "contents", "item", "unknown",
})

OBJECT_PARTS = {
    "car": CAR_PARTS,
    "laptop": LAPTOP_PARTS,
    "package": PACKAGE_PARTS,
}

RISK_FLAGS = frozenset({
    "none", "blurry_image", "cropped_or_obstructed", "low_light_or_glare",
    "wrong_angle", "wrong_object", "wrong_object_part", "damage_not_visible",
    "claim_mismatch", "possible_manipulation", "non_original_image",
    "text_instruction_present", "user_history_risk", "manual_review_required",
})

SEVERITY = frozenset({"none", "low", "medium", "high", "unknown"})

OUTPUT_COLUMNS = [
    "user_id", "image_paths", "user_claim", "claim_object",
    "evidence_standard_met", "evidence_standard_met_reason",
    "risk_flags", "issue_type", "object_part", "claim_status",
    "claim_status_justification", "supporting_image_ids", "valid_image", "severity",
]

SAFE_DEFAULTS = {
    "evidence_standard_met": "false",
    "evidence_standard_met_reason": "Unable to evaluate.",
    "risk_flags": "none",
    "issue_type": "unknown",
    "object_part": "unknown",
    "claim_status": "not_enough_information",
    "claim_status_justification": "Unable to process images.",
    "supporting_image_ids": "none",
    "valid_image": "false",
    "severity": "unknown",
}


def coerce_row(row: dict) -> dict:
    """Validate and coerce a prediction row to use only allowed values."""
    claim_object = row.get("claim_object", "car")
    valid_parts = OBJECT_PARTS.get(claim_object, CAR_PARTS)

    if row.get("claim_status") not in CLAIM_STATUS:
        row["claim_status"] = "not_enough_information"
    if row.get("issue_type") not in ISSUE_TYPES:
        row["issue_type"] = "unknown"
    if row.get("object_part") not in valid_parts:
        row["object_part"] = "unknown"
    if row.get("severity") not in SEVERITY:
        row["severity"] = "unknown"
    if row.get("evidence_standard_met") not in {"true", "false"}:
        row["evidence_standard_met"] = "false"
    if row.get("valid_image") not in {"true", "false"}:
        row["valid_image"] = "false"

    # Validate risk flags — keep only known tokens, and never mix the 'none'
    # sentinel with real flags (the schema treats 'none;flag' as invalid).
    raw_flags = row.get("risk_flags", "none")
    tokens = [t.strip() for t in raw_flags.split(";") if t.strip()]
    valid_tokens = [t for t in tokens if t in RISK_FLAGS and t != "none"]
    row["risk_flags"] = ";".join(valid_tokens) if valid_tokens else "none"

    # Validate supporting_image_ids — must be img_\d+ tokens or "none".
    raw_ids = row.get("supporting_image_ids", "none")
    if raw_ids.strip().lower() == "none":
        row["supporting_image_ids"] = "none"
    else:
        id_tokens = [t.strip() for t in raw_ids.split(";") if t.strip()]
        row["supporting_image_ids"] = ";".join(id_tokens) if id_tokens else "none"

    return row


def validate_prediction_rows(rows: list[dict]) -> list[str]:
    """Return schema/allowed-value errors for prediction rows (empty list = valid).

    Mirrors .claude/skills/eval-harness/scripts/validate_output.py so the eval and the
    standalone harness validator agree. Kept inside code/ so the submission is self-contained.
    """
    errors: list[str] = []
    for n, row in enumerate(rows, start=2):  # row 2 = first data row in the CSV
        obj = row.get("claim_object", "")
        if obj not in OBJECT_PARTS:
            errors.append(f"row {n}: claim_object '{obj}' invalid")
        if row.get("claim_status") not in CLAIM_STATUS:
            errors.append(f"row {n}: claim_status '{row.get('claim_status')}' invalid")
        if row.get("issue_type") not in ISSUE_TYPES:
            errors.append(f"row {n}: issue_type '{row.get('issue_type')}' invalid")
        if row.get("severity") not in SEVERITY:
            errors.append(f"row {n}: severity '{row.get('severity')}' invalid")
        if row.get("object_part") not in OBJECT_PARTS.get(obj, CAR_PARTS):
            errors.append(f"row {n}: object_part '{row.get('object_part')}' invalid for '{obj}'")
        for field in ("evidence_standard_met", "valid_image"):
            if row.get(field) not in {"true", "false"}:
                errors.append(f"row {n}: {field} '{row.get(field)}' not true/false")
        flags = [t.strip() for t in row.get("risk_flags", "").split(";") if t.strip()]
        if not flags:
            errors.append(f"row {n}: risk_flags empty (use 'none')")
        if "none" in flags and len(flags) > 1:
            errors.append(f"row {n}: risk_flags mixes 'none' with other flags")
        for flag in flags:
            if flag not in RISK_FLAGS:
                errors.append(f"row {n}: risk_flag '{flag}' invalid")
    return errors
