#!/usr/bin/env python3
"""
SessionStart hook — loads context and prints orientation info at session start.

Runs once when Claude Code session begins.
Exit 0: informational only, never blocks.
"""

import os
import sys
from datetime import datetime
from pathlib import Path


def find_active_ticket() -> str | None:
    """Read the active ticket ID from tickets/current.md."""
    current_file = Path("tickets/current.md")
    if current_file.exists():
        content = current_file.read_text().strip()
        if content and not content.startswith("#"):
            return content
        # Handle "# Active ticket: RAP-123" format
        for line in content.splitlines():
            if line.strip() and not line.startswith("#"):
                return line.strip()
    return None


def get_ticket_status(ticket_id: str) -> dict:
    """Read context.md for the active ticket."""
    context_file = Path(f"tickets/{ticket_id}/context.md")
    if not context_file.exists():
        return {"status": "UNKNOWN", "focus": "context.md not found"}

    content = context_file.read_text()
    status = "UNKNOWN"
    focus = ""
    for line in content.splitlines():
        if "STATUS:" in line:
            for s in ["ACTIVE", "PAUSED", "COMPLETED"]:
                if s in line:
                    status = s
                    break
        elif (
            focus == ""
            and status != "UNKNOWN"
            and line.strip()
            and not line.startswith("#")
        ):
            if "Current Focus" not in line:
                focus = line.strip()

    return {"status": status, "focus": focus[:120] if focus else ""}


def check_git_status() -> dict:
    """Get branch, dirty file count, and last commit."""
    import subprocess

    result: dict = {"branch": "unknown", "changed": 0, "last_commit": ""}
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
            result["last_commit"] = log.stdout.strip()[:70]
    except Exception:
        pass
    return result


def main() -> int:
    """Print session orientation context. Never blocks (always exit 0)."""
    now = datetime.now().strftime("%Y-%m-%d %H:%M")

    print(f"\n{'='*60}")
    print(f"  Session started: {now}")
    print(f"  Working dir: {os.getcwd()}")
    print(f"{'='*60}")

    # Active ticket
    ticket_id = find_active_ticket()
    if ticket_id:
        info = get_ticket_status(ticket_id)
        status_icon = {"ACTIVE": "🟢", "PAUSED": "🟡", "COMPLETED": "✅"}.get(
            info["status"], "❓"
        )
        print(f"\n  Active ticket: {ticket_id} {status_icon} {info['status']}")
        if info["focus"]:
            print(f"  Focus: {info['focus']}")
        print(f"\n  Resume: read tickets/{ticket_id}/context.md")
    else:
        print(f"\n  Active ticket: No active ticket. ❓ UNKNOWN")
        print(f"  Focus: context.md not found")
        print(f"\n  Resume: read tickets/No active ticket./context.md")

    # Git state
    git = check_git_status()
    git_state = (
        f"{git['changed']} modified/untracked files" if git["changed"] else "clean"
    )
    print(f"\n  Git: {git_state}")
    if git["branch"] != "unknown":
        print(f"  Branch: {git['branch']}")
    if git["last_commit"]:
        print(f"  Last commit: {git['last_commit']}")

    # Quick reminders
    print(f"\n  Quick commands:")
    print(f"    /start-ticket ID    Start or resume a ticket")
    print(f"    /pre-commit-check   Validate before committing")
    print(f"    /code-review        Review current changes")
    print(f"{'='*60}\n")

    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        # Never fail a session start
        sys.exit(0)
