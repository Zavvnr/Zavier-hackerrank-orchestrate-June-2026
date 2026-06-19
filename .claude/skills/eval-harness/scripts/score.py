#!/usr/bin/env python3
"""Score predictions against the labeled sample for the evidence-review task.

Usage: python score.py predictions.csv [--gold dataset/sample_claims.csv] [--json out.json]
Reports per-field accuracy, macro-F1 for claim_status, and set-overlap for the ';'-joined fields,
plus a per-case list of wrong fields. Stdlib only. Join key: image_paths (falls back to row order).
"""
import argparse
import csv
import json
import sys
from collections import defaultdict

LABEL_FIELDS = [
    "evidence_standard_met", "risk_flags", "issue_type", "object_part",
    "claim_status", "supporting_image_ids", "valid_image", "severity",
]
SET_FIELDS = {"risk_flags", "supporting_image_ids"}
KEY = "image_paths"


def _read(path):
    with open(path, newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def _norm(value):
    return (value or "").strip().lower()


def _as_set(value):
    return frozenset(t.strip().lower() for t in (value or "").split(";") if t.strip())


def _index(rows):
    """Index rows by KEY; return None if the key is missing or not unique."""
    by_key = {}
    for row in rows:
        k = row.get(KEY)
        if not k or k in by_key:
            return None
        by_key[k] = row
    return by_key


def score(pred_rows, gold_rows):
    pred_by_key, gold_by_key = _index(pred_rows), _index(gold_rows)
    if pred_by_key and gold_by_key and set(pred_by_key) == set(gold_by_key):
        pairs = [(pred_by_key[k], gold_by_key[k]) for k in gold_by_key]
        joined_on = "image_paths"
    else:
        pairs = list(zip(pred_rows, gold_rows))
        joined_on = "row order"

    n = len(pairs)
    present = [f for f in LABEL_FIELDS if gold_rows and f in gold_rows[0]]
    correct = defaultdict(int)
    tp, fp, fn = defaultdict(int), defaultdict(int), defaultdict(int)
    per_case = []

    for pred, gold in pairs:
        wrong = []
        for field in present:
            if field in SET_FIELDS:
                ok = _as_set(pred.get(field)) == _as_set(gold.get(field))
            else:
                ok = _norm(pred.get(field)) == _norm(gold.get(field))
            if ok:
                correct[field] += 1
            else:
                wrong.append(field)
        gp, gg = _norm(pred.get("claim_status")), _norm(gold.get("claim_status"))
        if gp == gg:
            tp[gg] += 1
        else:
            fp[gp] += 1
            fn[gg] += 1
        per_case.append({"key": gold.get(KEY, ""), "wrong": wrong})

    accuracy = {f: correct[f] / n for f in present} if n else {}
    classes = set(tp) | set(fp) | set(fn)
    classes.discard("")
    f1s = []
    for c in classes:
        p = tp[c] / (tp[c] + fp[c]) if (tp[c] + fp[c]) else 0.0
        r = tp[c] / (tp[c] + fn[c]) if (tp[c] + fn[c]) else 0.0
        f1s.append(2 * p * r / (p + r) if (p + r) else 0.0)
    macro_f1 = sum(f1s) / len(f1s) if f1s else 0.0

    return {"n": n, "joined_on": joined_on, "accuracy": accuracy,
            "claim_status_macro_f1": macro_f1, "per_case": per_case}


def main(argv=None):
    parser = argparse.ArgumentParser(description="Score predictions vs the labeled sample.")
    parser.add_argument("predictions")
    parser.add_argument("--gold", default="dataset/sample_claims.csv")
    parser.add_argument("--json", help="write the full result as JSON here")
    args = parser.parse_args(argv)

    result = score(_read(args.predictions), _read(args.gold))
    print(f"Scored {result['n']} rows  (joined on {result['joined_on']})")
    print(f"  {args.predictions}  vs  {args.gold}")
    print("-" * 50)
    for field, acc in sorted(result["accuracy"].items()):
        print(f"  {field:<28} {acc * 100:5.1f}%")
    print(f"  {'claim_status macro-F1':<28} {result['claim_status_macro_f1'] * 100:5.1f}%")
    print("-" * 50)
    n_perfect = sum(1 for c in result["per_case"] if not c["wrong"])
    print(f"  fully-correct rows: {n_perfect}/{result['n']}")
    if args.json:
        with open(args.json, "w", encoding="utf-8") as fh:
            json.dump(result, fh, indent=2)
        print(f"  wrote {args.json}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
