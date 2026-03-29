# RAP-222 Context

## STATUS: ACTIVE
**Last updated**: 2026-03-29 00:10

## Current Focus
NotificationCenter component created. Admin layout updated to include it in top bar.

## Technical State
- NotificationCenter.tsx: bell + dropdown, polling every 30s, mark read/all, delete
- admin/layout.tsx: top bar with 14px height added, NotificationCenter integrated
- Uses api.get/patch/post/delete from @/lib/api

## Next Steps
1. Commit and create PR

## Key Decisions Made
- Poll every 30s for unread count (SSE stream added in RAP-224)
- 20 notification limit per fetch (enough for small shelters)
- Relative timestamps (Hace Xm/h/d) for Spanish UX
