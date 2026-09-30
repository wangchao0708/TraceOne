import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from scripts.collect_codex import BUNDLED_CODEX_CANDIDATES, MODELS, PROSPECTIVE_MODELS
from scripts.collect_matrix import COLLECTABLE_MODELS
from traceone.fingerprint import TARGET_MODELS


class CollectionConfigTests(unittest.TestCase):
    def test_new_route_is_opt_in_not_a_release_target(self) -> None:
        self.assertEqual(MODELS, TARGET_MODELS)
        self.assertIn("gpt-6.1-sol", PROSPECTIVE_MODELS)
        self.assertIn("gpt-6.1-sol", COLLECTABLE_MODELS)
        self.assertNotIn("gpt-6.1-sol", MODELS)

    def test_current_desktop_binary_is_preferred(self) -> None:
        self.assertEqual(
            BUNDLED_CODEX_CANDIDATES[0].as_posix(),
            "/Applications/ChatGPT.app/Contents/Resources/codex-cli/bin/codex",
        )

    def test_prospective_route_cannot_trigger_an_eight_model_batch(self) -> None:
        project = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "responses"
            result = subprocess.run(
                [
                    sys.executable, str(project / "scripts/collect_matrix.py"),
                    "--output-dir", str(output),
                    "--prompt", str(project / "prompts/identity-v3-schema.txt"),
                    "--schema", str(project / "schemas/identity-v3.json"),
                    "--run-id", "no-call-test", "--split", "development",
                    "--repeat-start", "1", "--repeat-end", "1",
                    "--models", "gpt-5.5", "gpt-6.1-sol",
                ],
                capture_output=True, text=True, check=False,
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("collect the prospective", result.stderr)
            self.assertFalse(output.exists())


if __name__ == "__main__":
    unittest.main()
