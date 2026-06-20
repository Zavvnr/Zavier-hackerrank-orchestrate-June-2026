"""Deterministic rubric-consistency layer, applied after the VLM and schema coercion.

These are principled invariants of the task definition (each verified to hold on every labeled
sample row), NOT memorized per-row answers:
  - not_enough_information  <=>  evidence_standard_met == "false"  (can't evaluate => insufficient)
  - not_enough_information   ->  severity == "unknown"             (can't assess the extent)
  - supported / contradicted ->  evidence_standard_met == "true"   (you could evaluate the claim)
  - supported                ->  severity in {low, medium, high}   (visible damage => not none/unknown)
  - manual_review_required is ADDED (never removed) on clear review triggers: a contradiction, a
    risky user history, or an identity/authenticity mismatch.

Toggle off with EVR_CONSISTENCY=0 to A/B it via /evaluate.
"""
import os

ENABLED = os.environ.get("EVR_CONSISTENCY", "1") != "0"

_REVIEW_TRIGGERS = frozenset({
    "user_history_risk", "claim_mismatch", "wrong_object",
    "non_original_image", "possible_manipulation",
})


def _flags(value: str) -> list:
    """Split risk_flags into real (non-'none') tokens, preserving order."""
    return [t.strip() for t in (value or "").split(";") if t.strip() and t.strip() != "none"]


def enforce_consistency(row: dict) -> dict:
    """Apply the rubric invariants to one prediction row, in place; return it."""
    if not ENABLED:
        return row

    status = row.get("claim_status", "not_enough_information")

    # Status is primary: evidence_standard_met is derived from it. A supported/contradicted verdict
    # means the claim could be evaluated; not_enough_information means it could not. (claim_status is
    # the model's most reliable field, so it wins when the two disagree.)
    if status == "not_enough_information":
        row["evidence_standard_met"] = "false"
        row["severity"] = "unknown"
    elif status in ("supported", "contradicted"):
        row["evidence_standard_met"] = "true"

    # Supported implies visible damage, so a 'none'/'unknown' severity is contradictory; repair it to
    # the modal 'medium'. This only fires on an already-inconsistent model output.
    if status == "supported" and row.get("severity") in ("none", "unknown"):
        row["severity"] = "medium"

    # manual_review_required is additive: add it on clear review triggers, never remove it.
    flags = _flags(row.get("risk_flags", "none"))
    trigger = status == "contradicted" or bool(set(flags) & _REVIEW_TRIGGERS)
    # A 'supported' verdict that cites no supporting image is internally weak -> flag for review.
    if status == "supported" and row.get("supporting_image_ids", "none").strip().lower() == "none":
        trigger = True
    if trigger and "manual_review_required" not in flags:
        flags.append("manual_review_required")
    row["risk_flags"] = ";".join(flags) if flags else "none"

    return row
