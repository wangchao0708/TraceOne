import unittest
import json
import random

from traceone.adapter import identify_text_adapted, load_adapter
from traceone.fingerprint import TARGET_MODELS, load_bank


class AdapterTests(unittest.TestCase):
    def test_packaged_adapter_matches_bank_and_targets(self) -> None:
        adapter = load_adapter()
        bank = load_bank()
        self.assertEqual(adapter["schema"], "traceone-ridge-adapter-v1")
        self.assertEqual(adapter["models"], list(TARGET_MODELS))
        self.assertEqual(adapter["bank_model_order"], bank["robust"]["model_order"])
        self.assertEqual(adapter["training_rows"], 415)
        self.assertEqual(len(adapter["feature_mean"]), 39)
        self.assertEqual(len(adapter["weights"]), 39)
        self.assertEqual(len(adapter["weights"][0]), 5)

    def test_adapter_cannot_bypass_outer_unknown(self) -> None:
        rng = random.Random(19)
        grid = [[rng.randint(1, 355) for _ in range(35)] for _ in range(9)]
        result = identify_text_adapted(json.dumps({"numbers": grid}))
        self.assertEqual(result.status, "unknown")
        self.assertEqual(result.outer_guard.status, "unknown")


if __name__ == "__main__":
    unittest.main()
