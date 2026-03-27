# RAP-122 Plan

## Objective
Add breadcrumb navigation to the admin layout showing the current location in the admin hierarchy.

## Acceptance Criteria
- [x] Breadcrumbs show current location (e.g., Admin > Animals > Detalle)
- [x] Known segments use Spanish labels (Animales, Adopciones, etc.)
- [x] UUID/numeric segments display as "Detalle"
- [x] Last breadcrumb item is non-clickable (current page)
- [x] Breadcrumbs hidden on shallow pages (dashboard, admin root)

## Complexity Assessment
**Assessment result**: Simple Fix — single component creation + layout integration

## Approach
1. Create Breadcrumbs component with pathname parsing
2. Export buildBreadcrumbs utility for testing
3. Integrate into admin layout
