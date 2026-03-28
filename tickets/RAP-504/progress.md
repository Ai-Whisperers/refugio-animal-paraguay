# RAP-504 Progress Log

---
## [2026-03-27 10:00] Implementation started
**Action**: Created feature branch, began implementing Google OAuth flow
**Findings**: Existing auth system uses JWT with session tracking (JTI), User model at src/db/models/user.py
**Decision**: Follow existing patterns — use create_session + create_access_token for OAuth JWT generation
**Next**: Database migration

---
## [2026-03-27 10:15] Database migration created
**Action**: Created migration 038 adding oauth_provider, oauth_id, profile_picture_url columns
**Findings**: hashed_password was NOT NULL — needs to be nullable for OAuth-only users
**Decision**: Make hashed_password nullable in same migration; add unique constraint on (oauth_provider, oauth_id)
**Next**: Config and service layer

---
## [2026-03-27 10:30] Service and schemas created
**Action**: Created google_oauth_service.py and oauth.py schemas
**Findings**: httpx AsyncClient is already a project dependency
**Decision**: Use httpx for Google API calls; create OAuthUserInfo model for internal representation
**Next**: API endpoints

---
## [2026-03-27 10:45] API router and auth updates
**Action**: Created google_oauth.py with 4 endpoints; updated auth.py to reject OAuth-only users on password login
**Findings**: Account linking requires two-step flow when email exists but no OAuth link
**Decision**: Use pending link store with state parameter to track linking flow
**Next**: Frontend pages

---
## [2026-03-27 11:00] Frontend implementation
**Action**: Created login page and Google callback page
**Findings**: Existing frontend uses sessionStorage for JWT tokens
**Decision**: Spanish language UI; Google SVG icon with official brand colors
**Next**: Tests

---
## [2026-03-27 11:15] Tests written and quality gates
**Action**: Created 21 unit tests across 2 test files
**Findings**: AsyncMock makes .json() return coroutine — httpx Response.json() is sync
**Decision**: Use MagicMock for response objects in tests where .json() is called
**Next**: Commit, PR, queue update

---
## [2026-03-27 11:30] Quality gates passed
**Action**: All quality gates verified
**Findings**: 1325 unit tests pass, 0 failures; ruff clean; black clean; pyright clean
**Decision**: Ready for commit and PR
**Next**: Git operations
