# Agent Guide — Tools Hub (`tools`)

This repository is the central launcher, CLI dispatcher, and global agent skill provider for the `@RedoRojo` local productivity suite.

## 1. Quick Rules for AI Agents

- **Always prefer the CLI (`tools <alias> ...`) over the web UI (`./start-hub.sh` / `./run.sh`)** when asked to process files, URLs, or text.
- **Always pass `--json -q`** when invoking a tool programmatically:
  - `stdout` emits a single JSON object containing output paths and metadata.
  - `stderr` is silenced by `-q` (`--quiet`).
- **Exit codes** across all tools: `0` = success, `1` = runtime error, `2` = invalid CLI arguments, `130` = interrupted.
- **Bootstrap on a new computer**:
  ```bash
  git clone https://github.com/RedoRojo/tools-hub.git ~/Documents/tools
  ~/Documents/tools/setup.sh
  ```
  `setup.sh` clones/updates all tool repositories, links `~/.local/bin/tools`, and installs the global Antigravity skill at `~/.gemini/config/skills/redo-tools/SKILL.md`.

## 2. Command Reference

### PDF (`tools pdf` -> `pdf-toolbox/cli.py`)
```bash
tools pdf compress <file.pdf>... [--preset screen|ebook|printer] [--gray] [--dpi N] [-o out.pdf] --json -q
tools pdf merge <a.pdf> <b.pdf> [-o merged.pdf] --json -q
tools pdf split <file.pdf> --pages "1-5,8,10-12" [-o split.pdf] --json -q
tools pdf rotate <file.pdf> --angle 90|180|270 [--pages "1-3"] [-o rotated.pdf] --json -q
tools pdf inspect <file.pdf>... --json -q
tools pdf meta <file.pdf> [--title T] [--author A] [--subject S] [--keywords K] [-o out.pdf] --json -q
tools pdf ocr <img_or_pdf>... --lang spa+eng [--enhance] [--no-orient] [--txt] [-o scan.pdf] --json -q
tools pdf web <url> [--mode clean|full] [--style academic|modern|sans] [--no-images] [-o article.pdf] --json -q
```

### Kindle / EPUB3 (`tools kindle` -> `kindle-toolbox/cli.py`)
```bash
tools kindle web <url> [--title T] [--author A] [--style book|article] [--no-cover] [--no-images] [-o out.epub] --json -q
tools kindle pdf <file.pdf> [--columns auto|1|2] [--title T] [--author A] [--style book|article] [--no-cover] [-o out.epub] --json -q
tools kindle pdf-info <file.pdf> [--columns auto|1|2] --json -q
```

### Transcription (`tools transcript` -> `transcript/cli.py`)
```bash
tools transcript yt <url_or_id> [-l es|en] [-f txt|srt|vtt|json|csv|md|pdf] [--no-timestamps] [-o out|-] --json -q
tools transcript local <media_file>... [-m tiny|base|small|medium] [-l auto|es|en] [-f fmt] [--no-timestamps] [-o out|-] --json -q
tools transcript formats --json
```
*(Tip: Use `-o - -q` without `--json` to stream raw transcript text directly to `stdout`.)*

### QR Code (`tools qr` -> `qr-code/cli.py`)
```bash
tools qr "<text_or_url>" [-o out.png|out.svg|-] [-f png|svg] [-s 384] [-e L|M|Q|H] [--fg "#000000"] [--bg "#ffffff"] --json -q
tools qr "<text_or_url>" --terminal -q
```

## 3. Creating or Modifying Tools

Every tool in this ecosystem **must** follow [TOOL_STANDARD.md](TOOL_STANDARD.md):
- Start new tools from `_template/` (`cp -r _template <new-tool>`).
- Business logic lives in `core/` (or `services/`), never inside `app.py` or `cli.py`.
- Document both Web and CLI in `README.md` and provide an `AGENTS.md` for AI agents.
