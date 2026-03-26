#!/bin/bash
# queue-status.sh — Cross-reference QUEUE.md with ticket directories and git branches
#
# Usage: ./scripts/queue-status.sh
# Run from project root to verify queue state matches reality.

set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$PROJECT_ROOT"

echo "========================================="
echo "  Queue Status Report"
echo "  $(date '+%Y-%m-%d %H:%M')"
echo "========================================="
echo ""

# Check completed tickets
echo "--- Completed Tickets ---"
for ticket_dir in tickets/RAP-*/; do
    if [ -d "$ticket_dir" ]; then
        ticket_id=$(basename "$ticket_dir")
        status="UNKNOWN"
        if [ -f "$ticket_dir/context.md" ]; then
            status=$(grep -oP 'STATUS:\s*\K\w+' "$ticket_dir/context.md" 2>/dev/null || echo "NO_STATUS")
        fi
        has_recap="no"
        [ -f "$ticket_dir/recap.md" ] && has_recap="yes"
        has_review="no"
        [ -f "$ticket_dir/review-notes.md" ] && has_review="yes"
        echo "  $ticket_id: status=$status recap=$has_recap review=$has_review"
    fi
done
echo ""

# Check active branches
echo "--- Feature Branches ---"
git branch --list 'feature/*' 2>/dev/null | while read -r branch; do
    branch_name=$(echo "$branch" | sed 's/^[* ]*//')
    ticket_id=$(echo "$branch_name" | grep -oP 'RAP-\d+' || echo "NO_TICKET")
    has_pr="no"
    if command -v gh &>/dev/null; then
        pr_count=$(gh pr list --head "$branch_name" --state open --json number 2>/dev/null | grep -c "number" || true)
        [ "$pr_count" -gt 0 ] && has_pr="yes"
    fi
    echo "  $branch_name: ticket=$ticket_id pr=$has_pr"
done
echo ""

# Check current ticket
echo "--- Active Ticket ---"
if [ -f tickets/current.md ]; then
    current=$(cat tickets/current.md | tr -d '[:space:]')
    if [ -z "$current" ] || [ "$current" = "Noactiveticket."* ]; then
        echo "  None"
    else
        echo "  $current"
    fi
else
    echo "  No current.md file"
fi
echo ""

# Count QUEUE.md statuses
echo "--- Queue Summary ---"
if [ -f planning/QUEUE.md ]; then
    done_count=$(grep -c "DONE" planning/QUEUE.md 2>/dev/null || echo 0)
    ready_count=$(grep -c "READY" planning/QUEUE.md 2>/dev/null || echo 0)
    blocked_count=$(grep -c "BLOCKED" planning/QUEUE.md 2>/dev/null || echo 0)
    echo "  DONE: $done_count | READY: $ready_count | BLOCKED: $blocked_count"
else
    echo "  QUEUE.md not found"
fi
echo ""
echo "========================================="
