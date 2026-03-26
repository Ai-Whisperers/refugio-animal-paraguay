#!/usr/bin/env python3
"""
PreCompact hook — Refugio Animal Paraguay
Backs up the conversation transcript before Claude compacts the context.
Preserves full conversation history in ~/.claude/backups/refugio/.
"""
import json
import os
import shutil
import sys
from datetime import datetime

data = json.load(sys.stdin)
transcript_path = data.get("transcript_path", "")

if transcript_path and os.path.exists(transcript_path):
    backup_dir = os.path.expanduser("~/.claude/backups/refugio")
    os.makedirs(backup_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = os.path.join(backup_dir, f"transcript_{timestamp}.jsonl")
    shutil.copy(transcript_path, backup_path)
    print(f"Transcript backed up: {backup_path}", file=sys.stderr)

sys.exit(0)
