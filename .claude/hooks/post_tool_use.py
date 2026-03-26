#!/usr/bin/env python3
"""
PostToolUse hook — auto-format Python and TypeScript files after edits.

Triggered after every tool use. Reads tool name and file path from stdin JSON.
Exit 0: always (informational only, non-blocking).
"""

import json
import subprocess
import sys
from pathlib import Path


# File types that trigger auto-format
PYTHON_EXTENSIONS = {".py"}
TS_EXTENSIONS = {".ts", ".tsx", ".js", ".jsx"}


def get_tool_input() -> dict:
    """Read tool use data from stdin."""
    try:
        data = json.loads(sys.stdin.read())
        return data
    except (json.JSONDecodeError, ValueError):
        return {}


def format_python(filepath: str) -> bool:
    """Run black + isort on a Python file. Returns True if successful."""
    path = Path(filepath)
    if not path.exists() or path.suffix not in PYTHON_EXTENSIONS:
        return False

    # isort first, then black
    for cmd in [
        ["python3", "-m", "isort", "--quiet", str(path)],
        ["python3", "-m", "black", "--quiet", str(path)],
    ]:
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode not in (0, 1):  # black exits 1 on reformatted
            return False
    return True


def format_typescript(filepath: str) -> bool:
    """Run prettier on a TS/JS file. Returns True if successful."""
    path = Path(filepath)
    if not path.exists() or path.suffix not in TS_EXTENSIONS:
        return False

    # Check if prettier is available
    check = subprocess.run(
        ["npx", "prettier", "--version"],
        capture_output=True, text=True
    )
    if check.returncode != 0:
        return False

    result = subprocess.run(
        ["npx", "prettier", "--write", "--log-level", "warn", str(path)],
        capture_output=True, text=True
    )
    return result.returncode == 0


def extract_filepath(tool_data: dict) -> str | None:
    """Extract the file path from tool input data."""
    tool_input = tool_data.get("tool_input", {})

    # Write / Edit tools use file_path
    if "file_path" in tool_input:
        return tool_input["file_path"]

    # Notebook edit uses notebook_path
    if "notebook_path" in tool_input:
        return tool_input["notebook_path"]

    return None


def main() -> int:
    """Auto-format edited files. Never blocks."""
    tool_data = get_tool_input()
    tool_name = tool_data.get("tool_name", "")

    # Only trigger on file write/edit operations
    if tool_name not in ("Write", "Edit", "MultiEdit"):
        return 0

    filepath = extract_filepath(tool_data)
    if not filepath:
        return 0

    path = Path(filepath)
    ext = path.suffix.lower()

    if ext in PYTHON_EXTENSIONS:
        if format_python(filepath):
            # Silently formatted — don't spam output
            pass

    elif ext in TS_EXTENSIONS:
        if format_typescript(filepath):
            pass

    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        # Never block on PostToolUse failure
        sys.exit(0)
