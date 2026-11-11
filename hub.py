#!/usr/bin/env python3
"""
Tools Hub - Central Dashboard and Tool Process Manager
Runs and manages local tools in subdirectories with 1-click launch.
Requires no external dependencies (uses only the Python 3 standard library).
"""

import html
import json
import mimetypes
import os
import signal
import socket
import subprocess
import sys
import threading
import time
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = (BASE_DIR / "static").resolve()
TOOLS_CONFIG_FILE = BASE_DIR / "tools.json"
DEFAULT_HUB_PORT = int(os.environ.get("HUB_PORT", 7777))


class ReusableThreadingHTTPServer(ThreadingHTTPServer):
    allow_reuse_address = True


class ProcessManager:
    def __init__(self, base_dir: Path = BASE_DIR, config_file: Path = TOOLS_CONFIG_FILE):
        self.base_dir = Path(base_dir)
        self.config_file = Path(config_file)
        self.lock = threading.Lock()
        self.processes = {}  # tool_id -> {"proc": Popen, "started_at": float, "port": int}
        self.tools_cache = {}

    def is_port_listening(self, port: int, timeout: float = 0.5) -> bool:
        """Check whether a local port is accepting TCP connections."""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(timeout)
                return s.connect_ex(("127.0.0.1", port)) == 0
        except Exception:
            return False

    def load_tools(self):
        """Load tools from tools.json and auto-discover tool subdirectories."""
        tools = []
        registered_dirs = set()

        # 1. Read declarative entries from tools.json if present
        if self.config_file.exists():
            try:
                with open(self.config_file, "r", encoding="utf-8") as f:
                    tools = json.load(f)
                    for t in tools:
                        registered_dirs.add(t.get("dir", t.get("id")))
            except Exception as e:
                print(f"[ERROR] Failed to read tools.json: {e}", file=sys.stderr)

        # 2. Auto-discover subdirectories containing run.sh, app.py, or tool.json
        next_port = 8005
        ignored_dirs = {"static", "brain", "tests", "docs", "bin", "skills"}
        for item in sorted(self.base_dir.iterdir()):
            if item.is_dir() and not item.name.startswith((".", "_")) and item.name not in ignored_dirs:
                if item.name not in registered_dirs:
                    run_sh = item / "run.sh"
                    app_py = item / "app.py"
                    tool_json = item / "tool.json"

                    if run_sh.exists() or app_py.exists() or tool_json.exists():
                        while any(t.get("port") == next_port for t in tools) or self.is_port_listening(next_port):
                            next_port += 1

                        meta = {}
                        if tool_json.exists():
                            try:
                                with open(tool_json, "r", encoding="utf-8") as tf:
                                    meta = json.load(tf)
                            except Exception:
                                pass

                        cmd = "./run.sh" if run_sh.exists() else "python3 app.py"
                        tools.append({
                            "id": meta.get("id", item.name),
                            "name": meta.get("name", item.name.replace("-", " ").title()),
                            "description": meta.get("description", f"Tool in {item.name}"),
                            "category": meta.get("category", "Utilities"),
                            "icon": meta.get("icon", "code"),
                            "dir": item.name,
                            "command": meta.get("command", cmd),
                            "port": meta.get("port", next_port),
                            "health_path": meta.get("health_path", "/"),
                        })
                        next_port += 1

        self.tools_cache = {t["id"]: t for t in tools}
        return tools

    def get_tool_status(self, tool_id: str):
        tool = self.tools_cache.get(tool_id)
        if not tool:
            return None

        port = tool.get("port", 8000)
        port_active = self.is_port_listening(port)

        with self.lock:
            proc_info = self.processes.get(tool_id)
            is_running = False
            pid = None
            uptime = 0

            if proc_info:
                proc = proc_info["proc"]
                if proc.poll() is None:
                    is_running = True
                    pid = proc.pid
                    uptime = int(time.time() - proc_info["started_at"])
                else:
                    # Process exited
                    del self.processes[tool_id]

            # If port is listening even without a tracked Popen (e.g., started externally)
            if port_active and not is_running:
                is_running = True

            return {
                **tool,
                "running": is_running,
                "port_active": port_active,
                "pid": pid,
                "uptime": uptime,
                "url": f"http://127.0.0.1:{port}",
            }

    def start_tool(self, tool_id: str):
        """Start a tool if it is not already running."""
        tool = self.tools_cache.get(tool_id)
        if not tool:
            return False, "Tool not found"

        port = tool.get("port", 8000)
        tool_dir = self.base_dir / tool.get("dir", tool_id)

        if not tool_dir.exists():
            return False, f"Directory not found: {tool_dir}"

        with self.lock:
            if self.is_port_listening(port):
                return True, f"Tool already running at http://127.0.0.1:{port}"

            proc_info = self.processes.get(tool_id)
            if proc_info and proc_info["proc"].poll() is None:
                return True, f"Tool is already starting on port {port}..."

            env = os.environ.copy()
            env["PORT"] = str(port)

            cmd = tool.get("command", "./run.sh")
            try:
                # Use setsid so the entire process group can be terminated cleanly
                proc = subprocess.Popen(
                    cmd,
                    shell=True,
                    cwd=str(tool_dir),
                    env=env,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    preexec_fn=os.setsid,
                )
                self.processes[tool_id] = {
                    "proc": proc,
                    "started_at": time.time(),
                    "port": port,
                }
                print(f"[HUB] Started tool '{tool_id}' (PID {proc.pid}) on port {port}")
                return True, f"Starting on port {port}..."
            except Exception as e:
                return False, f"Execution failed: {e}"

    def stop_tool(self, tool_id: str):
        """Cleanly stop a running tool."""
        tool = self.tools_cache.get(tool_id)
        if not tool:
            return False, "Tool not found"

        port = tool.get("port", 8000)
        with self.lock:
            proc_info = self.processes.pop(tool_id, None)
            if proc_info:
                proc = proc_info["proc"]
                try:
                    os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
                    proc.wait(timeout=2.0)
                except (subprocess.TimeoutExpired, ProcessLookupError, PermissionError):
                    try:
                        os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
                    except Exception:
                        pass

        # Release any orphaned process still bound to the port
        if self.is_port_listening(port):
            try:
                subprocess.run(["fuser", "-k", "-TERM", f"{port}/tcp"], capture_output=True, timeout=2.0)
                time.sleep(0.3)
                if self.is_port_listening(port):
                    subprocess.run(["fuser", "-k", "-9", f"{port}/tcp"], capture_output=True, timeout=2.0)
            except Exception:
                pass

        time.sleep(0.2)
        return True, "Tool stopped"

    def restart_tool(self, tool_id: str):
        self.stop_tool(tool_id)
        time.sleep(0.8)
        return self.start_tool(tool_id)


manager = ProcessManager()


class HubRequestHandler(SimpleHTTPRequestHandler):
    def end_headers(self):
        # Disable caching for API responses
        if self.path.startswith("/api/"):
            self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
            self.send_header("Pragma", "no-cache")
            self.send_header("Expires", "0")
        super().end_headers()

    def _write_body(self, body: bytes):
        if self.command != "HEAD":
            self.wfile.write(body)

    def do_HEAD(self):
        self.do_GET()

    def do_GET(self):
        url_path = self.path.split("?", 1)[0]

        if url_path in ("/", "/index.html"):
            index_file = STATIC_DIR / "index.html"
            if index_file.exists():
                content = index_file.read_bytes()
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(content)))
                self.end_headers()
                self._write_body(content)
                return
            self.send_error(404, "index.html not found")
            return

        if url_path == "/api/tools":
            tools = manager.load_tools()
            statuses = [manager.get_tool_status(t["id"]) for t in tools]
            self.send_json(statuses)
            return

        if url_path.startswith("/api/health/"):
            tool_id = url_path[len("/api/health/"):]
            status = manager.get_tool_status(tool_id)
            if not status:
                self.send_json({"error": "Tool not found"}, status=404)
                return
            self.send_json({
                "id": tool_id,
                "ready": status["port_active"],
                "url": status["url"],
            })
            return

        if url_path.startswith("/launch/"):
            # 1-Click Launch & Auto-Redirect
            tool_id = url_path[len("/launch/"):]
            manager.load_tools()
            status = manager.get_tool_status(tool_id)

            if not status:
                body = b"<!DOCTYPE html><html lang='en'><head><meta charset='UTF-8'><title>Not Found</title></head><body><h1>Tool not found</h1></body></html>"
                self.send_response(404)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self._write_body(body)
                return

            port = status.get("port")
            target_url = f"http://127.0.0.1:{port}"

            # If already running, redirect immediately (302)
            if status.get("port_active"):
                self.send_response(302)
                self.send_header("Location", target_url)
                self.send_header("Content-Length", "0")
                self.end_headers()
                return

            # If stopped, start in background and show live waiting splash page
            if self.command != "HEAD":
                manager.start_tool(tool_id)

            tool_name = html.escape(status.get("name", tool_id))
            js_tool_id = json.dumps(tool_id)
            js_target_url = json.dumps(target_url)
            safe_target_href = html.escape(target_url, quote=True)

            html_splash = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <meta name="color-scheme" content="light dark">
  <title>Starting {tool_name}...</title>
  <style>
    :root {{ color-scheme: light dark; }}
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
      background-color: #0c0d0e;
      color: #f1f3f5;
      display: flex;
      align-items: center;
      justify-content: center;
      min-height: 100vh;
      padding: 1.5rem;
    }}
    .card {{
      background: #141517;
      border: 1px solid #25262b;
      border-radius: 14px;
      padding: 2.5rem 2rem;
      max-width: 420px;
      width: 100%;
      text-align: center;
      box-shadow: 0 10px 30px rgba(0, 0, 0, 0.4);
    }}
    .spinner {{
      width: 42px;
      height: 42px;
      border: 3px solid #2c2e33;
      border-top-color: #3b82f6;
      border-radius: 50%;
      animation: spin 0.8s linear infinite;
      margin: 0 auto 1.5rem;
    }}
    @keyframes spin {{ to {{ transform: rotate(360deg); }} }}
    @media (prefers-reduced-motion: reduce) {{
      .spinner {{ animation: none; }}
    }}
    h1 {{ font-size: 1.25rem; font-weight: 600; margin-bottom: 0.5rem; }}
    p {{ color: #9ca3af; font-size: 0.875rem; line-height: 1.4; }}
    .badge {{
      display: inline-block;
      margin-top: 1.25rem;
      font-size: 0.75rem;
      color: #cbd5e1;
      background: #1a1b1e;
      padding: 0.25rem 0.75rem;
      border-radius: 9999px;
      border: 1px solid #2c2e33;
      font-family: monospace;
    }}
  </style>
</head>
<body>
  <div class="card">
    <div class="spinner" aria-hidden="true"></div>
    <h1>Starting {tool_name}</h1>
    <p id="msg" role="status" aria-live="polite">Starting server in the background...</p>
    <div class="badge">Port {port}</div>
  </div>
  <script>
    const toolId = {js_tool_id};
    const targetUrl = {js_target_url};
    let attempts = 0;
    const maxAttempts = 35; // 35 * 400ms = 14s

    async function checkReady() {{
      attempts++;
      try {{
        const res = await fetch("/api/health/" + encodeURIComponent(toolId));
        const data = await res.json();
        if (data.ready) {{
          document.getElementById("msg").textContent = "Server ready! Opening application...";
          window.location.replace(targetUrl);
          return;
        }}
      }} catch (e) {{}}

      if (attempts >= maxAttempts) {{
        document.getElementById("msg").innerHTML = 'Took too long to respond.<br><a href="{safe_target_href}" style="color:#60a5fa;text-decoration:underline;">Try opening directly</a>';
      }} else {{
        setTimeout(checkReady, 400);
      }}
    }}

    setTimeout(checkReady, 500);
  </script>
</body>
</html>"""
            body = html_splash.encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self._write_body(body)
            return

        # Serve static assets safely (preventing path traversal)
        if url_path.startswith("/static/"):
            rel_path = url_path[len("/static/"):].lstrip("/")
            if rel_path:
                try:
                    file_path = (STATIC_DIR / rel_path).resolve()
                except OSError:
                    self.send_error(404, "Route not found")
                    return
                if file_path.is_relative_to(STATIC_DIR) and file_path.is_file():
                    mime_type, _ = mimetypes.guess_type(str(file_path))
                    ext = file_path.suffix.lower()
                    if ext == ".html":
                        ct = "text/html; charset=utf-8"
                    elif ext == ".css":
                        ct = "text/css; charset=utf-8"
                    elif ext == ".js":
                        ct = "application/javascript; charset=utf-8"
                    elif ext == ".svg":
                        ct = "image/svg+xml"
                    elif ext == ".json":
                        ct = "application/json; charset=utf-8"
                    else:
                        ct = mime_type or "application/octet-stream"
                    content = file_path.read_bytes()
                    self.send_response(200)
                    self.send_header("Content-Type", ct)
                    self.send_header("Content-Length", str(len(content)))
                    self.end_headers()
                    self._write_body(content)
                    return

        self.send_error(404, "Route not found")

    def do_POST(self):
        url_path = self.path.split("?", 1)[0]

        if url_path.startswith("/api/tools/") and url_path.endswith("/start"):
            tool_id = url_path[len("/api/tools/"):-len("/start")]
            success, msg = manager.start_tool(tool_id)
            self.send_json({"success": success, "message": msg, "tool": manager.get_tool_status(tool_id)})
            return

        if url_path.startswith("/api/tools/") and url_path.endswith("/stop"):
            tool_id = url_path[len("/api/tools/"):-len("/stop")]
            success, msg = manager.stop_tool(tool_id)
            self.send_json({"success": success, "message": msg, "tool": manager.get_tool_status(tool_id)})
            return

        if url_path.startswith("/api/tools/") and url_path.endswith("/restart"):
            tool_id = url_path[len("/api/tools/"):-len("/restart")]
            success, msg = manager.restart_tool(tool_id)
            self.send_json({"success": success, "message": msg, "tool": manager.get_tool_status(tool_id)})
            return

        self.send_error(404, "POST endpoint not found")

    def send_json(self, data, status=200):
        body = json.dumps(data, ensure_ascii=False, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self._write_body(body)

    def log_message(self, format, *args):
        try:
            msg = format % args
            if "/api/health/" in msg or "/api/tools" in msg:
                return
            sys.stderr.write(f"[HUB] {msg}\n")
        except Exception:
            pass


def create_server(host: str = "127.0.0.1", port: int = DEFAULT_HUB_PORT) -> ReusableThreadingHTTPServer:
    return ReusableThreadingHTTPServer((host, port), HubRequestHandler)


def run_hub(port=DEFAULT_HUB_PORT):
    manager.load_tools()

    def handle_shutdown(sig, frame):
        print("\n[HUB] Shutting down Tools Hub...")
        sys.exit(0)

    signal.signal(signal.SIGINT, handle_shutdown)
    signal.signal(signal.SIGTERM, handle_shutdown)

    try:
        httpd = create_server("127.0.0.1", port)
    except OSError as e:
        print(f"[ERROR] Could not bind to port {port}: {e}", file=sys.stderr)
        sys.exit(1)

    print("=" * 60)
    print(f"🚀 Tools Hub dashboard active at: http://127.0.0.1:{port}")
    print("=" * 60)

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        httpd.server_close()


if __name__ == "__main__":
    port = DEFAULT_HUB_PORT
    if len(sys.argv) > 1:
        try:
            port = int(sys.argv[1])
        except ValueError:
            pass
    run_hub(port)
