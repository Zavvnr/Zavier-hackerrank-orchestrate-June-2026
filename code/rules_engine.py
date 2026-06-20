"""Evidence requirement matching and risk flag logic."""

import re

# Keyword mapping from claim text / object type to requirement applies_to families.
_APPLIES_TO_KEYWORDS: dict[str, list[str]] = {
    "dent": ["dent or scratch"],
    "scratch": ["dent or scratch"],
    "crack": ["crack, broken, or missing part", "screen, keyboard, or trackpad"],
    "glass_shatter": ["crack, broken, or missing part"],
    "broken_part": ["crack, broken, or missing part"],
    "missing_part": ["crack, broken, or missing part", "contents or inner item"],
    "torn_packaging": ["crushed, torn, or seal damage"],
    "crushed_packaging": ["crushed, torn, or seal damage"],
    "water_damage": ["water, stain, or label damage"],
    "stain": ["water, stain, or label damage"],
}

_OBJECT_ISSUE_FAMILIES: dict[str, list[str]] = {
    "car": ["dent or scratch", "crack, broken, or missing part", "vehicle identity or orientation"],
    "laptop": ["screen, keyboard, or trackpad", "hinge, lid, corner, body, or port"],
    "package": ["crushed, torn, or seal damage", "water, stain, or label damage", "contents or inner item"],
}


def get_relevant_requirements(
    evidence_requirements: list[dict],
    claim_object: str,
    user_claim: str,
) -> list[str]:
    """Return a list of human-readable requirement strings relevant to this claim."""
    user_claim_lower = user_claim.lower()
    relevant: list[str] = []

    # Always include the general requirements that apply to all objects.
    for req in evidence_requirements:
        if req.get("claim_object") == "all":
            relevant.append(req["minimum_image_evidence"])

    # Include requirements for this specific object type.
    obj_families = _OBJECT_ISSUE_FAMILIES.get(claim_object, [])
    for req in evidence_requirements:
        if req.get("claim_object") != claim_object:
            continue
        applies_to = req.get("applies_to", "").lower()
        # Include if the applies_to family is relevant to the claim type.
        if any(family.lower() in applies_to or applies_to in family.lower() for family in obj_families):
            relevant.append(req["minimum_image_evidence"])

    return list(dict.fromkeys(relevant))  # deduplicate while preserving order


def detect_prompt_injection(user_claim: str) -> bool:
    """Return True if the user claim contains instruction-injection language."""
    injection_patterns = [
        r"ignore\s+(previous|prior|all)\s+instructions?",
        r"approve\s+(this|the)\s+claim\s+immediately",
        r"skip\s+manual\s+review",
        r"mark\s+(this|the\s+claim)\s+(as\s+)?(supported|approved)",
        r"follow\s+(it|this|the\s+note)\s+and\s+approve",
        r"system\s+reading\s+this\s+should",
        r"ignore\s+all\s+previous",
    ]
    text = user_claim.lower()
    return any(re.search(p, text) for p in injection_patterns)


def build_risk_flags(
    vlm_flags: str,
    user_history_flags: str,
    user_claim: str,
) -> str:
    """Merge VLM-detected flags, user history flags, and injection detection."""
    flags: list[str] = []

    # Flags from VLM.
    if vlm_flags and vlm_flags.lower() != "none":
        flags.extend(f.strip() for f in vlm_flags.split(";") if f.strip())

    # Flags from user history CSV.
    if user_history_flags and user_history_flags.lower() != "none":
        flags.extend(f.strip() for f in user_history_flags.split(";") if f.strip())

    # Prompt injection detection.
    if detect_prompt_injection(user_claim):
        if "text_instruction_present" not in flags:
            flags.append("text_instruction_present")
        if "manual_review_required" not in flags:
            flags.append("manual_review_required")

    # Deduplicate and filter to valid flags only.
    from schema import RISK_FLAGS
    seen: set[str] = set()
    deduped: list[str] = []
    for f in flags:
        if f not in seen and f in RISK_FLAGS:
            seen.add(f)
            deduped.append(f)

    return ";".join(deduped) if deduped else "none"
