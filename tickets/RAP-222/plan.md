# RAP-222 Plan

## Objective
Redesign the in-app notification center as a bell-icon dropdown accessible from every admin page.

## Description
Currently there is no visual notification indicator in the admin UI. This story adds a NotificationCenter component: a bell icon with unread count badge in the admin layout's top bar, opening a dropdown with recent notifications, mark-as-read, and delete actions.

## Acceptance Criteria
- [ ] Bell icon visible in admin top bar on all pages
- [ ] Unread count badge updates every 30 seconds
- [ ] Dropdown shows last 20 notifications with relative timestamps
- [ ] Mark individual notification as read via button
- [ ] Mark all as read in one click
- [ ] Delete individual notifications
- [ ] Empty state message when no notifications
- [ ] Click outside / ESC closes dropdown
- [ ] Accessible: ARIA, keyboard navigation

## Complexity Assessment
**Track**: Simple Fix — new component + layout update. 2 files modified, 1 new file.
