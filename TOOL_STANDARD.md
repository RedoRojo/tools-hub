# Tool Standard

Every tool managed by Tools Hub **must** provide both a **web interface** and a **command line interface (CLI)**, built on the same core logic. Start new tools by copying [`_template/`](_template/).

```bash
cp -r _template my-tool && cd my-tool   # then rename ids, ports, aliases
```

## 1. Required Layout

```text
my-tool/
├── core/               # ALL business logic (pure functions, no HTTP, no printing)
│   └── __init__.py
├── app.py              # Web adapter: HTTP, uploads, task polling -> calls core/
├── cli.py              # CLI adapter: argparse -> calls core/ synchronously
├── cli.sh              # CLI launcher: resolves the Python env, runs cli.py (never cd)
├── run.sh              # Web launcher used by Tools Hub
├── tool.json           # Metadata incl. "cli": {"alias", "command"}
├── requirements.txt    # (or environment.yml for conda-based tools)
├── tests/
│   └── test_cli.py     # unittest-based CLI tests (+ existing web tests)
├── AGENTS.md           # Concise CLI recipes & JSON output schemas for AI agents
├── README.md           # Must document BOTH "Web Interface" and "Command Line Interface"
└── .gitignore
```

## 2. Layering Rules

| Layer | May import | Must not |
| :--- | :--- | :--- |
| `core/` | stdlib, third-party libs | FastAPI, `print`, global task dicts, hard-coded output dirs |
| `app.py` | `core/`, FastAPI | Contain business logic beyond request/response shaping |
| `cli.py` | `core/` (lazily) | Import `app.py`, FastAPI, or start a server |

- Core functions accept explicit paths (`input_path`, `output_path` / `output_dir`) and return plain dicts.
- Long-running work exposes a **synchronous** function with an optional `progress_cb(percent: int, message: str)`. Background/web jobs wrap that function in a thread; the CLI calls it directly.

## 3. CLI Conventions

| Topic | Rule |
| :--- | :--- |
| Framework | `argparse` (stdlib). No extra CLI dependencies. |
| Invocation | `tools <alias> <command> [args]` (global) or `./cli.sh <command> [args]` (standalone). Single-action tools may omit subcommands. |
| Program name | Read from `TOOLS_PROG` env var (set by the dispatcher), default `cli.sh`. |
| Startup | Heavy imports go **inside** command handlers so `--help` is instant. |
| Streams | Results → `stdout`. Progress, logs, warnings, errors → `stderr`. |
| Common flags | Every subcommand: `--json`, `-q/--quiet`, `-v/--verbose`. Top level: `-V/--version`. |
| `--json` | Prints a single JSON object to stdout (paths absolute). |
| Output files | Default to the **current working directory**. Without `-o`, never overwrite (`name-1.ext`, ...). With `-o`, write exactly there (a directory gets the default name). |
| Batch | Commands that take files accept multiple paths / globs when it makes sense. |
| stdin | Text inputs accept `-` to read from stdin when it makes sense. |
| Exit codes | `0` success · `1` runtime error · `2` usage error · `130` interrupted. |
| Errors | `error: <message>` on stderr, no traceback unless `-v`. |
| Language | All help text, messages, docs, and commits in **English**. |

## 4. Registration

`tool.json` (and the tool's entry in `tools-hub/tools.json`) must include:

```json
"cli": { "alias": "my", "command": "./cli.sh" }
```

Also add the repository to `TOOLS` in `setup.sh`.

## 5. Testing

- Tests use the standard library `unittest` and run the CLI via `subprocess` with `sys.executable`.
- Minimum coverage: `--help` for every subcommand, a usage error (exit 2), one real run per subcommand on a tiny fixture (generated in a temp dir), and valid `--json` output.
- Run: `python -m unittest discover -s tests -v` inside the tool's environment.

## 6. New Tool Checklist

- [ ] Business logic lives in `core/`, shared by `app.py` and `cli.py`
- [ ] `cli.py` + executable `cli.sh` following the conventions above
- [ ] `tool.json` has a `cli` block; tool registered in `tools.json` and `setup.sh`
- [ ] `AGENTS.md` documents exact `--json -q` CLI recipes and JSON output schema for AI agents
- [ ]Global skill `skills/redo-tools/SKILL.md` in `tools-hub` updated with the new tool's commands
- [ ] README documents both the Web Interface and the CLI
- [ ] `tests/test_cli.py` passes; existing web tests still pass
- [ ] Public GitHub repo created under `RedoRojo`, docs and commits in English
