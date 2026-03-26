# RAP-021 References

## Story
- planning/epics/EPIC-10-authentication-and-user-accounts/stories/S02-password-reset-and-email-verification/STORY.md
- planning/epics/EPIC-10-authentication-and-user-accounts/stories/S02-password-reset-and-email-verification/tasks/T02-implement-password-reset.md

## Key Files
- src/auth/utils.py — password hashing, JWT utils
- src/auth/dependencies.py — auth dependencies
- src/api/auth.py — auth router
- src/db/models/user.py — User model
- src/schemas/user.py — user schemas
- src/config.py — settings
- src/app.py — app factory
