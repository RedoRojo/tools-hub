"""
Unit and HTTP integration tests for Tools Hub.
Uses only the Python 3 standard library.
"""

import http.client
import json
import sys
import tempfile
import threading
import unittest
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from hub import ProcessManager, create_server


class ToolsHubTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = create_server("127.0.0.1", 0)
        cls.port = cls.server.server_address[1]
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join(timeout=2)

    def _request(self, method: str, path: str):
        conn = http.client.HTTPConnection("127.0.0.1", self.port, timeout=5)
        try:
            conn.request(method, path)
            res = conn.getresponse()
            body = res.read()
            return res.status, dict(res.getheaders()), body
        finally:
            conn.close()

    def test_dashboard_html_is_english_and_accessible(self):
        status, headers, body = self._request("GET", "/")
        self.assertEqual(status, 200)
        self.assertIn("text/html", headers.get("Content-Type", ""))
        html = body.decode("utf-8")

        self.assertIn('<html lang="en">', html)
        self.assertIn('<meta name="color-scheme" content="light dark">', html)
        self.assertIn("Tools Dashboard", html)
        self.assertIn("Refresh", html)
        self.assertIn('role="status"', html)
        self.assertNotIn("onclick=", html)

        for spanish_term in ("Herramienta", "Refrescar", "Cargando", "Detenida", "Puerto:"):
            self.assertNotIn(spanish_term, html)

    def test_head_requests_return_empty_body(self):
        for path in ("/", "/api/tools"):
            status, _, body = self._request("HEAD", path)
            self.assertEqual(status, 200)
            self.assertEqual(body, b"")

    def test_tools_json_in_english(self):
        tools_path = BASE_DIR / "tools.json"
        tools = json.loads(tools_path.read_text(encoding="utf-8"))
        ids = {t["id"] for t in tools}
        self.assertEqual(ids, {"pdf-toolbox", "transcript", "qr-code", "kindle-toolbox"})

        categories = {t["category"] for t in tools}
        self.assertEqual(categories, {"Documents", "Media", "Utilities", "Reading"})

    def test_api_tools_and_health_endpoints(self):
        status, _, body = self._request("GET", "/api/tools")
        self.assertEqual(status, 200)
        tools = json.loads(body.decode("utf-8"))
        self.assertGreaterEqual(len(tools), 4)

        status, _, body = self._request("GET", "/api/health/qr-code")
        self.assertEqual(status, 200)
        health = json.loads(body.decode("utf-8"))
        self.assertEqual(health["id"], "qr-code")
        self.assertIn("ready", health)

        status, _, body = self._request("GET", "/api/health/nonexistent-tool")
        self.assertEqual(status, 404)
        self.assertEqual(json.loads(body.decode("utf-8")), {"error": "Tool not found"})

    def test_launch_missing_tool_and_path_traversal(self):
        status, _, body = self._request("GET", "/launch/nonexistent-tool")
        self.assertEqual(status, 404)
        self.assertIn("Tool not found", body.decode("utf-8"))

        status, _, _ = self._request("GET", "/static/../hub.py")
        self.assertEqual(status, 404)

    def test_post_endpoints_error_messages_in_english(self):
        status, _, body = self._request("POST", "/api/tools/missing-tool/stop")
        self.assertEqual(status, 200)
        data = json.loads(body.decode("utf-8"))
        self.assertFalse(data["success"])
        self.assertEqual(data["message"], "Tool not found")

        status, _, _ = self._request("POST", "/api/unknown")
        self.assertEqual(status, 404)

    def test_process_manager_auto_discovery_and_ignored_dirs(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            config = root / "tools.json"
            config.write_text("[]", encoding="utf-8")

            # Ignored directories
            for ignored in ("static", "tests", "docs", ".hidden"):
                d = root / ignored
                d.mkdir()
                (d / "run.sh").write_text("#!/bin/sh\n", encoding="utf-8")

            # Auto-discovered tool with run.sh only
            auto_dir = root / "sample-tool"
            auto_dir.mkdir()
            (auto_dir / "run.sh").write_text("#!/bin/sh\n", encoding="utf-8")

            # Auto-discovered tool with tool.json
            custom_dir = root / "custom-tool"
            custom_dir.mkdir()
            (custom_dir / "tool.json").write_text(
                json.dumps({
                    "id": "custom-tool",
                    "name": "Custom Tool",
                    "description": "Custom description",
                    "category": "Dev",
                    "port": 8099,
                }),
                encoding="utf-8",
            )

            pm = ProcessManager(base_dir=root, config_file=config)
            discovered = pm.load_tools()
            by_id = {t["id"]: t for t in discovered}

            self.assertEqual(set(by_id.keys()), {"sample-tool", "custom-tool"})
            self.assertEqual(by_id["sample-tool"]["category"], "Utilities")
            self.assertEqual(by_id["sample-tool"]["description"], "Tool in sample-tool")
            self.assertEqual(by_id["custom-tool"]["port"], 8099)


if __name__ == "__main__":
    unittest.main()
