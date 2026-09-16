import unittest

from traceone.degradation import (
    compare_paired_outcomes,
    compare_stratified_outcomes,
    holm_bonferroni,
    mcnemar_detection_power,
    one_sided_mcnemar,
    plan_mcnemar,
)


class DegradationTests(unittest.TestCase):
    def test_exact_one_sided_mcnemar(self) -> None:
        self.assertEqual(one_sided_mcnemar(3, 0), 0.125)
        self.assertAlmostEqual(one_sided_mcnemar(5, 1), 7 / 64)

    def test_reports_degradation_and_missingness_separately(self) -> None:
        baseline = {f"q{i}": True for i in range(10)} | {"missing-now": True}
        current = {f"q{i}": (i >= 6) for i in range(10)} | {"new": True}
        result = compare_paired_outcomes(
            baseline,
            current,
            alpha=0.05,
            minimum_effect=0.2,
            require_complete_pairing=False,
        )
        self.assertEqual(result.status, "degraded")
        self.assertEqual(result.regressions, 6)
        self.assertEqual(result.baseline_only_items, 1)
        self.assertEqual(result.current_only_items, 1)

    def test_holm_preserves_original_order(self) -> None:
        result = holm_bonferroni([0.03, 0.001, 0.2])
        self.assertFalse(result[0]["reject"])
        self.assertTrue(result[1]["reject"])
        self.assertFalse(result[2]["reject"])

    def test_strict_pairing_refuses_different_item_sets(self) -> None:
        result = compare_paired_outcomes(
            {"a": True, "baseline-only": True},
            {"a": False},
        )
        self.assertEqual(result.status, "invalid_comparison")
        self.assertFalse(result.complete_pairing)

    def test_invalid_current_response_counts_as_failure_by_default(self) -> None:
        result = compare_paired_outcomes(
            {"a": True, "b": True}, {"a": None, "b": True}
        )
        self.assertEqual(result.paired_items, 2)
        self.assertEqual(result.regressions, 1)
        self.assertEqual(result.invalid_current_items, 1)

    def test_family_tests_receive_holm_correction(self) -> None:
        baseline = {f"a{i}": True for i in range(8)} | {
            f"b{i}": True for i in range(8)
        }
        current = {f"a{i}": False for i in range(8)} | {
            f"b{i}": True for i in range(8)
        }
        families = {item: item[0] for item in baseline}
        result = compare_stratified_outcomes(
            baseline, current, families, minimum_effect=0.1
        )
        by_family = {item["family"]: item for item in result["families"]}
        self.assertEqual(by_family["a"]["multiplicity_adjusted_status"], "degraded")
        self.assertEqual(
            by_family["b"]["multiplicity_adjusted_status"],
            "no_detected_degradation",
        )

    def test_power_increases_for_a_stronger_alternative(self) -> None:
        weak = mcnemar_detection_power(48, 0.08, 0.04, minimum_effect=0.02)
        strong = mcnemar_detection_power(48, 0.25, 0.01, minimum_effect=0.02)
        self.assertGreater(strong, weak)
        plan = plan_mcnemar(
            [24, 48], 0.25, 0.01, minimum_effect=0.02, target_power=0.5
        )
        self.assertEqual(len(plan["candidates"]), 2)
        self.assertIn(plan["recommended_items"], {24, 48})

    def test_exact_power_respects_size_under_the_null(self) -> None:
        power = mcnemar_detection_power(
            96, 0.1, 0.1, alpha=0.05, minimum_effect=0.0
        )
        self.assertLessEqual(power, 0.05)


if __name__ == "__main__":
    unittest.main()
