#!/usr/bin/env python3
"""
Tools Hub - Panel Central y Gestor de Herramientas
Ejecuta y gestiona herramientas locales en subdirectorios con lanzamiento en 1-clic.
No requiere dependencias externas (usa la biblioteca estándar de Python 3).
"""

import os
import sys
import json
import time
import signal
import socket
import urllib.request
import urllib.error
import subprocess
import threading
from pathlib import Path
from http.server import HTTPServer, SimpleHTTPRequestHandler, ThreadingHTTPServer

BASE_DIR = Path(__file__).resolve().parent
TOOLS_CONFIG_FILE = BASE_DIR / "tools.json"
DEFAULT_HUB_PORT = int(os.environ.get("HUB_PORT", 7777))

class ProcessManager:
    def __init__(self):
        self.lock = threading.Lock()
        self.processes = {}  # tool_id -> {"proc": Popen, "started_at": float, "port": int}
        self.tools_cache = {}

    def is_port_listening(self, port: int, timeout: float = 0.5) -> bool:
        """Comprueba si un puerto local está respondiendo."""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(timeout)
                return s.connect_ex(("127.0.0.1", port)) == 0
        except Exception:
            return False

    def load_tools(self):
        """Carga herramientas desde tools.json y auto-detecta subdirectorios."""
        tools = []
        registered_dirs = set()

        # 1. Leer de tools.json si existe
        if TOOLS_CONFIG_FILE.exists():
            try:
                with open(TOOLS_CONFIG_FILE, "r", encoding="utf-8") as f:
                    tools = json.load(f)
                    for t in tools:
                        registered_dirs.add(t.get("dir", t.get("id")))
            except Exception as e:
                print(f"[ERROR] Error al leer tools.json: {e}", file=sys.stderr)

        # 2. Auto-detección en subdirectorios
        next_port = 8005
        for item in sorted(BASE_DIR.iterdir()):
            if item.is_dir() and not item.name.startswith((".", "_")) and item.name not in ["static", "brain"]:
                if item.name not in registered_dirs:
                    run_sh = item / "run.sh"
                    app_py = item / "app.py"
                    tool_json = item / "tool.json"
                    
                    if run_sh.exists() or app_py.exists() or tool_json.exists():
                        # Encontrar puerto libre
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
                            "id": item.name,
                            "name": meta.get("name", item.name.replace("-", " ").title()),
                            "description": meta.get("description", f"Herramienta en {item.name}"),
                            "category": meta.get("category", "Utilidades"),
                            "icon": meta.get("icon", "code"),
                            "dir": item.name,
                            "command": meta.get("command", cmd),
                            "port": meta.get("port", next_port),
                            "health_path": meta.get("health_path", "/")
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
                    # El proceso terminó
                    del self.processes[tool_id]

            # Si el puerto responde aunque no tengamos el Popen (ej. iniciado externamente)
            if port_active and not is_running:
                is_running = True

            return {
                **tool,
                "running": is_running,
                "port_active": port_active,
                "pid": pid,
                "uptime": uptime,
                "url": f"http://127.0.0.1:{port}"
            }

    def start_tool(self, tool_id: str):
        """Inicia una herramienta si no está ya en ejecución."""
        tool = self.tools_cache.get(tool_id)
        if not tool:
            return False, "Herramienta no encontrada"

        port = tool.get("port", 8000)
        tool_dir = BASE_DIR / tool.get("dir", tool_id)

        if not tool_dir.exists():
            return False, f"Directorio no encontrado: {tool_dir}"

        # Comprobar si ya está activa
        status = self.get_tool_status(tool_id)
        if status and status["port_active"]:
            return True, f"Herramienta ya activa en http://127.0.0.1:{port}"

        with self.lock:
            env = os.environ.copy()
            env["PORT"] = str(port)

            cmd = tool.get("command", "./run.sh")
            try:
                # Usar setsid para que podamos matar el grupo completo si se detiene
                proc = subprocess.Popen(
                    cmd,
                    shell=True,
                    cwd=str(tool_dir),
                    env=env,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    preexec_fn=os.setsid
                )
                self.processes[tool_id] = {
                    "proc": proc,
                    "started_at": time.time(),
                    "port": port
                }
                print(f"[HUB] Iniciada herramienta '{tool_id}' (PID {proc.pid}) en puerto {port}")
                return True, f"Iniciando en puerto {port}..."
            except Exception as e:
                return False, f"Error al ejecutar: {e}"

    def stop_tool(self, tool_id: str):
        """Detiene la herramienta de forma limpia."""
        tool = self.tools_cache.get(tool_id)
        if not tool:
            return False, "Herramienta no encontrada"

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

        # Si aún queda algún proceso huérfano en el puerto, liberarlo
        if self.is_port_listening(port):
            try:
                subprocess.run(["fuser", "-k", "-TERM", f"{port}/tcp"], capture_output=True, timeout=2.0)
                time.sleep(0.3)
                if self.is_port_listening(port):
                    subprocess.run(["fuser", "-k", "-9", f"{port}/tcp"], capture_output=True, timeout=2.0)
            except Exception:
                pass

        time.sleep(0.2)
        return True, "Herramienta detenida"

    def restart_tool(self, tool_id: str):
        self.stop_tool(tool_id)
        time.sleep(0.8)
        return self.start_tool(tool_id)


manager = ProcessManager()

class HubRequestHandler(SimpleHTTPRequestHandler):
    def end_headers(self):
        # Deshabilitar caché para llamadas a la API
        if self.path.startswith("/api/"):
            self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
            self.send_header("Pragma", "no-cache")
            self.send_header("Expires", "0")
        super().end_headers()

    def do_HEAD(self):
        self.do_GET()

    def do_GET(self):
        url_path = self.path.split("?")[0]

        if url_path == "/" or url_path == "/index.html":
            index_file = BASE_DIR / "static" / "index.html"
            if index_file.exists():
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.end_headers()
                with open(index_file, "rb") as f:
                    self.wfile.write(f.read())
                return
            else:
                self.send_error(404, "index.html not found")
                return

        elif url_path == "/api/tools":
            tools = manager.load_tools()
            statuses = [manager.get_tool_status(t["id"]) for t in tools]
            self.send_json(statuses)
            return

        elif url_path.startswith("/api/health/"):
            tool_id = url_path[len("/api/health/"):]
            status = manager.get_tool_status(tool_id)
            if not status:
                self.send_json({"error": "Tool not found"}, status=404)
                return
            self.send_json({
                "id": tool_id,
                "ready": status["port_active"],
                "url": status["url"]
            })
            return

        elif url_path.startswith("/launch/"):
            # 1-Click Launch & Auto-Redirect
            tool_id = url_path[len("/launch/"):]
            tools = manager.load_tools()
            status = manager.get_tool_status(tool_id)

            if not status:
                self.send_response(404)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.end_headers()
                self.wfile.write(b"<h1>Herramienta no encontrada</h1>")
                return

            port = status.get("port")
            target_url = f"http://127.0.0.1:{port}"

            # Si ya está activo, redirigir inmediatamente (302)
            if status.get("port_active"):
                self.send_response(302)
                self.send_header("Location", target_url)
                self.send_header("Content-Length", "0")
                self.end_headers()
                return

            # Si está inactivo, iniciar en segundo plano y mostrar pantalla de espera activa
            manager.start_tool(tool_id)
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            
            tool_name = status.get("name", tool_id)
            html_splash = f"""<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Iniciando {tool_name}...</title>
  <style>
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
    h1 {{ font-size: 1.25rem; font-weight: 600; margin-bottom: 0.5rem; }}
    p {{ color: #909296; font-size: 0.875rem; line-height: 1.4; }}
    .badge {{
      display: inline-block;
      margin-top: 1.25rem;
      font-size: 0.75rem;
      color: #adb5bd;
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
    <div class="spinner"></div>
    <h1>Iniciando {tool_name}</h1>
    <p id="msg">Arrancando servidor en segundo plano...</p>
    <div class="badge">Puerto {port}</div>
  </div>
  <script>
    const toolId = "{tool_id}";
    const targetUrl = "{target_url}";
    let attempts = 0;
    const maxAttempts = 35; // 35 * 400ms = 14s

    async function checkReady() {{
      attempts++;
      try {{
        const res = await fetch("/api/health/" + toolId);
        const data = await res.json();
        if (data.ready) {{
          document.getElementById("msg").textContent = "¡Servidor listo! Abriendo aplicación...";
          window.location.replace(targetUrl);
          return;
        }}
      }} catch (e) {{}}

      if (attempts >= maxAttempts) {{
        document.getElementById("msg").innerHTML = 'Tardó demasiado en responder.<br><a href="' + targetUrl + '" style="color:#60a5fa;text-decoration:underline;">Intentar abrir directamente</a>';
      }} else {{
        setTimeout(checkReady, 400);
      }}
    }}

    setTimeout(checkReady, 500);
  </script>
</body>
</html>"""
            self.wfile.write(html_splash.encode("utf-8"))
            return

        # Servir estáticos si los hay
        if url_path.startswith("/static/"):
            rel_path = url_path[len("/static/"):]
            file_path = BASE_DIR / "static" / rel_path
            if file_path.exists() and file_path.is_file():
                self.send_response(200)
                # determinar content type simple
                ext = file_path.suffix.lower()
                ct = "text/plain"
                if ext == ".html": ct = "text/html; charset=utf-8"
                elif ext == ".css": ct = "text/css; charset=utf-8"
                elif ext == ".js": ct = "application/javascript; charset=utf-8"
                elif ext == ".svg": ct = "image/svg+xml"
                elif ext == ".json": ct = "application/json"
                self.send_header("Content-Type", ct)
                self.end_headers()
                with open(file_path, "rb") as f:
                    self.wfile.write(f.read())
                return

        self.send_error(404, "Ruta no encontrada")

    def do_POST(self):
        url_path = self.path.split("?")[0]
        
        if url_path.startswith("/api/tools/") and url_path.endswith("/start"):
            tool_id = url_path[len("/api/tools/"): -len("/start")]
            success, msg = manager.start_tool(tool_id)
            self.send_json({"success": success, "message": msg, "tool": manager.get_tool_status(tool_id)})
            return

        elif url_path.startswith("/api/tools/") and url_path.endswith("/stop"):
            tool_id = url_path[len("/api/tools/"): -len("/stop")]
            success, msg = manager.stop_tool(tool_id)
            self.send_json({"success": success, "message": msg, "tool": manager.get_tool_status(tool_id)})
            return

        elif url_path.startswith("/api/tools/") and url_path.endswith("/restart"):
            tool_id = url_path[len("/api/tools/"): -len("/restart")]
            success, msg = manager.restart_tool(tool_id)
            self.send_json({"success": success, "message": msg, "tool": manager.get_tool_status(tool_id)})
            return

        self.send_error(404, "Endpoint POST no encontrado")

    def send_json(self, data, status=200):
        body = json.dumps(data, ensure_ascii=False, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format, *args):
        try:
            msg = format % args
            if "/api/health/" in msg or "/api/tools" in msg:
                return
            sys.stderr.write(f"[HUB] {msg}\n")
        except Exception:
            pass


def run_hub(port=DEFAULT_HUB_PORT):
    manager.load_tools()
    server_address = ("127.0.0.1", port)
    
    # Manejar cierre limpio con Ctrl+C
    def handle_sigint(sig, frame):
        print("\n[HUB] Apagando panel de herramientas...")
        sys.exit(0)

    signal.signal(signal.SIGINT, handle_sigint)
    signal.signal(signal.SIGTERM, handle_sigint)

    try:
        httpd = ThreadingHTTPServer(server_address, HubRequestHandler)
    except OSError as e:
        print(f"[ERROR] No se pudo vincular el puerto {port}: {e}", file=sys.stderr)
        sys.exit(1)

    print("=" * 60)
    print(f"🚀 Tools Hub (Panel General) activo en: http://127.0.0.1:{port}")
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
