# Agent Guide — Example Tool (`tools example`)

Fast instructions for AI coding agents using or modifying this tool.

## 1. Using This Tool from an Agent

- **Never start the web server (`./run.sh`)** to run a one-off task. Always call the CLI.
- **Always pass `--json -q`** for structured output on `stdout` and silent progress on `stderr`.
- **Exit codes**: `0` success, `1` runtime error, `2` usage error.

### Commands
```bash
tools example greet "Ada" --json -q
tools example greet "Ada" --shout --json -q
```

### JSON Output Schema (`greet`)
```json
{
  "message": "Hello, Ada!"
}
```

## 2. Architecture for Contributors

- `core/logic.py`: Pure business logic (no FastAPI, no `print`).
- `app.py`: Web adapter (FastAPI).
- `cli.py` / `cli.sh`: CLI adapter (`argparse`). Never `cd` inside `cli.sh`.
- `tests/test_cli.py`: `unittest` test suite. Run with `.venv/bin/python -m unittest discover -s tests -v`.
