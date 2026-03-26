---
task_id: T01
task_title: Build Settings Interface Endpoints
task_status: pending
story_id: S03
epic_id: EPIC-7
created_date: 2026-03-25
estimated_effort: 5
dependencies:
  - system_settings table (key-value store)
  - EPIC-10 RBAC (require_admin_role)
  - Configuration service (T02)
---

# T01: Build Settings Interface Endpoints

## Overview

The settings interface provides two endpoints: GET returns all system configuration settings as a structured JSON object, and PATCH accepts partial updates to modify one or more settings values. Settings are stored in a key-value table in the database with typed values serialized to text storage. The interface presents settings in a categorized structure grouping related settings together: email configuration, payment thresholds, shelter information, and notification preferences.

## Why This Task Matters

Hardcoded configuration values embedded in application code require developer deployments to change. The shelter administrator should be able to update the donation minimum amount, shelter contact email, WhatsApp notification phone number, and other operational parameters through the admin dashboard without touching code. Storing these values in the database and exposing them through an authenticated API endpoint enables self-service configuration management and reduces operational delays.

## Technical Requirements

The GET endpoint for admin settings retrieves all current configuration values and returns them organized into categories. Each category is a named object within the response JSON, and each category contains key-value pairs where the values are returned as their semantic types — integers for numeric settings, strings for text settings, booleans for feature flags — rather than all values being represented as strings. The categories included are email containing smtp_host, smtp_port, smtp_from_address, and smtp_from_name. Payment category contains minimum_donation_eur_cents, maximum_donation_eur_cents, and stripe_webhook_timeout_seconds. Shelter category contains shelter_name_es, shelter_name_nl, contact_phone, whatsapp_number, and physical_address_es. Notifications category contains email_notifications_enabled, whatsapp_notifications_enabled, and admin_alert_email.

The PATCH endpoint for updating settings accepts a partial settings object where any subset of categories and their keys can be updated. Only the provided keys are updated in the database, and keys that are not provided remain unchanged. Setting keys that do not exist in the known settings schema return 422 unprocessable entity response to prevent accidental creation of unknown settings through typos in key names.

Boolean settings accept only the JSON literals true or false. Numeric settings validate against minimum and maximum bounds defined in the settings schema so invalid values like negative donation minimums are rejected. String settings validate against maximum length constraints. All validation failures return 422 unprocessable entity with a message describing the constraint violation.

All admin settings endpoints require the require_admin_role dependency from EPIC-10, meaning only users with admin role can access these endpoints.

All setting changes are recorded in an audit log table with these fields: admin_user_id identifying who made the change, setting_key naming the changed setting, old_value containing the previous value before the change, new_value containing the value after the change, and timestamp showing when the change occurred.

## Implementation Approach

The settings schema is defined as a registry within the configuration service mentioned in T02. This registry maps setting keys to their type, validation rules including bounds and length limits, and default values. The GET endpoint queries all rows from the system_settings table, assembles them into the categorized response structure using the schema as a guide, and casts values from their text storage representation to their semantic Python types for inclusion in the JSON response.

The PATCH endpoint iterates through the provided key-value pairs in the request body, validates each against the schema constraints, reads the current value from the database for audit logging purposes, updates the database row with the new value, and commits the transaction. The response to PATCH returns the full settings object after applying all updates, allowing the client to immediately see the post-update state without making a separate GET request.

The categorization logic is implemented in a helper function that accepts a flat dictionary of key-value pairs and the schema registry, then restructures the data into the nested category structure for response serialization. This keeps the database schema flat and simple while presenting a well-organized interface to the admin user.

## Success Criteria

The GET endpoint returns all settings with correct types — numeric settings return as integers not strings, boolean settings as true or false not as strings. The PATCH endpoint with a single key updates only that key while leaving others unchanged. Sending an unknown key in the PATCH request returns 422 unprocessable entity. Sending an out-of-bounds numeric value like a negative minimum donation amount returns 422 with the constraint violation described. All successful changes appear in the audit log table.

Tests must verify GET response has correct structure with expected categories. Tests must verify PATCH with partial settings updates only the specified keys. Tests must verify validation of bounds for numeric fields. Tests must verify validation of maximum length for string fields. Tests must verify unknown keys are rejected.
