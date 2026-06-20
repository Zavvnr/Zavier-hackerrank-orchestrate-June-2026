"""Offline unit tests for the deterministic glue: consistency layer, best-of-N logic, JSON salvage.

The Anthropic SDK is stubbed, so these run with no API key and no network.
Run: python code/tests/test_logic.py        (or: python -m unittest discover -s code/tests)
"""
import copy
import csv
import pathlib
import sys
import types
import unittest

CODE_DIR = pathlib.Path(__file__).resolve().parents[1]
ROOT = CODE_DIR.parent
sys.path.insert(0, str(CODE_DIR))

# Stub the anthropic SDK so importing vlm needs neither the package nor a key.
_fake = types.ModuleType("anthropic")


class RateLimitError(Exception):
    pass


class APIStatusError(Exception):
    def __init__(self, *a, status_code=500, **k):
        self.status_code = status_code
        super().__init__(*a)


class Anthropic:
    def __init__(self, *a, **k):
        pass


_fake.RateLimitError = RateLimitError
_fake.APIStatusError = APIStatusError
_fake.Anthropic = Anthropic
sys.modules.setdefault("anthropic", _fake)

import consistency
import schema
import vlm


def _raise(*a, **k):
    raise AssertionError("verifier should not run on this input")


class TestConsistency(unittest.TestCase):
    def _row(self, **over):
        row = dict(schema.SAFE_DEFAULTS)
        row.update(over)
        return row

    def test_nei_forces_evidence_and_severity(self):
        r = consistency.enforce_consistency(self._row(
            claim_status="not_enough_information", evidence_standard_met="true", severity="medium"))
        self.assertEqual(r["evidence_standard_met"], "false")
        self.assertEqual(r["severity"], "unknown")

    def test_status_is_primary_over_evidence(self):
        # A supported verdict with a stray evidence=false is repaired by trusting the status.
        r = consistency.enforce_consistency(self._row(
            claim_status="supported", evidence_standard_met="false", severity="medium",
            supporting_image_ids="img_1"))
        self.assertEqual(r["claim_status"], "supported")
        self.assertEqual(r["evidence_standard_met"], "true")

    def test_contradicted_sets_evidence_and_review(self):
        r = consistency.enforce_consistency(self._row(
            claim_status="contradicted", evidence_standard_met="false", risk_flags="none"))
        self.assertEqual(r["evidence_standard_met"], "true")
        self.assertIn("manual_review_required", r["risk_flags"])

    def test_supported_bad_severity_repaired(self):
        r = consistency.enforce_consistency(self._row(
            claim_status="supported", evidence_standard_met="true", severity="unknown",
            supporting_image_ids="img_1"))
        self.assertEqual(r["severity"], "medium")

    def test_user_history_risk_adds_review(self):
        r = consistency.enforce_consistency(self._row(
            claim_status="supported", evidence_standard_met="true", severity="medium",
            supporting_image_ids="img_1", risk_flags="user_history_risk"))
        self.assertIn("manual_review_required", r["risk_flags"])

    def test_supported_without_support_image_flags_review(self):
        r = consistency.enforce_consistency(self._row(
            claim_status="supported", evidence_standard_met="true", severity="medium",
            supporting_image_ids="none"))
        self.assertIn("manual_review_required", r["risk_flags"])

    def test_clean_supported_unchanged(self):
        r = consistency.enforce_consistency(self._row(
            claim_status="supported", evidence_standard_met="true", severity="medium",
            supporting_image_ids="img_1", risk_flags="none"))
        self.assertEqual(r["risk_flags"], "none")
        self.assertEqual(r["severity"], "medium")

    def test_never_mixes_none_with_flags(self):
        r = consistency.enforce_consistency(self._row(
            claim_status="contradicted", evidence_standard_met="true", risk_flags="none"))
        toks = r["risk_flags"].split(";")
        self.assertFalse("none" in toks and len(toks) > 1)

    def test_idempotent_on_gold_sample(self):
        path = ROOT / "dataset" / "sample_claims.csv"
        if not path.exists():
            self.skipTest("sample_claims.csv not present")
        with open(path, encoding="utf-8") as fh:
            rows = list(csv.DictReader(fh))
        for r in rows:
            keep = {k: r.get(k) for k in ("claim_status", "evidence_standard_met", "severity")}
            keep_flags = frozenset(t for t in r["risk_flags"].split(";") if t)
            out = consistency.enforce_consistency(copy.deepcopy(r))
            for k, v in keep.items():
                self.assertEqual(out[k], v, f"{k} changed on a correct gold row")
            self.assertEqual(frozenset(t for t in out["risk_flags"].split(";") if t), keep_flags,
                             "risk_flags changed on a correct gold row")


class TestParseJson(unittest.TestCase):
    def test_plain(self):
        self.assertEqual(vlm._parse_json('{"a": 1}'), {"a": 1})

    def test_fenced(self):
        self.assertEqual(vlm._parse_json('```json\n{"a": 1}\n```'), {"a": 1})

    def test_prose_wrapped(self):
        self.assertEqual(vlm._parse_json('Here you go:\n{"a": 1}\nthanks'), {"a": 1})


class TestBestOfN(unittest.TestCase):
    def setUp(self):
        self._orig = (vlm.BEST_OF_N, vlm._cached_call, vlm._verify)
        vlm.BEST_OF_N = 3

    def tearDown(self):
        vlm.BEST_OF_N, vlm._cached_call, vlm._verify = self._orig

    def test_confident_baseline_skips_sampling(self):
        calls = []

        def fake_cached(client, content, system, temp, key):
            calls.append(key)
            return {"claim_status": "supported", "evidence_standard_met": "true", "risk_flags": "none"}

        vlm._cached_call = fake_cached
        vlm._verify = _raise
        out = vlm._best_of_n(None, [], "sys", "k")
        self.assertEqual(out["claim_status"], "supported")
        self.assertEqual(len(calls), 1)  # only the baseline; no extra candidates, no verifier

    def test_disagreement_uses_verifier(self):
        cands = {
            "k|lens0": {"claim_status": "supported", "evidence_standard_met": "true",
                        "risk_flags": "claim_mismatch"},
            "k|lens1": {"claim_status": "not_enough_information", "evidence_standard_met": "false",
                        "risk_flags": "claim_mismatch"},
            "k|lens2": {"claim_status": "contradicted", "evidence_standard_met": "true",
                        "risk_flags": "none"},
        }
        vlm._cached_call = lambda client, content, system, temp, key: cands[key]
        vlm._verify = lambda client, content, valid, key: 1  # pick the NEI candidate
        out = vlm._best_of_n(None, [], "sys", "k")
        self.assertEqual(out["claim_status"], "not_enough_information")

    def test_agreement_skips_verifier(self):
        same = {"claim_status": "contradicted", "evidence_standard_met": "true",
                "risk_flags": "damage_not_visible"}
        vlm._cached_call = lambda client, content, system, temp, key: dict(same)
        vlm._verify = _raise
        out = vlm._best_of_n(None, [], "sys", "k")
        self.assertEqual(out["claim_status"], "contradicted")


if __name__ == "__main__":
    unittest.main(verbosity=2)
