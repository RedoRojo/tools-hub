#!/usr/bin/env python3
"""
Example Tool - Command Line Interface.

Thin adapter over core/: parses arguments, calls core functions synchronously,
and prints results. It must never import the web app (app.py) or FastAPI.

Conventions (see TOOL_STANDARD.md in tools-hub):
- Results go to stdout; progress, logs, and errors go to stderr.
- Every subcommand accepts --json, -q/--quiet, and -v/--verbose.
- Output files default to the caller's current working directory.
- Exit codes: 0 success, 1 runtime error, 2 usage error, 130 interrupted.
- Heavy modules are imported lazily inside each command handler.
"""

import argparse
import json
import os
import sys
from pathlib import Path

__version__ = "1.0.0"

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))  # make core/ importable from any working directory

PROG = os.environ.get("TOOLS_PROG", "cli.sh")
EXIT_OK, EXIT_ERROR, EXIT_USAGE, EXIT_INTERRUPTED = 0, 1, 2, 130


class CLIError(Exception):
    """Expected runtime error: printed without a traceback, exits with code 1."""


# ---------------------------------------------------------------------------
# Output helpers
# ---------------------------------------------------------------------------

def log(args, message: str) -> None:
    """Print a progress/info message to stderr unless --quiet is set."""
    if not getattr(args, "quiet", False):
        print(message, file=sys.stderr, flush=True)


def emit(args, payload: dict, human: str) -> None:
    """Print the command result to stdout as JSON (--json) or human-readable text."""
    if getattr(args, "json", False):
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    elif human:
        print(human)


def resolve_output(requested, default_name: str) -> Path:
    """
    Resolve an output path.
    - Explicit -o paths are used as-is (directories get default_name appended).
    - Without -o, write default_name to the current directory, never overwriting
      an existing file (name.ext -> name-1.ext -> name-2.ext ...).
    """
    if requested:
        path = Path(requested).expanduser()
        if path.is_dir():
            path = path / default_name
        path.parent.mkdir(parents=True, exist_ok=True)
        return path.resolve()

    path = Path.cwd() / default_name
    stem, suffix, counter = path.stem, path.suffix, 1
    while path.exists():
        path = path.with_name(f"{stem}-{counter}{suffix}")
        counter += 1
    return path.resolve()


# ---------------------------------------------------------------------------
# Command handlers
# ---------------------------------------------------------------------------

def cmd_greet(args) -> int:
    from core.logic import greet  # lazy import keeps --help instant

    message = greet(args.name, shout=args.shout)
    emit(args, {"message": message}, message)
    return EXIT_OK


# ---------------------------------------------------------------------------
# Parser
# ---------------------------------------------------------------------------

def add_common_flags(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--json", action="store_true", help="print machine-readable JSON to stdout")
    parser.add_argument("-q", "--quiet", action="store_true", help="suppress progress messages")
    parser.add_argument("-v", "--verbose", action="store_true", help="show full tracebacks on errors")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog=PROG,
        description="Example Tool - replace with a one-line description.",
    )
    parser.add_argument("-V", "--version", action="version", version=f"%(prog)s {__version__}")
    sub = parser.add_subparsers(dest="command", metavar="<command>")

    p = sub.add_parser("greet", help="print a greeting", description="Print a greeting.")
    p.add_argument("name", help="who to greet")
    p.add_argument("--shout", action="store_true", help="uppercase the greeting")
    add_common_flags(p)
    p.set_defaults(func=cmd_greet)

    return parser


def main(argv=None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if not getattr(args, "func", None):
        parser.print_help(sys.stderr)
        return EXIT_USAGE

    try:
        return args.func(args) or EXIT_OK
    except CLIError as e:
        print(f"error: {e}", file=sys.stderr)
        return EXIT_ERROR
    except KeyboardInterrupt:
        print("Interrupted.", file=sys.stderr)
        return EXIT_INTERRUPTED
    except Exception as e:  # unexpected failure
        if getattr(args, "verbose", False):
            raise
        print(f"error: {e} (use -v for details)", file=sys.stderr)
        return EXIT_ERROR


if __name__ == "__main__":
    sys.exit(main())
