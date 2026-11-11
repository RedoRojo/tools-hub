# Tools Hub ⚡

Central dashboard and unified process manager for local productivity web tools. Designed with a clean, minimalist, and ultra-fast web interface, it lets you launch and open any tool in a new browser tab with a single click.

---

## 🚀 Quick Start

If you just cloned this repository on a new machine, download all independent tool repositories with:

```bash
./setup.sh
```

To start the central dashboard and open it automatically in your default browser:

```bash
./start-hub.sh
```

The dashboard will be available at: **[http://localhost:7777](http://localhost:7777)**

---

## 🛠️ Included Tools (Independent Repositories)

| Tool | Directory / Repo | Port | Description |
| :--- | :--- | :--- | :--- |
| **YouTube & Local Transcript** | [`transcript/`](https://github.com/RedoRojo/transcript) | `8001` | YouTube video and local media transcription powered by Whisper with multi-format export (TXT, PDF, SRT, MD). |
| **PDF Toolbox** | [`pdf-toolbox/`](https://github.com/RedoRojo/pdf-toolbox) | `8002` | Scanned book OCR, PDF compression, merge, split, rotate, and clean web article to PDF conversion. |
| **Link to QR** | [`qr-code/`](https://github.com/RedoRojo/qr-code) | `8003` | Instant QR code generator with one-click clipboard copy and PNG/SVG downloads. |
| **Kindle Toolbox** | [`kindle-toolbox/`](https://github.com/RedoRojo/kindle-toolbox) | `8004` | Web article and PDF to reflowable EPUB3 converter optimized for E-Ink displays and Kindle readers. |

Each tool lives in its own Git repository and runs in isolation inside its subdirectory with its own environment (`.venv` or Miniconda) and dedicated port.

---

## ⚡ How the 1-Click Launcher Works

1. On the main dashboard (`http://localhost:7777`), click **"Launch & Open"** on the desired tool card.
2. Your browser opens a new tab. If the tool's server is currently stopped, the Hub automatically starts it in the background.
3. The tab polls the server port in real time and redirects immediately once the tool is ready.
4. If the tool was already running, it opens instantaneously with zero wait time.
5. You can stop or restart any running tool directly from the action buttons on its card.

---

## ➕ Adding a New Tool

The Hub includes **automatic tool discovery**. To integrate a new tool:

1. Create or clone a folder in this directory (e.g., `my-tool/`).
2. Add its startup script `run.sh` or `app.py` inside (and optionally a `tool.json`).
3. *(Optional)* Register its metadata and port in `tools.json`:

```json
{
  "id": "my-tool",
  "name": "My New Tool",
  "description": "Brief description of what it does.",
  "category": "Utilities",
  "icon": "code",
  "dir": "my-tool",
  "command": "./run.sh",
  "port": 8005,
  "health_path": "/"
}
```

Refresh the dashboard (`R` key or Refresh button) and it will automatically appear ready to launch.

---

## ⚙️ Project Structure

```text
tools/
├── hub.py              # HTTP server and process manager (Python standard library)
├── start-hub.sh        # Executable startup script and browser launcher
├── setup.sh            # Script to clone or update all independent tool repositories
├── tools.json          # Declarative registry of tools and ports
├── static/
│   └── index.html      # Minimalist web interface (modern CSS + reactive JS)
├── transcript/         # Independent repo: YouTube & Local Transcript (port 8001)
├── pdf-toolbox/        # Independent repo: PDF Toolbox (port 8002)
├── qr-code/            # Independent repo: Link to QR (port 8003)
└── kindle-toolbox/     # Independent repo: Kindle Toolbox (port 8004)
```
