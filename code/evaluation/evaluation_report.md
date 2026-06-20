# Evaluation Report

## Scores on sample_claims.csv (n=20)

**claim_status macro-F1: 0.611**  ·  **schema: PASS**

### Per-field accuracy
| Field | Accuracy |
|-------|----------|
| claim_status | 0.700 |
| evidence_standard_met | 0.800 |
| issue_type | 0.450 |
| object_part | 0.800 |
| risk_flags | 0.400 |
| severity | 0.300 |
| supporting_image_ids | 0.800 |
| valid_image | 0.950 |

*Set fields (`risk_flags`, `supporting_image_ids`) use exact-set match above, which agrees with the harness `/evaluate` scorer. Jaccard partial-credit diagnostic — risk_flags: 0.620, supporting_image_ids: 0.825.*

## Per-case breakdown
| user_id | object | gold | pred | result |
|---------|--------|------|------|--------|
| user_001 | car | supported | supported | OK |
| user_002 | car | not_enough_information | not_enough_information | OK |
| user_004 | car | supported | not_enough_information | MISS |
| user_007 | car | supported | supported | OK |
| user_005 | car | contradicted | not_enough_information | MISS |
| user_006 | car | not_enough_information | contradicted | MISS |
| user_003 | car | supported | supported | OK |
| user_008 | car | contradicted | contradicted | OK |
| user_009 | laptop | supported | supported | OK |
| user_010 | laptop | supported | supported | OK |
| user_011 | laptop | supported | supported | OK |
| user_012 | laptop | supported | supported | OK |
| user_018 | laptop | supported | supported | OK |
| user_020 | laptop | contradicted | supported | MISS |
| user_015 | package | supported | supported | OK |
| user_030 | package | supported | not_enough_information | MISS |
| user_031 | package | supported | supported | OK |
| user_032 | package | not_enough_information | not_enough_information | OK |
| user_033 | package | contradicted | contradicted | OK |
| user_034 | package | contradicted | supported | MISS |

## Operational analysis

| Metric | Value |
|--------|-------|
| Model | claude-sonnet-4-6 |
| Sample claims processed | 20 |
| Test claims to process | 44 |
| Total claims (sample + test) | 64 |
| Avg latency per claim | 7.8s |
| Total sample run time | 156.4s |
| Disk cache entries present | 337 |
| Est. avg input tokens/claim | ~3,000 |
| Est. avg output tokens/claim | ~300 |
| Est. total input tokens | ~192,000 |
| Est. total output tokens | ~19,200 |
| Est. total cost (USD) | ~$0.86 |

**Pricing assumptions:** claude-sonnet-4-6 at $3.00/MTok input, $15.00/MTok output (Anthropic list pricing, June 2026).
Images are encoded as JPEG base64; each image adds ~1000–2500 input tokens depending on resolution.

## Batching, caching, and rate-limit strategy

- **Disk cache:** Each claim is hashed (SHA-256 over image bytes + context JSON). Reruns skip cached claims entirely, making reruns free and deterministic.
- **One call per claim:** All images for a claim are submitted in a single multi-image message. This minimizes RPM usage and gives the model cross-image context for identity-mismatch detection.
- **Temperature 0:** All calls use temperature=0 for determinism.
- **Retry with exponential backoff:** Up to 4 retries on rate-limit (429) and server errors (5xx), starting at 8s doubling each attempt.
- **Graceful degradation:** If a call fails after all retries, the claim row uses safe defaults (`not_enough_information`, `severity=unknown`) rather than crashing the batch.
- **TPM/RPM headroom:** With ~64 claims and ~3000 input tokens each, peak throughput is ~3,200 TPM — well within claude-sonnet-4-6 limits. Sequential processing keeps RPM low (~1 RPM), avoiding burst throttling.
