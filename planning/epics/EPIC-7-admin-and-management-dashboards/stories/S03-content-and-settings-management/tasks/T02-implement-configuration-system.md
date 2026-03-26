---
task_id: T02
task_title: Implement Configuration System
task_status: pending
story_id: S03
epic_id: EPIC-7
created_date: 2026-03-25
estimated_effort: 6
dependencies:
  - system_settings database table
  - T01 settings interface (depends on this service)
  - Application startup hooks
---

# T02: Implement Configuration System

## Overview

The configuration system is a service layer that sits between the database and the rest of the application, providing type-safe access to system settings. It implements a two-tier lookup: first checking an in-memory cache populated at startup from the database, then falling back to environment variables for infrastructure-level settings that should not be in the database such as JWT_SECRET, database URL, and Stripe API key. The service provides named accessor methods for each setting category so application code reads settings through a stable interface rather than directly querying the database or reading environment variables ad-hoc throughout the codebase.

## Why This Task Matters

Without a unified configuration service, application code reads settings from different sources in inconsistent ways: some modules read from environment variables using os.environ calls, others query the database directly, others use hardcoded defaults scattered through the code. This fragmentation makes it impossible to test with different configurations, understand what settings exist and where they come from, or change how settings are sourced without editing multiple files. The configuration service creates a single point of truth for all runtime settings and enables the admin settings interface from T01 to update values that immediately affect application behavior.

## Technical Requirements

The configuration system is implemented as a singleton class instantiated once at application startup by the FastAPI application initialization code. At startup, it loads all rows from the system_settings table into an in-memory dictionary keyed by the setting key column. The database read is performed once during initialization; subsequent reads come from the in-memory cache during request handling for performance.

Infrastructure secrets — JWT_SECRET, DATABASE_URL, STRIPE_SECRET_KEY, and SMTP_PASSWORD — are loaded from environment variables at startup and never stored in the database. These are sensitive values that should not be persisted or recoverable from application database backups. The service reads these from environment variables and makes them available through named accessor methods.

Application settings such as minimum donation amounts, shelter contact information, feature flags, and notification preferences live in the system_settings table and are accessible through typed accessor methods. Named accessor methods are provided for each setting: get_minimum_donation_eur_cents returns an integer, get_shelter_name with a language parameter returns a string, get_whatsapp_number returns a string, get_email_notifications_enabled returns a boolean, and so on.

The service exposes a refresh method that re-queries the database and updates the in-memory cache. The admin settings PATCH endpoint from T01 calls this refresh method after committing updates so subsequent requests see new values immediately. Cache invalidation is synchronous: the refresh call completes before the PATCH endpoint returns to the client.

If a setting is not found in the database, the accessor returns a hard-coded default value defined as a class constant in the service. This provides sensible fallback behavior if a setting has not been configured. The service raises ConfigurationError, a custom exception, if a required infrastructure environment variable is missing at startup with a descriptive message naming the missing variable.

## Implementation Approach

The service is implemented using either Python dataclasses or a simple class with type-annotated attributes to represent the in-memory configuration state. The load_from_db method queries the system_settings table and populates the internal state dictionary. Type casting from the text storage format in the database to Python types occurs at load time so accessor methods work with native Python types.

Accessor methods read from the in-memory state dictionary, providing fast access without database round-trips on every request. Accessor methods handle both settings that exist in the dictionary and provide defaults for settings that are not configured. The refresh method calls load_from_db again, replacing the current in-memory state atomically in a single assignment operation.

The service is registered as a FastAPI application state attribute so route handlers and dependencies can access it through the request object using FastAPI's app.state mechanism. Alternatively, the service can be instantiated as a module-level singleton in a configuration module and imported by route handlers, depending on the existing FastAPI application structure.

Environment variable loading uses getenv with a second argument specifying no default, then checks if the result is None to detect missing required variables. This approach separates infrastructure secrets from application settings clearly.

## Success Criteria

Application startup fails with a clear ConfigurationError if the JWT_SECRET environment variable is not set, clearly indicating which variable is missing. Updating a setting through the admin PATCH endpoint from T01 and immediately calling a GET endpoint must return the updated value with no stale cache. All accessor methods return values of the correct Python type — integers for numeric settings, booleans for flags, strings for text values.

Tests can construct the service with a mock database session to test behavior with specific setting values without requiring a real database or environment variables. Tests verify that changing a setting and calling refresh updates the returned value. Tests verify that missing required environment variables cause startup errors. Tests verify that missing optional database settings return configured default values.
