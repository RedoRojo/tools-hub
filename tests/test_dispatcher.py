"""
Tests for the global `tools` CLI dispatcher (bin/tools) and the tool template.
Standard library only.
"""

import importlib.machinery
import importlib.util
import json
import subprocess
import sys
import unittest
from pathlib import Path

HUB_DIR = Path(__file__).resolve().parent.parent
DISPATCHER = HUB_DIR / "bin" / "tools"
TEMPLATE_DIR = HUB_DIR / "_template"


def load_dispatcher():
    loader = importlib.machinery.SourceFileLoader("tools_dispatcher", str(DISPATCHER))
    spec = importlib.util.spec_from_loader("tools_dispatcher", loader)
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    return module


def run(*args):
    return subprocess.run([sys.executable, str(DISPATCHER), *args], capture_output=True, text=True, timeout=60)


class DispatcherTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.mod = load_dispatcher()
        cls.tools = cls.mod.load_tools()

    def test_every_registered_tool_declares_a_cli_alias(self):
        entries = json.loads((HUB_DIR / "tools.json").read_text(encoding="utf-8"))
        aliases = [e["cli"]["alias"] for e in entries]
        self.assertEqual(len(aliases), len(set(aliases)), "CLI aliases must be unique")
        for entry in entries:
            self.assertEqual(entry["cli"]["command"], "./cli.sh")

    def test_resolve_by_alias_id_and_dir(self):
        self.assertEqual(self.mod.resolve("pdf", self.tools)["id"], "pdf-toolbox")
        self.assertEqual(self.mod.resolve("pdf-toolbox", self.tools)["id"], "pdf-toolbox")
        self.assertEqual(self.mod.resolve("qr", self.tools)["id"], "qr-code")
        self.assertIsNone(self.mod.resolve("does-not-exist", self.tools))

    def test_template_is_not_discovered_as_a_tool(self):
        self.assertNotIn("example-tool", [t["id"] for t in self.tools])

    def test_list_output(self):
        for args in ([], ["list"], ["--help"]):
            result = run(*args)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("Available tools:", result.stdout)
            self.assertIn("pdf", result.stdout)

    def test_unknown_tool_is_usage_error(self):
        result = run("nope")
        self.assertEqual(result.returncode, 2)
        self.assertIn("unknown tool", result.stderr)

    def test_version(self):
        result = run("--version")
        self.assertEqual(result.returncode, 0)
        self.assertIn("tools", result.stdout)


class TemplateTests(unittest.TestCase):
    def test_template_has_required_files(self):
        for name in ("cli.py", "cli.sh", "run.sh", "app.py", "tool.json", "README.md",
                     "requirements.txt", ".gitignore", "core/__init__.py", "tests/test_cli.py"):
            self.assertTrue((TEMPLATE_DIR / name).exists(), f"_template/{name} is missing")
        meta = json.loads((TEMPLATE_DIR / "tool.json").read_text(encoding="utf-8"))
        self.assertIn("alias", meta["cli"])

    def test_template_cli_tests_pass(self):
        result = subprocess.run(
            [sys.executable, "-m", "unittest", "discover", "-s", "tests"],
            cwd=TEMPLATE_DIR, capture_output=True, text=True, timeout=120,
        )
        self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == "__main__":
    unittest.main()
