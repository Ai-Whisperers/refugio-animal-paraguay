---
task_id: T02
task_title: Implement Campaign Management Backend
task_status: pending
story_id: S04
epic_id: EPIC-11
created_date: 2026-03-25
estimated_effort: 6
dependencies:
  - donation_campaigns table
  - EPIC-10 RBAC (require_admin_role for management endpoints)
  - T01 campaign listing endpoint
---

# T02: Implement Campaign Management Backend

## Overview

While T01 provides read-only public access to campaigns, this task implements the full admin CRUD interface for managing donation campaigns: creating new campaigns, updating existing campaign details and goals, activating and deactivating campaigns, and viewing campaign performance metrics. These admin endpoints require the admin role from EPIC-10's RBAC system and are served on a separate admin router rather than the public portal router.

## Why This Task Matters

The Dutch owner and shelter administrators must be able to create new fundraising campaigns without developer involvement. Campaigns for specific causes — veterinary emergencies, food drives, construction projects — must go live quickly when the need arises. The ability to set goals, write bilingual descriptions, and track progress against targets is essential for the donor communication strategy. Admin management of campaigns closes the loop between the public-facing display from T01 and the internal operations.

## Technical Requirements

The POST endpoint for campaign creation accepts a JSON request body and creates a new campaign record. Required fields in the request body are title_es containing the Spanish language campaign name, description_es for the Spanish language description, and goal_amount_cents as an integer representing the fundraising target in euro-cents. Optional fields are title_nl for Dutch language title, description_nl for Dutch language description, and sort_order to control display position on the public listing. The is_active field defaults to true when not specified, making new campaigns immediately visible on the public portal. The campaign_id is generated as a UUID by the application, not by the database sequence.

The GET endpoint for listing all campaigns returns all campaigns regardless of whether they are marked active or inactive, including for each campaign the raised_amount_cents aggregate computed the same way as T01, plus an additional donor_count field showing the number of unique donors who have contributed to that campaign. Results are sorted by created_at descending so the most recently created campaigns appear first.

The GET endpoint for a single campaign by identifier in the path returns the full details for that campaign including an extended donation history summary showing the total number of unique donors, the total confirmed amount raised, and the timestamp of the most recent donation received for that campaign.

The PATCH endpoint for updating campaigns accepts a JSON body containing any subset of mutable fields: title_es, title_nl, description_es, description_nl, goal_amount_cents, sort_order, and is_active. The endpoint updates only the fields present in the request body, leaving absent fields unchanged. The immutable fields campaign_id and created_at cannot be modified and attempting to include them in the request body returns an error. Database-level constraints prevent goal_amount_cents from being updated to zero or negative values.

Deactivating a campaign by setting is_active to false through the PATCH endpoint hides it from the public portal listing immediately without deleting the campaign record or its associated donation records. This allows campaign reactivation if needed and preserves the financial history.

All admin campaign endpoints require the require_admin_role dependency from EPIC-10, meaning only authenticated users with admin role can access these endpoints. Staff and adopter role tokens receive a 403 forbidden response.

## Implementation Approach

The Pydantic model for creating campaigns uses field validation to enforce that goal_amount_cents is a positive integer greater than zero. The model validates that at least one of the two title variants and at least one of the two description variants is provided — campaigns cannot be created with no language variants. The update model uses Optional type annotations for all mutable columns, allowing each field to be independently specified or omitted, which enables true partial updates where unchanged fields preserve their current values.

SQLAlchemy model-level validation runs before database commits and prevents goal_amount_cents from being updated to zero or negative values with a clear error message. The admin GET endpoint for listing campaigns includes an aggregate subquery that counts the number of distinct donor_id values for each campaign using a COUNT DISTINCT expression, and joins this with the regular raised_amount_cents aggregation from T01.

The single-campaign detail endpoint queries the donations table filtered by campaign_id and confirmed status to build the donation history summary. It uses a SELECT with COUNT DISTINCT for donor count, SUM for total amount, and MAX for the most recent donation timestamp. If no donations exist, these aggregates return zero and null respectively.

The create operation persists the campaign with the provided values and returns the created campaign object with all fields populated. The update operation reads the current state before modification for audit purposes, applies the updates, and returns the modified campaign. Both create and update endpoints record changes to the audit log table with admin_user_id, affected campaign_id, changed fields, and timestamp for traceability.

## Success Criteria

Creating a campaign with valid values must make that campaign immediately visible on the public portal listing via the T01 endpoint when subsequent requests are made. Deactivating a campaign through PATCH must remove it from public listing within the same request cycle with no caching delays. All CRUD operations are idempotent where semantically appropriate: updating a campaign with unchanged values produces no error and returns the current campaign state unmodified.

Admin endpoints must enforce authentication by returning 403 forbidden for requests with staff or adopter role tokens. Creating a campaign without a title in either language must return 422 unprocessable entity. Setting goal_amount_cents to zero or negative must return 422 unprocessable entity.

Performance target: all admin endpoints must respond within 500 milliseconds for typical operations including database roundtrips. Listing 50 campaigns with aggregate calculations must still meet this target.
