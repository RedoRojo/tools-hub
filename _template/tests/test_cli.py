"""
CLI tests for Example Tool. Standard library only (unittest + subprocess).
Run with: python -m unittest discover -s tests -v
"""

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
CLI = BASE_DIR / "cli.py"


def run_cli(*args, cwd=None):
    return subprocess.run(
        [sys.executable, str(CLI), *args],
        capture_output=True,
        text=True,
        cwd=cwd,
        timeout=120,
    )


class CLITests(unittest.TestCase):
    def test_help_exits_zero(self):
        for args in ([], ["greet"]):
            result = run_cli(*args, "--help")
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("usage:", result.stdout)

    def test_no_command_is_usage_error(self):
        self.assertEqual(run_cli().returncode, 2)

    def test_greet_human_and_json(self):
        result = run_cli("greet", "Ada")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), "Hello, Ada!")

        result = run_cli("greet", "Ada", "--json")
        self.assertEqual(json.loads(result.stdout)["message"], "Hello, Ada!")

    def test_runs_from_any_working_directory(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = run_cli("greet", "Ada", cwd=tmp)
            self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == "__main__":
    unittest.main()
