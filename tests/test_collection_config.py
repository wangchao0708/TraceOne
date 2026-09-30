import subprocess
import json
import sys
import tempfile
import unittest
from io import StringIO
from unittest.mock import patch
from pathlib import Path

from scripts.collect_codex import BUNDLED_CODEX_CANDIDATES, MODELS, PROSPECTIVE_MODELS, collect_one
from scripts.collect_matrix import COLLECTABLE_MODELS
from scripts.collect_matrix import main as collect_matrix_main
from traceone.optimized import EIGHT_TARGET_MODELS


class CollectionConfigTests(unittest.TestCase):
    def test_error_events_are_not_misreported_as_tool_calls(self) -> None:
        events = [{"type":"item.completed","item":{"type":"error","message":"transient"}},
                  {"type":"item.completed","item":{"type":"agent_message","text":"[]"}},
                  {"type":"turn.completed","usage":{}}]
        completed = subprocess.CompletedProcess([],0,"\n".join(map(json.dumps, events)),"")
        with patch("scripts.collect_codex.subprocess.run", return_value=completed), patch("scripts.collect_codex.runtime_version", return_value="test"):
            row = collect_one(Path("/test/codex"),"gpt-6.1-sol","fixture","development",1)
        self.assertEqual(row["tool_item_count"],0)
        self.assertEqual(row["completed_error_count"],1)
        events.insert(0,{"type":"item.completed","item":{"type":"command_execution","command":"not executed by this fixture"}})
        completed.stdout = "\n".join(map(json.dumps, events))
        with patch("scripts.collect_codex.subprocess.run", return_value=completed), patch("scripts.collect_codex.runtime_version", return_value="test"):
            row = collect_one(Path("/test/codex"),"gpt-6.1-sol","fixture","development",2)
        self.assertEqual(row["tool_item_count"],1)

    def test_new_route_is_a_registered_eighth_target(self) -> None:
        self.assertEqual(MODELS, EIGHT_TARGET_MODELS)
        self.assertNotIn("gpt-6.1-sol", PROSPECTIVE_MODELS)
        self.assertIn("gpt-6.1-sol", COLLECTABLE_MODELS)
        self.assertIn("gpt-6.1-sol", MODELS)

    def test_current_desktop_binary_is_preferred(self) -> None:
        self.assertEqual(
            BUNDLED_CODEX_CANDIDATES[0].as_posix(),
            "/Applications/ChatGPT.app/Contents/Resources/codex-cli/bin/codex",
        )

    def test_duplicate_routes_are_rejected_without_collecting(self) -> None:
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
                    "--models", "gpt-6.1-sol", "gpt-6.1-sol",
                ],
                capture_output=True, text=True, check=False,
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("model routes must be unique", result.stderr)
            self.assertFalse(output.exists())

    def test_eighth_route_batch_needs_no_prospective_opt_in(self) -> None:
        project = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as directory:
            argv = ["collect_matrix.py", "--output-dir", directory,
                    "--prompt", str(project / "prompts/identity-v3-schema.txt"),
                    "--schema", str(project / "schemas/identity-v3.json"),
                    "--run-id", "no-call-test", "--split", "development",
                    "--repeat-start", "1", "--repeat-end", "1",
                    "--models", "gpt-5.5", "gpt-6.1-sol"]
            with patch.object(sys, "argv", argv), patch("scripts.collect_matrix.subprocess.Popen") as popen, patch("sys.stdout", new_callable=StringIO):
                popen.return_value.communicate.return_value = ("", "")
                popen.return_value.returncode = 0
                collect_matrix_main()
            self.assertEqual(popen.call_count, 2)
            commands = [call.args[0] for call in popen.call_args_list]
            self.assertEqual({command[command.index("--model") + 1] for command in commands},
                             {"gpt-5.5", "gpt-6.1-sol"})


if __name__ == "__main__":
    unittest.main()
