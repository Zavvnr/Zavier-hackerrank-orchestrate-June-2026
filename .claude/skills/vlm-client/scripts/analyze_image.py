#!/usr/bin/env python3
"""Anthropic Claude vision client for the evidence-review solution.

The single place the solution talks to a model (harness rule: all model calls go through here).
Features: env-only API key, temperature 0, on-disk caching keyed by inputs (reruns are free and
deterministic), and a token/cost helper. Default model is cost-first; override per call.

CLI smoke test: python analyze_image.py img_1.jpg [img_2.jpg ...] --prompt "describe the damage"
Requires: pip install anthropic ; export ANTHROPIC_API_KEY=...   (never read .env)
"""
import argparse
import base64
import hashlib
import json
import os
import sys
from pathlib import Path

# USD per 1M tokens, as of 2026-06. Update if Anthropic changes pricing.
PRICING = {
    "claude-haiku-4-5": {"in": 1.0, "out": 5.0},
    "claude-sonnet-4-6": {"in": 3.0, "out": 15.0},
    "claude-opus-4-8": {"in": 5.0, "out": 25.0},
}
DEFAULT_MODEL = "claude-haiku-4-5"   # cost-first; escalate to sonnet for hard cases
CACHE_DIR = Path(os.environ.get("EVR_CACHE_DIR", ".cache/vlm"))
MEDIA = {".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png", ".webp": "image/webp"}


def _media_type(path):
    return MEDIA.get(Path(path).suffix.lower(), "image/jpeg")


def _cache_key(model, prompt, image_bytes_list, max_tokens):
    h = hashlib.sha256()
    for part in (model, prompt, str(max_tokens)):
        h.update(part.encode())
        h.update(b"\0")
    for raw in image_bytes_list:
        h.update(hashlib.sha256(raw).digest())
    return h.hexdigest()


def estimate_image_tokens(width, height):
    """Rough Claude image-token estimate ~ (w*h)/750 (images are capped near 1568px/side)."""
    return int((width * height) / 750)


def estimate_cost(model, in_tokens, out_tokens):
    """USD cost for a call at standard (non-cached, non-batch) pricing."""
    price = PRICING.get(model, PRICING[DEFAULT_MODEL])
    return in_tokens / 1e6 * price["in"] + out_tokens / 1e6 * price["out"]


def analyze(image_paths, prompt, model=DEFAULT_MODEL, max_tokens=1024, use_cache=True):
    """Return the model's text for (prompt + images). Cached on disk by (model, prompt, images)."""
    image_bytes = [Path(p).read_bytes() for p in image_paths]
    key = _cache_key(model, prompt, image_bytes, max_tokens)
    cache_file = CACHE_DIR / f"{key}.json"
    if use_cache and cache_file.exists():
        return json.loads(cache_file.read_text())["text"]

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError("ANTHROPIC_API_KEY not set (export it; never read .env).")
    try:
        import anthropic
    except ImportError as exc:
        raise RuntimeError("anthropic SDK not installed: pip install anthropic") from exc

    blocks = []
    for path, raw in zip(image_paths, image_bytes):
        blocks.append({"type": "image", "source": {
            "type": "base64", "media_type": _media_type(path),
            "data": base64.standard_b64encode(raw).decode()}})
    blocks.append({"type": "text", "text": prompt})

    client = anthropic.Anthropic(api_key=api_key)
    resp = client.messages.create(
        model=model, max_tokens=max_tokens, temperature=0,
        messages=[{"role": "user", "content": blocks}])
    text = "".join(b.text for b in resp.content if getattr(b, "type", None) == "text")

    if use_cache:
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        cache_file.write_text(json.dumps({
            "text": text, "model": model,
            "usage": {"in": resp.usage.input_tokens, "out": resp.usage.output_tokens}}))
    return text


def main(argv=None):
    parser = argparse.ArgumentParser(description="Claude vision smoke test.")
    parser.add_argument("images", nargs="+")
    parser.add_argument("--prompt", default="Describe any visible damage and the object part.")
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--no-cache", action="store_true")
    args = parser.parse_args(argv)
    print(analyze(args.images, args.prompt, model=args.model, use_cache=not args.no_cache))
    return 0


if __name__ == "__main__":
    sys.exit(main())
