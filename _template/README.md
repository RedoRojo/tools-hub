# Example Tool

One-paragraph description of what the tool does.

## 🌐 Web Interface

```bash
./run.sh
```

Opens at **http://127.0.0.1:8005** (or launch it from **Tools Hub**).

## ⌨️ Command Line Interface

Via the global Tools Hub dispatcher (recommended):

```bash
tools example greet "Ada"
tools example greet "Ada" --json
```

Or standalone from this repository:

```bash
./cli.sh greet "Ada"
```

Run `tools example --help` or `tools example <command> --help` for all options.

## 🧪 Running Tests

```bash
.venv/bin/python -m unittest discover -s tests -v
```
