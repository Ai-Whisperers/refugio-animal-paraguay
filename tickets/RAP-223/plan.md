# RAP-223 Plan

## Objective
Group in-app notifications by type with collapsible threads and per-group unread counts.

## Description
The existing notification center shows a flat list. This story adds grouping by type (e.g. "Solicitudes de adopcion", "Donaciones recibidas") with collapsible accordion sections. Groups auto-expand when they have unread items. Each group shows a count badge and a "Leer" quick-action.

## Acceptance Criteria
- [ ] useGroupedNotifications hook groups flat list by notification_type
- [ ] Groups sorted by most-recent notification activity
- [ ] Each group is collapsible (expands/collapses on click)
- [ ] Groups with unread items auto-expand on page load
- [ ] Per-group unread count badge
- [ ] "Leer" button marks all notifications in a group as read
- [ ] Dedicated /admin/notifications page shows grouped view
- [ ] Accessible: ARIA expanded, proper list roles

## Complexity Assessment
**Track**: Simple Fix — hook + new page. 2 new files, no modifications to existing.

## Approach
1. Create useGroupedNotifications hook (pure computation)
2. Create /admin/notifications grouped page
3. Link from admin settings
