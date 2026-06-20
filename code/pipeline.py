"""Per-claim orchestration: load context, call VLM, post-process results."""

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent))

import vlm
import rules_engine
import schema
import consistency


DATASET_ROOT = pathlib.Path(__file__).parent.parent / "dataset"


def process_claim(
    row: dict,
    user_history: dict[str, dict],
    evidence_requirements: list[dict],
) -> dict:
    """Process a single claim row and return a complete output dict."""
    user_id = row["user_id"]
    image_paths_str = row["image_paths"]
    user_claim = row["user_claim"]
    claim_object = row.get("claim_object", "car")

    # Resolve image paths relative to dataset root.
    image_paths = [DATASET_ROOT / p.strip() for p in image_paths_str.split(";") if p.strip()]

    # Look up user history.
    hist = user_history.get(user_id, {})
    hist_summary = hist.get("history_summary", "No history available.")
    hist_flags = hist.get("history_flags", "none")

    # Get relevant evidence requirements.
    req_texts = rules_engine.get_relevant_requirements(evidence_requirements, claim_object, user_claim)

    # Call the VLM.
    vlm_result = vlm.analyze_claim(
        image_paths=image_paths,
        claim_object=claim_object,
        user_claim=user_claim,
        evidence_requirements=req_texts,
        user_history_summary=hist_summary,
        user_risk_flags=hist_flags,
    )

    # If the VLM returned an error, fall back to safe defaults.
    if "_error" in vlm_result:
        prediction = dict(schema.SAFE_DEFAULTS)
        prediction["risk_flags"] = rules_engine.build_risk_flags("", hist_flags, user_claim)
    else:
        prediction = dict(schema.SAFE_DEFAULTS)
        prediction.update(vlm_result)
        # Merge risk flags: VLM flags + user history flags + injection detection.
        prediction["risk_flags"] = rules_engine.build_risk_flags(
            vlm_result.get("risk_flags", "none"),
            hist_flags,
            user_claim,
        )

    # Validate and coerce to allowed values.
    prediction["user_id"] = user_id
    prediction["image_paths"] = image_paths_str
    prediction["user_claim"] = user_claim
    prediction["claim_object"] = claim_object
    prediction = schema.coerce_row(prediction)
    prediction = consistency.enforce_consistency(prediction)

    return prediction
