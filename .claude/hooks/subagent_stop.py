#!/usr/bin/env python3
"""SubagentStop hook — prints a compact cost summary line for each subagent completion."""

import json
import sys


def main() -> None:
    try:
        data = json.load(sys.stdin)
        subagent_id = data.get("subagent_id", "")[:8]
        cost_usd = data.get("cost_usd", 0)
        print(f"  [subagent done] {subagent_id} — cost: ${cost_usd:.4f}")
    except Exception:
        pass


if __name__ == "__main__":
    main()
