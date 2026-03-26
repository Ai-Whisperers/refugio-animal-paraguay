#!/usr/bin/env python3
"""
Stop hook — prints session summary and sends desktop notification when Claude finishes.

Runs after every Claude response that ends a turn.
Exit 0: informational only, never blocks.
"""

import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path


def get_git_summary() -> dict:
    """Get changed file count and current branch."""
    result = {"branch": "unknown", "changed": 0, "last_commit": ""}
    try:
        branch = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            capture_output=True,
            text=True,
            cwd=os.getcwd(),
        )
        if branch.returncode == 0:
            result["branch"] = branch.stdout.strip()

        status = subprocess.run(
            ["git", "status", "--porcelain"],
            capture_output=True,
            text=True,
            cwd=os.getcwd(),
        )
        if status.returncode == 0:
            result["changed"] = len(
                [l for l in status.stdout.splitlines() if l.strip()]
            )

        log = subprocess.run(
            ["git", "log", "--oneline", "-1"],
            capture_output=True,
            text=True,
            cwd=os.getcwd(),
        )
        if log.returncode == 0:
            result["last_commit"] = log.stdout.strip()[:60]
    except Exception:
        pass
    return result


def get_active_ticket() -> str | None:
    """Read active ticket from tickets/current.md."""
    current_file = Path("tickets/current.md")
    if current_file.exists():
        content = current_file.read_text().strip()
        for line in content.splitlines():
            line = line.strip()
            if line and not line.startswith("#"):
                return line
    return None


def notify(title: str, body: str) -> None:
    """Send desktop notification — silently skip if not available."""
    try:
        subprocess.run(
            ["notify-send", "--urgency=low", "--expire-time=5000", title, body],
            capture_output=True,
            timeout=3,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass  # notify-send not available — headless or no display


def main() -> int:
    """Print session end summary. Never blocks."""
    git = get_git_summary()
    ticket = get_active_ticket()
    now = datetime.now().strftime("%H:%M")

    summary_parts = []
    if ticket:
        summary_parts.append(f"ticket: {ticket}")
    if git["changed"]:
        summary_parts.append(f"{git['changed']} file(s) changed")
    if git["branch"] != "unknown":
        summary_parts.append(f"branch: {git['branch']}")

    summary = " | ".join(summary_parts) if summary_parts else "no changes"

    print(f"\n[{now}] Claude finished — {summary}")
    if git["last_commit"]:
        print(f"  Last commit: {git['last_commit']}")

    # Desktop notification
    notify_body = summary
    notify("Claude Code", notify_body)

    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        sys.exit(0)
