# RAP-041 Context

## STATUS: COMPLETED
**Last updated**: 2026-03-26

## Current Focus
Completed. PR #51 submitted targeting develop.

## Technical State
- Branch: feature/RAP-041-donation-landing-page
- 3 commits on branch
- Migration 013 applied to dev database
- 38 new tests (18 unit + 20 integration), all passing
- PR: https://github.com/Ai-Whisperers/refugio-animal-paraguay/pull/51

## Key Decisions Made
- Campaign progress computed at query time from CampaignDonation junction + Donation joins (not cached)
- Only completed donations count towards progress (pending donations excluded)
- Admin campaign list returns raw list (not paginated), public list is paginated
- Multi-currency support: EUR/USD use cents (÷100), PYG uses whole units
- DynamicIcon component maps string icon names to lucide-react components
- Replaced emoji unicode escapes with lucide-react icons across all pages
