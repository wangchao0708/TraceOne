import json
import random
import unittest

from traceone.fingerprint import ADAPTIVE_GUARD, BALANCED_GUARD, classify_parsed, load_bank
from traceone.parsing import ParseResult


class FingerprintTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.bank = load_bank()

    def test_uniform_sequence_is_rejected(self) -> None:
        rng = random.Random(7)
        numbers = tuple(rng.randint(1, 355) for _ in range(315))
        parsed = ParseResult(numbers, True, (), 315, 315)
        result = classify_parsed(parsed, bank=self.bank, guard=BALANCED_GUARD)
        self.assertEqual(result.status, "unknown")
        self.assertIn("low_absolute_similarity", result.guard_reasons)

    def test_short_sequence_is_rejected_before_scoring(self) -> None:
        parsed = ParseResult((1, 2, 3), True, (), 3, 3)
        result = classify_parsed(parsed, bank=self.bank, guard=BALANCED_GUARD)
        self.assertEqual(result.status, "unknown")
        self.assertEqual(result.guard_reasons, ("insufficient_usable_numbers",))


if __name__ == "__main__":
    unittest.main()
