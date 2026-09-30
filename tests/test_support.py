import json
import random
import unittest

from traceone.adapter import fit_ridge_adapter, load_adapter
from traceone.fingerprint import TARGET_MODELS, load_bank
from traceone.support import fit_support, identify_text_supported, load_support


class SupportTests(unittest.TestCase):
    def test_packaged_support_matches_release_artifacts(self) -> None:
        support = load_support()
        adapter = load_adapter()
        bank = load_bank()
        self.assertEqual(support["schema"], "traceone-target-support-v1")
        self.assertEqual(support["models"], list(TARGET_MODELS))
        self.assertEqual(support["bank_model_order"], bank["robust"]["model_order"])
        self.assertEqual(support["training_rows"], adapter["training_rows"])
        self.assertEqual(len(support["precision"]), 48)
        self.assertEqual(len(support["distance_thresholds"]), 7)

    def test_outer_guard_still_precedes_support_rescue(self) -> None:
        rng = random.Random(23)
        grid = [[rng.randint(1, 355) for _ in range(35)] for _ in range(9)]
        result = identify_text_supported(json.dumps({"numbers": grid}))
        self.assertEqual(result.status, "unknown")
        self.assertIsNone(result.support_passed)

    def test_explicit_eighth_class_support_uses_artifact_targets(self) -> None:
        bank = load_bank()
        models = TARGET_MODELS + ("gpt-6.1-sol",)
        rng = random.Random(62)
        rows = [(model, [rng.randint(1, 355) for _ in range(315)])
                for model in models for _ in range(2)]
        adapter = fit_ridge_adapter(rows, bank, models=models, raw_weight=0.25)
        support = fit_support(rows, bank, adapter)
        self.assertEqual(support["models"], list(models))
        self.assertEqual(len(support["centroids"]), 8)
        self.assertEqual(len(support["distance_thresholds"]), 8)


if __name__ == "__main__":
    unittest.main()
