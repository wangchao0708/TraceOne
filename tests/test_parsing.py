import unittest

from traceone.parsing import parse_grid_response, parse_identity_response


class ParsingTests(unittest.TestCase):
    def test_accepts_exact_array(self) -> None:
        result = parse_identity_response("[1, 2, 355]", expected_count=3)
        self.assertTrue(result.valid)
        self.assertEqual(result.numbers, (1, 2, 355))

    def test_rejects_wrapped_or_repaired_output(self) -> None:
        wrapped = parse_identity_response("answer: [1, 2, 3]", expected_count=3)
        self.assertFalse(wrapped.valid)
        self.assertTrue(wrapped.errors[0].startswith("invalid_json:"))

        invalid = parse_identity_response("[1, 0, true, 356]", expected_count=4)
        self.assertFalse(invalid.valid)
        self.assertEqual(invalid.numbers, (1,))
        self.assertIn("item_1_out_of_range", invalid.errors)
        self.assertIn("item_2_not_integer", invalid.errors)
        self.assertIn("item_3_out_of_range", invalid.errors)

    def test_grid_requires_exact_shape(self) -> None:
        valid = parse_grid_response("[[1, 2], [3, 4]]", rows=2, columns=2)
        self.assertTrue(valid.valid)
        self.assertEqual(valid.numbers, (1, 2, 3, 4))

        invalid = parse_grid_response("[[1], [2, 3]]", rows=2, columns=2)
        self.assertFalse(invalid.valid)
        self.assertIn("row_0_wrong_count:1", invalid.errors)


if __name__ == "__main__":
    unittest.main()
