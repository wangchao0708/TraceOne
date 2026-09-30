import json
import random
import unittest

import numpy as np

from traceone.fingerprint import load_bank
from traceone.optimized import (EIGHT_TARGET_MODELS, feature_groups, fit_optimized,
                                identify_text_optimized, sequence_structure)


class OptimizedTests(unittest.TestCase):
    def test_features_include_repetition_and_order(self):
        numbers = [1 + i % 97 for i in range(315)]
        groups = feature_groups(numbers, load_bank())
        self.assertEqual({k: len(v) for k, v in groups.items()},
                         {"bank": 48, "raw": 355, "structure": 188, "order": 198})
        reversed_groups = feature_groups(numbers[::-1], load_bank())
        np.testing.assert_allclose(groups["raw"], reversed_groups["raw"])
        self.assertFalse(np.array_equal(groups["structure"], reversed_groups["structure"]))
        with self.assertRaises(ValueError):
            sequence_structure(numbers[:279])

    def test_fitting_and_prediction_cover_eight_routes(self):
        rng = random.Random(83)
        training = [(m, [rng.randint(1+40*i, 35+40*i) for _ in range(315)])
                    for i, m in enumerate(EIGHT_TARGET_MODELS) for _ in range(3)]
        calibration = [(m, [rng.randint(1+40*i, 35+40*i) for _ in range(315)])
                       for i, m in enumerate(EIGHT_TARGET_MODELS)]
        bank = load_bank()
        for kind in ("ridge", "kernel"):
            artifact = fit_optimized(training, calibration, bank,
                                     group_weights={"bank": 1, "raw": 1, "structure": .5},
                                     classifier=kind)
            self.assertEqual(artifact["models"], list(EIGHT_TARGET_MODELS))
            self.assertEqual(artifact["calibration_rows"], 8)
            # Calibration numbers are distinct from training, even in this small unit fixture.
            self.assertFalse({tuple(n) for _, n in training} & {tuple(n) for _, n in calibration})
            for label, numbers in training:
                text = json.dumps({"numbers": [numbers[i:i+35] for i in range(0,315,35)]})
                result = identify_text_optimized(text, bank=bank, artifact=artifact)
                self.assertIn(result.status, ("identified", "unknown"))
                self.assertEqual(max(result.adapter.adapter_scores, key=result.adapter.adapter_scores.get), label)
            invalid = identify_text_optimized('[1,2]', bank=bank, artifact=artifact)
            self.assertEqual(invalid.status, "unknown")
            self.assertIsNone(invalid.label)
            self.assertIsNone(invalid.support_distance)
            broken = json.dumps([[1]*35]*8 + [[356]*35])
            parsed = identify_text_optimized(broken, bank=bank, artifact=artifact)
            self.assertFalse(parsed.adapter.outer_guard.format_compliant)
            self.assertEqual(sum(len(v) for v in json.loads(broken)),315)
            self.assertEqual(parsed.status,"unknown")
            self.assertIsNone(parsed.adapter.adapter_margin)

    def test_invalid_training_conditions_are_rejected(self):
        with self.assertRaises(ValueError):
            fit_optimized([], [], load_bank(), group_weights={"bank": 1})
        with self.assertRaises(ValueError):
            fit_optimized([], [], load_bank(), group_weights={"typo": 1})


if __name__ == "__main__":
    unittest.main()
