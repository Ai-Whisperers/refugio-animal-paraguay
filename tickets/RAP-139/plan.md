# RAP-139 Plan

## Objective
Add a rich text editor for detailed veterinary notes on the vet visit form, allowing staff to format notes with bold, lists, and headings.

## Description
Vet visit notes currently use a plain textarea. This story adds rich text editing capability (bold, italic, lists, headings) to the vet notes field in the vet visit form. Uses a lightweight client-side editor following existing frontend patterns.

## Acceptance Criteria
- [ ] Notes field uses a rich text editor (bold, italic, unordered list, ordered list, headings)
- [ ] Formatted content is saved to the API as HTML or markdown
- [ ] Notes can be displayed as formatted text when viewing a visit record
- [ ] Editor shows toolbar with formatting controls
- [ ] Empty state and placeholder text shown
- [ ] Content is cleared after successful save

## Complexity Assessment
**Track**: Simple Fix

**Assessment result**: Simple — new component using browser-native contenteditable or lightweight library

## Approach
1. Build a minimal rich text editor component using `contenteditable` div with formatting commands
2. Integrate into the vet visit form (`/admin/animals/[id]` page or new vet visit form)
3. Follow existing admin page patterns (Spanish labels, Tailwind CSS)

## Dependencies
- Existing admin animal detail/edit pages
- No new npm packages needed (use document.execCommand or browser native approach)

## Risks
- execCommand is deprecated — use a controlled approach with Selection API
  Mitigation: Use a well-established pattern with proper fallback
