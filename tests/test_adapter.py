import unittest
import json
import random
from unittest.mock import patch

import numpy as np

from traceone.adapter import fit_ridge_adapter, identify_text_adapted, load_adapter
from traceone.fingerprint import TARGET_MODELS, load_bank


class AdapterTests(unittest.TestCase):
    def test_packaged_adapter_matches_bank_and_targets(self) -> None:
        adapter = load_adapter()
        bank = load_bank()
        self.assertEqual(adapter["schema"], "traceone-ridge-adapter-v1")
        self.assertEqual(adapter["models"], list(TARGET_MODELS))
        self.assertEqual(adapter["bank_model_order"], bank["robust"]["model_order"])
        self.assertEqual(adapter["training_rows"], 791)
        self.assertEqual(set(adapter["training_label_counts"].values()), {113})
        self.assertEqual(adapter["raw_weight"], 0.25)
        self.assertEqual(len(adapter["feature_mean"]), 403)
        self.assertEqual(len(adapter["weights"]), 403)
        self.assertEqual(len(adapter["weights"][0]), 7)

    def test_adapter_cannot_bypass_outer_unknown(self) -> None:
        rng = random.Random(19)
        grid = [[rng.randint(1, 355) for _ in range(35)] for _ in range(9)]
        result = identify_text_adapted(json.dumps({"numbers": grid}))
        self.assertEqual(result.status, "unknown")
        self.assertEqual(result.outer_guard.status, "unknown")

    def test_explicit_eighth_class_does_not_change_default_artifact(self) -> None:
        models = TARGET_MODELS + ("gpt-6.1-sol",)
        rng = random.Random(61)
        rows = [(model, [rng.randint(1, 355) for _ in range(315)])
                for model in models for _ in range(2)]
        artifact = fit_ridge_adapter(rows, load_bank(), models=models, raw_weight=0.25)
        self.assertEqual(artifact["models"], list(models))
        self.assertEqual(len(artifact["weights"][0]), 8)
        self.assertEqual(load_adapter()["models"], list(TARGET_MODELS))

    def test_raw_weight_boundary_tracks_bank_size(self) -> None:
        bank = {"robust": {"model_order": [str(i) for i in range(15)]}}
        matrix = np.random.default_rng(15).normal(size=(6, 50))
        rows = [("a" if i < 3 else "b", [i]) for i in range(6)]
        with patch("traceone.adapter.adapter_feature", side_effect=lambda numbers, bank, include_raw: matrix[numbers[0]]):
            artifact = fit_ridge_adapter(rows, bank, models=("a", "b"), alpha=2, raw_weight=0.25)
        standardized = (matrix - matrix.mean(0)) / matrix.std(0)
        standardized[:, 45:] *= 0.25
        targets = np.asarray([[1, 0]] * 3 + [[0, 1]] * 3)
        expected = np.linalg.solve(standardized.T @ standardized + 2 * np.eye(50),
                                   standardized.T @ (targets - targets.mean(0)))
        np.testing.assert_allclose(artifact["weights"], expected, atol=1e-12)

    def test_explicit_empty_or_duplicate_targets_are_rejected(self) -> None:
        for models in ((), ("a", "a")):
            with self.assertRaises(ValueError):
                fit_ridge_adapter([], load_bank(), models=models)


if __name__ == "__main__":
    unittest.main()
