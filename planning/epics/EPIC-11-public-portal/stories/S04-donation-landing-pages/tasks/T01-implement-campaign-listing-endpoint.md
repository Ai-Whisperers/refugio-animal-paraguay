---
task_id: T01
task_title: Implement Campaign Listing Endpoint
task_status: pending
story_id: S04
epic_id: EPIC-11
created_date: 2026-03-25
estimated_effort: 5
dependencies:
  - donation_campaigns database table
  - donations table for aggregate totals
  - Public portal router with no authentication requirement
---

# T01: Implement Campaign Listing Endpoint

## Overview

The campaign listing endpoint is a public, unauthenticated GET endpoint that returns all currently active donation campaigns. Each campaign record includes its title, description in Spanish and Dutch, fundraising goal in euro-cents, the current total of confirmed donations aggregated from the donations table, and a computed percentage showing how close the campaign is to its goal. The response is designed to power the donation landing page that EU-based donors from the Dutch owner's network will see, so it includes Dutch language content alongside Spanish.

## Why This Task Matters

Donations are the financial lifeline of Refugio Animal Paraguay. The Dutch owner has an extensive European fundraising network, so the donation landing page must speak to both Spanish-speaking local supporters and Dutch-speaking European donors. Campaign-based fundraising with visible progress toward goals is a proven donor engagement technique — donors are more likely to give when they see momentum and a specific purpose for their funds. This endpoint drives that experience.

## Technical Requirements

The endpoint implements a GET request handler that queries the donation_campaigns table for all records where the is_active column is true. The response includes the following fields for each campaign: campaign_id as a UUID identifier, title_es containing the Spanish language campaign name, title_nl containing the Dutch language campaign name which may be null if not provided, description_es for the Spanish language campaign description, description_nl for the Dutch language description also nullable, goal_amount_cents as an integer representing the fundraising objective in euro-cents, and raised_amount_cents as an integer computed as the sum of amount_cents from the donations table where the campaign_id matches and the donation status is confirmed.

The percentage_funded field is computed as raised_amount_cents divided by goal_amount_cents multiplied by 100 to produce a decimal percentage. This percentage is capped at 100.0 to handle edge cases where donations slightly exceed the goal due to rounding or timing windows between queries. The response also includes is_active to confirm the campaign is active and created_at showing when the campaign record was created.

The query results are sorted first by the sort_order column in ascending order, then by created_at in descending order for any campaigns sharing equal sort_order values. This stable sort ensures that within each priority tier, newer campaigns appear first.

The aggregate query for raised_amount_cents uses a correlated subquery or SQLAlchemy's func.sum combined with a join against the donations table filtered to confirmed status. Using a LEFT JOIN ensures campaigns with zero donations still appear in the result set with raised_amount_cents of zero rather than being omitted.

No authentication is required — this endpoint must be accessible to anonymous visitors arriving at the donation landing page. Cross-origin resource sharing headers must permit the frontend origin so browser-based JavaScript fetch requests can successfully call this endpoint and update the donation landing page with current campaign progress.

## Implementation Approach

The endpoint function performs a SQLAlchemy query against the donation_campaigns table with a LEFT JOIN to a subquery that aggregates confirmed donation totals grouped by campaign_id. The subquery is constructed using SQLAlchemy's select statement with an alias for clarity. The main query filters for is_active equals true and orders by sort_order ascending then created_at descending.

The Pydantic response model is defined as a list containing campaign item objects. Each item model includes all required fields with appropriate type annotations. Computed fields are implemented using Pydantic's computed_field decorator on percentage_funded. The percentage_funded field computes from goal_amount_cents and raised_amount_cents after the database returns raw values. A field validator on percentage_funded ensures the computed value never exceeds 100.0.

The endpoint does not paginate because the total number of active campaigns is expected to remain small across the shelter's operational lifetime. If this assumption changes in the future, pagination can be added without breaking the existing interface by adding optional limit and offset query parameters with sensible defaults.

## Success Criteria and Testing Strategy

The endpoint must return correct aggregate totals that match manual sum verification against the donations table for the specified campaign. A test harness creates multiple campaigns and multiple donations against each, then verifies the endpoint response includes correct raised_amount_cents values.

Tests verify that a campaign with no donations returns raised_amount_cents of zero and percentage_funded of 0.0. Tests verify that a campaign with donations exceeding the goal returns percentage_funded of 100.0 never higher than that. Tests verify Dutch language fields are null when not provided and appear as strings when provided. Tests verify that deactivated campaigns do not appear in the response.

Performance target is a response within 200 milliseconds for a typical shelter with 10 active campaigns, including the aggregate query execution time. This is measured with database connection pooling active and typical database load. Monitoring should track query duration to alert if database performance degrades in production.
