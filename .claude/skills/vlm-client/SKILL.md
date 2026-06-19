---
name: vlm-client
description: How the solution calls the Anthropic Claude vision model — model choice, batching, caching, prompt shape, and cost/latency estimation. Use when implementing or tuning any model call in code/.
---

# VLM client (Claude vision)

All model calls go through one client (`scripts/analyze_image.py` -> `code/vlm.py`). Centralizing the
call is what makes cost, caching, and determinism controllable, and keeps "all model calls go through
the VLM client" checkable.

## Model choice (cost-first)
| Model | $/1M in | $/1M out | Use for |
|---|---|---|---|
| `claude-haiku-4-5` | 1.0 | 5.0 | default — first pass on every claim |
| `claude-sonnet-4-6` | 3.0 | 15.0 | escalate hard / low-confidence / contradicted cases |
| `claude-opus-4-8` | 5.0 | 25.0 | rarely; only if Sonnet still misreads |

Output costs 5x input — keep responses short (a structured JSON object, not prose). Pricing as of
2026-06; if Anthropic changes it, update `PRICING` in `scripts/analyze_image.py` and this table.

## Token & cost estimation
- Image input tokens ~ `(width*height)/750`, capped ~1568px/side. A 1024x768 photo ~ 1k tokens.
- Per claim: ~1-3 images + a compact prompt ~ 1.5-4k input, ~0.3k output.
- 44 test rows x ~2 images is a few US cents on Haiku; the cache makes reruns free.

## Levers (use them, and report them in the operational analysis)
- **On-disk cache** keyed by (model, prompt, image bytes) -> reruns cost nothing and are deterministic
  (`EVR_CACHE_DIR`, default `.cache/vlm`).
- **Prompt caching** (Anthropic): put the long rubric in a cached block -> -90% on the repeated prefix.
- **Batch API**: -50% for the full non-interactive test run.
- **One call per claim**: send all of a claim's images in a single message and ask for every field at
  once as JSON. Never call per-image or per-field.
- **temperature 0** always. The key comes from `ANTHROPIC_API_KEY`; never read `.env`.

## Prompt shape
Cached system block = the rubric (`evidence-review` skill). User block = the images + claim + object +
the per-object allowed values, asking for a single JSON object with the 14 fields. Validate the JSON
against `evidence-review/reference/schema.md` before writing the row; on parse failure, fail safe to
`not_enough_information` / `unknown` with `manual_review_required`.

See `scripts/analyze_image.py` for the reference implementation (env key, base64, cache, usage).
