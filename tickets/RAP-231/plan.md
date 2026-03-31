# RAP-231 Plan

## Objective
Add a GDPR-compliant cookie consent banner with essential/analytics preference controls displayed at the bottom of every page.

## Description
A cookie consent banner must appear for first-time visitors, offering them the ability to accept all cookies, reject optional ones, or customize their choices. Preferences are persisted in localStorage and accessible to other components via a useCookieConsent hook.

## Acceptance Criteria
- [ ] Banner visible on first visit until user makes a choice
- [ ] Three actions: Accept All, Essential Only, Customize
- [ ] Preferences modal with essential (forced on), analytics, marketing (disabled) toggles
- [ ] Consent stored in localStorage under `rap_cookie_consent`
- [ ] Link to /privacy policy page in banner text
- [ ] Accessible: role=banner, role=dialog, aria-labels, keyboard navigable
- [ ] Banner placed in root layout so it appears on all pages

## Complexity Assessment
**Track**: Simple Fix — new self-contained client component added to layout.

**Assessment result**: Simple Fix — isolated component with no backend dependency.

## Approach
1. Add COOKIE_CONSENT strings to strings.ts
2. Create CookieConsentBanner component with banner + preferences modal
3. Create useCookieConsent hook for reading preferences
4. Add CookieConsentBanner to root layout.tsx
5. Commit

## Dependencies
- None (reads /privacy page link, which is added in RAP-230 PR)

## Risks
- Risk: Banner interferes with BottomNav z-index → Mitigation: Banner uses z-40, BottomNav uses z-50
