import hashlib
import json
import unittest
from collections import Counter
from datetime import datetime
from pathlib import Path

import numpy as np

from traceone.optimized import EIGHT_TARGET_MODELS, identify_text_optimized, load_optimized

ROOT=Path(__file__).resolve().parents[1]


class EightReleaseTests(unittest.TestCase):
    def test_eight_model_artifact_and_legacy_are_separate(self):
        artifact=load_optimized()
        self.assertEqual(artifact["models"],list(EIGHT_TARGET_MODELS))
        self.assertEqual((artifact["training_rows"],artifact["calibration_rows"]),(571,124))
        self.assertEqual(artifact["classifier"],"ridge")
        self.assertEqual(artifact["group_weights"],{"bank":1,"raw":1,"structure":.5,"order":0})
        self.assertEqual(np.asarray(artifact["weights"]).shape,(591,8))
        self.assertTrue(np.isfinite(artifact["weights"]).all())
        self.assertEqual((ROOT/"src/traceone/data/codex_low_v8_optimized.json").read_bytes(),
                         (ROOT/"dist/data/codex_low_v8_optimized.json").read_bytes())

    def test_confirmation_is_fresh_balanced_and_private_fields_are_absent(self):
        rows=[json.loads(line) for line in (ROOT/"data/public/confirmation-v12.jsonl").read_text().splitlines()]
        frozen=json.loads((ROOT/"config/release-candidate-v12.json").read_text())
        self.assertEqual(len(rows),len({r["sample_id"] for r in rows}))
        self.assertEqual(Counter(r["requested_model"] for r in rows),Counter({m:15 for m in EIGHT_TARGET_MODELS}))
        for r in rows:
            self.assertGreater(datetime.fromisoformat(r["collected_at"]),datetime.fromisoformat(frozen["frozen_at"]))
            self.assertEqual(r["provider"],"openai-codex-subscription")
            self.assertEqual(r["runtime"],"codex-cli 0.159.2")
            self.assertEqual(r["reasoning_effort"],"low")
            self.assertEqual(r["run_id"],"confirmation-v12")
            self.assertEqual(r["split"],"confirmation")
            self.assertEqual(r["prompt_sha256"],frozen["prompt"]["normalized_text_sha256"])
            self.assertIsNone(r["output_schema_sha256"])
            self.assertEqual(r["tool_item_count"],0)
            self.assertNotIn("thread_id",r)
            self.assertNotIn("stderr_tail",r)
        manifest=json.loads((ROOT/"data/public/confirmation-v12.manifest.json").read_text())
        self.assertEqual(manifest["sha256"],hashlib.sha256((ROOT/"data/public/confirmation-v12.jsonl").read_bytes()).hexdigest())

    def test_failed_research_gate_is_not_relabelled_as_passed(self):
        evaluation=json.loads((ROOT/"data/confirmation-v12-evaluation.json").read_text())
        self.assertEqual((evaluation["matches"],evaluation["samples"]),(101,120))
        self.assertEqual([evaluation["per_model"][m]["matches"] for m in EIGHT_TARGET_MODELS],
                         [15,14,15,14,9,14,10,10])
        self.assertEqual(sum(v["unknown"] for v in evaluation["per_model"].values()),9)
        self.assertEqual(sum(v["format_compliant"] for v in evaluation["per_model"].values()),61)
        release=json.loads((ROOT/"config/release-v0.3.0.json").read_text())
        self.assertFalse(release["confirmation"]["gate_passed"])
        self.assertFalse(release["deployment"]["public_site_updated"])

    def test_high_margin_cannot_bypass_support(self):
        rows=[json.loads(line) for line in (ROOT/"data/public/confirmation-v12.jsonl").read_text().splitlines()]
        artifact=load_optimized()
        artifact["support"]["thresholds"]=[0]*8
        result=identify_text_optimized(rows[0]["text"],artifact=artifact)
        self.assertEqual(result.adapter.status,"identified")
        self.assertEqual(result.status,"unknown")
        self.assertEqual(result.support_path,"optimized_rejected")


if __name__=="__main__":
    unittest.main()
