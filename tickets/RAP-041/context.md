# RAP-041 Context

## STATUS: ACTIVE
**Last updated**: 2026-03-26

## Current Focus
Building Campaign model, migration, API endpoints, and frontend pages for the Donation Landing Page.

## Technical State
- Branch: feature/RAP-041-donation-landing-page
- New model: Campaign (SQLAlchemy)
- New migration: 013_create_campaigns_table
- New endpoints: /public/campaigns, /admin/campaigns
- Frontend: /donate page revamp + /donate/campaigns/[id] detail

## Next Steps
1. Create Campaign ORM model
2. Create Alembic migration
3. Create schemas and endpoints
4. Build frontend pages

## Blockers
- None

## Key Decisions Made
- Campaign model stores raised_amount_cents as computed from donations (not cached) for accuracy
- Using existing Stripe PaymentIntent flow, just linking to campaign_id
