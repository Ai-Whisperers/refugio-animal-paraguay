#!/usr/bin/env python3
"""
PreToolUse hook — Refugio Animal Paraguay
Blocks .env file access and destructive commands before they execute.
Exit 2 = block the operation and show message to user.
Exit 0 = allow.
"""
import json
import re
import sys

data = json.load(sys.stdin)
tool_name = data.get("tool_name", "")
tool_input = data.get("tool_input", {})

# ── Block direct .env file access ─────────────────────────────────────────────
file_path = str(tool_input.get("file_path", "") or tool_input.get("path", ""))
if re.search(r"\.env($|\.)", file_path):
    print(
        "BLOCKED: Direct .env file access denied.\n"
        "WHY: Secrets must not be read or written directly by Claude.\n"
        "HOW: Use os.environ[] in code; set values in the shell before running.",
        file=sys.stderr,
    )
    sys.exit(2)

# ── Block destructive Bash commands ───────────────────────────────────────────
if tool_name == "Bash":
    command = str(tool_input.get("command", "")).lower()
    destructive_patterns = [
        ("rm -rf", "recursive force delete"),
        ("sudo rm", "privileged file deletion"),
        ("drop table", "table destruction — data loss"),
        ("truncate table", "table truncation — data loss"),
        ("delete from", "bulk row deletion"),
        ("drop database", "database destruction"),
        ("drop schema", "schema destruction"),
    ]
    for pattern, description in destructive_patterns:
        if pattern in command:
            print(
                f"BLOCKED: Destructive operation detected — {description}.\n"
                f"WHY: Pattern '{pattern}' can cause irreversible data loss.\n"
                f"HOW: If this is intentional, run the command manually in the terminal.",
                file=sys.stderr,
            )
            sys.exit(2)

sys.exit(0)
