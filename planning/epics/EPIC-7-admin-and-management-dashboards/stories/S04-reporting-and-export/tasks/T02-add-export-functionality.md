---
task_id: T02
task_title: Add Export Functionality
task_status: pending
story_id: S04
epic_id: EPIC-7
created_date: 2026-03-25
estimated_effort: 5
dependencies:
  - T01 report generator (same data sources)
  - EPIC-10 RBAC (require_admin_role)
  - FastAPI StreamingResponse
---

# T02: Add Export Functionality

## Overview

The export functionality extends the report system by adding downloadable CSV export endpoints alongside the JSON report endpoints from T01. Each report has a corresponding export endpoint that returns the same data formatted as a comma-separated values file with proper headers. The response uses FastAPI's StreamingResponse with CSV content type and Content-Disposition header that triggers browser download. Large exports stream row-by-row to avoid loading all data into memory simultaneously.

## Why This Task Matters

European funding partners typically request reports in spreadsheet format, not JSON API responses. Accountants and board members reviewing donation records need to open the data in Excel or LibreOffice Calc. Manual export from database GUIs by developers is not scalable. CSV export endpoints let the admin download properly formatted spreadsheets on demand without technical assistance.

## Technical Requirements

The GET endpoint for shelter activity export produces CSV file output with the following columns in order: date showing each day in the range, species showing the animal type, intake_count showing animals taken in that day, adoption_count showing animals adopted that day, medical_event_count showing medical treatments that day, and volunteer_hours showing volunteer hours logged that day. One CSV row appears per day within the date range where any activity occurred. Days with no activity are omitted from the export.

The GET endpoint for financial export produces CSV with columns: date showing the donation date, donation_id as the unique identifier, donor_name_or_anonymous showing either the donor's name or "Anonymous Donor" based on visibility preference, amount_eur_cents showing the donation in euro-cents, amount_pyg showing any portion in Paraguayan Guaraní, campaign_title for the associated campaign if any, payment_method showing how payment was made, and status showing confirmation status. One CSV row appears per donation record.

The GET endpoint for adoption pipeline export produces CSV with columns: application_id, applicant_name, animal_name showing which animal, application_date, status showing current status, days_to_resolution computed as the difference between application date and final resolution date, and rejection_reason populated only for rejected applications. One CSV row appears per adoption application within the date range.

All export endpoints accept the same date_from and date_to query parameters as their JSON counterparts from T01 with identical default and validation behavior. Response headers include Content-Type of text/csv and Content-Disposition set to attachment with a descriptive filename that includes the report type and date range — for example "financial-report-2026-01-01-to-2026-03-31.csv" — so the downloaded file has a meaningful name.

The CSV generator uses Python's built-in csv module to produce properly escaped CSV that handles commas, quotes, and newlines within field values correctly. Streaming: the response yields rows incrementally from a generator function rather than assembling the entire CSV in memory; for the financial export with potentially thousands of rows this is important for memory efficiency.

All export endpoints require require_admin_role from EPIC-10. Donor privacy: the donor_name column in the financial export uses the donor's full name only when the donor explicitly opted into name visibility; otherwise the field shows "Anonymous Donor" to respect privacy preferences.

## Implementation Approach

FastAPI's StreamingResponse accepts a Python generator function as its content parameter. The generator function opens a StringIO buffer, creates a csv.writer bound to that buffer, and writes the header row, then yields that header row as a string. The generator then queries the database using SQLAlchemy's yield_per for memory-efficient iteration over result rows without loading all records into memory at once. For each database record, the generator yields one properly formatted CSV row string.

The filename in Content-Disposition is constructed from a report type constant and the formatted date range parameters. The stream generator function is defined as a nested function inside the endpoint handler so it has access to the validated query parameters and the database session from FastAPI's dependency injection system.

Privacy filtering for donor names is performed by checking a visibility flag on each donor record and substituting "Anonymous Donor" when appropriate. The CSV writer handles all escaping of special characters, eliminating the need for manual quote insertion or escape sequence handling.

## Success Criteria

Downloading the financial export and opening it in a spreadsheet application shows correct column headers, properly escaped values with no truncation or corruption, and one row per donation matching the database records for the specified date range. Anonymous donor entries display "Anonymous Donor" not personal names when visibility preference is false.

The streaming behavior must be verified by confirming the response begins returning data before all database rows are read. Test this with a database containing thousands of rows and confirm the first bytes arrive within 100 milliseconds. All export filenames include the date range in ISO 8601 format for traceability. Export files open in multiple spreadsheet applications without format errors.
