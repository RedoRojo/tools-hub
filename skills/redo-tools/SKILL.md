---
name: redo-tools
description: >-
  Local CLI toolkit (`tools`) for PDF processing, OCR, web-to-PDF, web/PDF-to-EPUB3 (Kindle),
  YouTube & local Whisper audio/video transcription, and QR code generation.
  Use this skill whenever the user asks to compress, merge, split, rotate, inspect, edit metadata,
  or OCR PDFs/images; convert web articles or PDFs into EPUB3 e-books; transcribe YouTube videos
  or local audio/video files into TXT/SRT/VTT/MD/PDF/JSON/CSV; or generate QR codes (PNG/SVG/terminal).
---

# Redo Tools (`tools` CLI Suite)

You have direct access to the local `tools` CLI suite (`~/.local/bin/tools`).

## Golden Rules for Agents

1. **Always use the CLI (`tools <alias> ...`)** — never start the web server (`./run.sh` or `app.py`) when the user wants to process files, URLs, or text.
2. **Pass `--json -q` for machine-parsable output**:
   - `stdout` receives a single JSON object with output file paths and metrics.
   - `-q` suppresses progress logs on `stderr`.
3. **Pass `-o <path>` when the user specifies where to save**, or omit `-o` to write into the current working directory (it never overwrites existing files).
4. **If `tools` is not installed on this machine yet**, bootstrap it in one command:
   ```bash
   git clone https://github.com/RedoRojo/tools-hub.git ~/Documents/tools && ~/Documents/tools/setup.sh
   ```

---

## 1. PDF Toolbox (`tools pdf`)

| Task | Command |
| :--- | :--- |
| **Compress PDF(s)** | `tools pdf compress input.pdf --preset ebook --json -q [-o out.pdf]` |
| **Compress (max / grayscale)** | `tools pdf compress input.pdf --preset screen --gray --json -q` |
| **Merge PDFs** | `tools pdf merge a.pdf b.pdf -o merged.pdf --json -q` |
| **Split / extract pages** | `tools pdf split input.pdf --pages "1-5,8,10-12" -o excerpt.pdf --json -q` |
| **Rotate pages** | `tools pdf rotate input.pdf --angle 90 [--pages "1-3"] -o rotated.pdf --json -q` |
| **Inspect metadata & size** | `tools pdf inspect input.pdf --json -q` |
| **Update PDF metadata** | `tools pdf meta input.pdf --title "Title" --author "Author" -o out.pdf --json -q` |
| **OCR scanned PDF or images** | `tools pdf ocr page1.jpg page2.jpg --lang spa+eng [--enhance] [--txt] -o scan.pdf --json -q` |
| **Web article to PDF** | `tools pdf web "https://example.com/post" [--mode clean\|full] [--no-images] -o article.pdf --json -q` |

* **Presets (`--preset`)**: `screen` (~72 dpi), `ebook` (~150 dpi, default), `printer` (~300 dpi), or custom `--dpi N`.
* **Key JSON fields returned**: `filepath`, `filename`, `compressed_size_bytes` / `size_bytes`, `saved_percentage` (compress), `pages` / `metadata` (inspect), `text_filepath` (ocr with `--txt`).

---

## 2. Kindle Toolbox — Web & PDF to EPUB3 (`tools kindle`)

| Task | Command |
| :--- | :--- |
| **Web article → EPUB3** | `tools kindle web "https://example.com/article" [--title "..."] [--author "..."] -o article.epub --json -q` |
| **PDF book → EPUB3** | `tools kindle pdf book.pdf [--columns auto\|1\|2] [--title "..."] [--author "..."] -o book.epub --json -q` |
| **Inspect PDF chapters** | `tools kindle pdf-info book.pdf [--columns auto\|1\|2] --json -q` |

* **Options**: `--style book|article` (default `book`), `--no-cover`, `--no-images` (for `web`).
* **Key JSON fields returned**: `filepath`, `filename`, `filesize`, `title`, `author`, `chapters_count` (for `pdf`).

---

## 3. YouTube & Local Whisper Transcript (`tools transcript`)

| Task | Command |
| :--- | :--- |
| **YouTube → file** | `tools transcript yt "https://youtu.be/VIDEO_ID" -f srt [-l es] -o subtitles.srt --json -q` |
| **YouTube → stdout (pipe)** | `tools transcript yt "https://youtu.be/VIDEO_ID" -f txt --no-timestamps -o - -q` |
| **Local audio/video → file** | `tools transcript local video.mp4 -m base [-l es\|en\|auto] -f md -o notes.md --json -q` |
| **Local audio/video → stdout** | `tools transcript local audio.mp3 -m tiny -f txt --no-timestamps -o - -q` |
| **List export formats** | `tools transcript formats --json` |

* **Formats (`-f/--format`)**: `txt`, `srt`, `vtt`, `json`, `csv`, `md`, `pdf` (inferred from `-o` extension when omitted).
* **Whisper models (`-m/--model`)**: `tiny` (fastest), `base` (default), `small`, `medium`.
* **Timestamps**: included by default in `txt`/`md`/`pdf`; pass `--no-timestamps` for clean flowing paragraphs.
* **Key JSON fields returned**: `output`, `format`, `bytes`, `title`, `language`, `segments`, `words`, `duration`.

---

## 4. Link to QR (`tools qr`)

| Task | Command |
| :--- | :--- |
| **Generate PNG** | `tools qr "https://example.com" -o qr.png --size 512 --json -q` |
| **Generate SVG** | `tools qr "https://example.com" -o qr.svg --fg "#1e3a8a" --bg "#ffffff" --json -q` |
| **Print QR in terminal** | `tools qr "https://example.com" --terminal -q` |

* **Options**: `-s/--size` (default `384`), `-e/--error L|M|Q|H` (default `H`), `--fg`, `--bg`, `--border`.
* **Key JSON fields returned**: `output`, `format`, `size`, `version`, `error`, `bytes`.
