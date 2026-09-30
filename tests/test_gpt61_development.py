import hashlib
import json
import unittest
from pathlib import Path

from scripts.evaluate_gpt61_development import prepare, read_rows, validate_corpus
from traceone.support import identify_text_supported

ROOT = Path(__file__).resolve().parents[1]


class GPT61DevelopmentTests(unittest.TestCase):
    def test_public_corpus_is_real_conditioned_and_private_fields_are_removed(self) -> None:
        path = ROOT / "data/public/gpt61-development-v1.jsonl"
        rows = read_rows(path)
        quality = validate_corpus(prepare(rows))
        self.assertEqual(quality["rows"], 489)
        self.assertEqual(quality["successful_calls"], 489)
        self.assertEqual(quality["strict_format_compliant"], 478)
        self.assertEqual(sum(r["requested_model"] == "gpt-6.1-sol" for r in rows), 178)
        manifest = json.loads((ROOT / "data/public/gpt61-development-v1.manifest.json").read_text())
        self.assertEqual(manifest["sha256"], hashlib.sha256(path.read_bytes()).hexdigest())
        evaluation = json.loads((ROOT / "data/gpt61-development-v1.json").read_text())
        self.assertEqual(evaluation["input_sha256"], manifest["sha256"])
        self.assertEqual(evaluation["quality"], quality)

    def test_failed_development_is_not_presented_as_confirmation(self) -> None:
        evaluation = json.loads((ROOT / "data/gpt61-development-v1.json").read_text())
        self.assertIn("NOT qualified", evaluation["status"])
        original = evaluation["original_prompt"]["eight_class_variants"][0]
        self.assertEqual((original["matches"], original["samples"]), (101, 120))
        self.assertEqual(original["per_model"]["gpt-6.1-sol"]["matches"], 8)
        best = evaluation["replacement_prompt"]["variants"][0]
        self.assertEqual((best["matches"], best["samples"]), (175, 192))
        self.assertEqual(best["per_model"]["gpt-6-astra"]["matches"], 19)
        self.assertEqual(best["per_model"]["gpt-6.1-sol"]["matches"], 19)
        self.assertEqual(best["with_existing_outer_guard"]["matches"], 171)
        self.assertEqual(evaluation["web_pilot"]["strict_format_compliant"], 5)

    def test_current_python_default_retains_every_historical_v11_prediction(self) -> None:
        rows = read_rows(ROOT / "data/public/confirmation-v10.jsonl")
        saved = json.loads((ROOT / "data/confirmation-v10-evaluation.json").read_text())
        expected = {r["sample_id"]: r["supported"] for r in saved["samples"]}
        for row in rows:
            result = identify_text_supported(row["text"])
            wanted = expected[row["sample_id"]]
            self.assertEqual(result.status, wanted["status"])
            self.assertEqual(result.label, wanted["label"])
            self.assertAlmostEqual(result.adapter.adapter_margin, wanted["adapter_margin"], places=10)
            self.assertAlmostEqual(result.support_distance, wanted["support_distance"], places=10)


if __name__ == "__main__":
    unittest.main()
