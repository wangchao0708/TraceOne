import json
import unittest
from pathlib import Path


PROJECT = Path(__file__).resolve().parents[1]


class ReleaseEvidenceTests(unittest.TestCase):
    def test_seven_model_third_confirmation_is_recorded_as_failed(self) -> None:
        evaluation = json.loads(
            (PROJECT / "data/confirmation-v10-evaluation.json").read_text()
        )
        supported = evaluation["profiles"]["supported"]
        self.assertEqual(supported["samples"], 105)
        self.assertEqual(supported["format_compliant"], 105)
        self.assertEqual(supported["requested_label_matches"], 103)
        self.assertEqual(
            supported["per_model"]["gpt-6-sol"]["requested_label_matches"], 13
        )

    def test_seven_model_second_confirmation_is_recorded_as_failed(self) -> None:
        evaluation = json.loads(
            (PROJECT / "data/confirmation-v9-evaluation.json").read_text()
        )
        supported = evaluation["profiles"]["supported"]
        self.assertEqual((supported["requested_label_matches"], supported["samples"]), (98, 105))
        self.assertEqual(supported["per_model"]["gpt-5.6-sol"]["requested_label_matches"], 13)
        self.assertEqual(supported["per_model"]["gpt-6-sol"]["requested_label_matches"], 12)
        comparison = json.loads(
            (PROJECT / "data/confirmation-v9-head-to-head.json").read_text()
        )
        self.assertEqual(comparison["modeltrace_one_call"]["requested_label_matches"], 96)
        self.assertEqual(comparison["modeltrace_three_call"]["requested_label_matches"], 35)

    def test_final_confirmation_and_head_to_head_claims(self) -> None:
        evaluation = json.loads(
            (PROJECT / "data/confirmation-v7-evaluation.json").read_text()
        )
        supported = evaluation["profiles"]["supported"]
        self.assertEqual((supported["requested_label_matches"], supported["samples"]), (75, 75))
        self.assertTrue(
            all(item["requested_label_matches"] == 15 for item in supported["per_model"].values())
        )

        comparison = json.loads(
            (PROJECT / "data/confirmation-v7-head-to-head.json").read_text()
        )
        self.assertEqual(
            comparison["traceone_one_call"]["requested_label_matches"], 75
        )
        self.assertEqual(
            comparison["modeltrace_one_call"]["requested_label_matches"], 74
        )
        self.assertEqual(
            comparison["modeltrace_three_call"]["requested_label_matches"], 25
        )

    def test_open_world_and_power_claims(self) -> None:
        open_world = json.loads(
            (PROJECT / "data/open-world-development-v2.json").read_text()
        )["unseen_label_ood"]
        self.assertEqual(
            open_world["traceone_supported_false_acceptance"]["count"], 24
        )
        self.assertEqual(
            open_world["modeltrace_closed_set_false_identification"]["count"],
            288,
        )
        power = json.loads(
            (PROJECT / "data/degradation-power-plan-v2.json").read_text()
        )
        self.assertEqual(power["recommended_items"], 192)

    def test_public_confirmation_has_no_private_log_fields(self) -> None:
        rows = [
            json.loads(line)
            for line in (PROJECT / "data/public/confirmation-v7.jsonl")
            .read_text()
            .splitlines()
            if line.strip()
        ]
        self.assertEqual(len(rows), 75)
        self.assertEqual(len({row["sample_id"] for row in rows}), 75)
        for row in rows:
            self.assertNotIn("thread_id", row)
            self.assertNotIn("stderr_tail", row)


if __name__ == "__main__":
    unittest.main()
