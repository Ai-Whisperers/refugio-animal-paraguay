---
task_id: T01
task_title: Implement Report Generator
task_status: pending
story_id: S04
epic_id: EPIC-7
created_date: 2026-03-25
estimated_effort: 7
dependencies:
  - EPIC-10 RBAC (require_admin_role)
  - All data tables: animals, donations, adoption_requests, volunteers
---

# T01: Implement Report Generator

## Overview

The report generator provides a set of admin endpoints that aggregate data from across the application and return structured summaries useful for monthly operational reviews, funding reports to European donors, and year-end summaries. Reports are pre-defined and named — there is no ad-hoc query builder. The three primary reports are: the shelter activity report showing animal intakes, adoptions, medical events, and volunteer hours over a date range; the financial report showing donations by currency, by campaign, by payment method, and comparing total received versus goals; and the adoption pipeline report showing applications grouped by status, average processing time, and success rate.

## Why This Task Matters

The Dutch owner must report regularly to European funding partners on shelter outcomes and financial accountability. Without structured reporting endpoints, these reports require manual database queries by a developer, introducing delay and human error into what should be a routine operational process. Named reports with date range parameters allow the admin to generate precise reports for the exact period their funding partners need without technical assistance.

## Technical Requirements

The GET endpoint for shelter activity report accepts query parameters date_from and date_to specified as ISO 8601 date strings. The response contains: total_animals_by_species showing dogs count, cats count, and other species count reflecting what animals are currently in shelter; intake_count_in_period showing how many animals were taken in during the date range; adoption_count_in_period showing how many animals were adopted during the date range; medical_events_count_in_period showing how many medical treatment records were created during the date range; and volunteer_hours_logged_in_period showing the sum of hours from volunteer shift records with timestamps in the date range.

The GET endpoint for financial report accepts the same date_from and date_to query parameters and returns: total_donations_eur as the sum of donations with currency_code equal to EUR, total_donations_pyg as the sum of donations with currency_code equal to PYG, total_by_campaign as an array of objects each containing campaign title and its total received amount, total_by_payment_method showing aggregates grouped by payment method, and month_by_month_breakdown as an ordered list of monthly aggregates each containing the month, amount_eur, and amount_pyg.

The GET endpoint for adoption pipeline report returns a current snapshot with no date range needed: count_by_status showing how many applications are in each status including pending, under_review, approved, rejected, and completed; median_days_from_application_to_final_status computed from the adoption_requests table; most_common_rejection_reasons as a list of the top rejection reasons found in the last 50 rejection records with frequency counts.

All report endpoints require require_admin_role dependency from EPIC-10. Date range validation enforces that date_from must be before date_to. The maximum allowed date range is 366 days to prevent excessively expensive queries. If no dates are provided in the request, the default range is the last 30 days from today. Response includes a generated_at timestamp showing when the report was generated and the date_range field containing the start and end dates used, including any applied defaults, so reports are self-documenting.

## Implementation Approach

Each report endpoint performs multiple targeted SQL queries via SQLAlchemy and assembles the results into the response model structure. The shelter activity report uses COUNT queries with date-range filters on the animals, donations, medical_events, and volunteer_shifts tables. Species counting uses GROUP BY species to break down totals. The financial report groups donations by month using database-level date truncation to extract year and month from the created_at timestamp, then aggregates by currency and by payment_method. Results include campaign information via a join to the donation_campaigns table.

The adoption pipeline report uses a status-based GROUP BY query to count applications in each status. Processing time calculation uses SQLAlchemy's percentile_cont aggregate function available in PostgreSQL 9.4 and later to compute the median of the date difference between created_at and final_status_date. The most common rejection reasons require reading the last 50 rejection records and performing frequency analysis in Python using standard collections.Counter rather than SQL for implementation simplicity and to avoid complex SQL patterns.

All queries use parameterized inputs from FastAPI's Query parameter injection to prevent SQL injection and to validate input types at the FastAPI layer. Date parameters are parsed and validated using Python's datetime.date.fromisoformat method through Pydantic validation.

## Success Criteria

All three reports return complete data matching manual verification against the database. Date range defaults work correctly when no parameters are provided in the request. Invalid date ranges such as end date before start date, or a range exceeding 366 days, return 422 unprocessable entity with a descriptive error message. Performance target: all reports respond within 3 seconds for a 1-year date range with 10,000 donation records and 2,000 adoption requests.

Reports include generated_at and date_range fields in response. Tests verify shelter activity counts match raw table record counts for the date range. Tests verify financial totals by currency match summing all donations filtered by currency. Tests verify adoption pipeline status distribution is correct. Tests verify default date range behavior when no parameters provided.
