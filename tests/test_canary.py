import unittest

from traceone.canary import generate_canary, score_canary


class CanaryTests(unittest.TestCase):
    def test_generation_is_deterministic(self) -> None:
        self.assertEqual(generate_canary(42, 2), generate_canary(42, 2))
        self.assertEqual(len(generate_canary(42, 2)["items"]), 8)

    def test_missing_and_wrong_answers_are_explicit(self) -> None:
        benchmark = {
            "schema": "traceone-canary-v1",
            "seed": 1,
            "items": [
                {"id": "a", "family": "x", "expected": "7"},
                {"id": "b", "family": "x", "expected": "8"},
                {"id": "c", "family": "x", "expected": "9"},
            ],
        }
        scored = score_canary(
            benchmark,
            [
                {"item_id": "a", "text": '{"answer":"7"}'},
                {"item_id": "b", "text": "7"},
            ],
        )
        self.assertEqual([item["correct"] for item in scored["items"]], [True, False, None])


if __name__ == "__main__":
    unittest.main()
