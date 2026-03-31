# RAP-227 References

## Key Files
- `frontend/src/app/portal/profile/page.tsx` — portal profile page with placeholder deletion button
- `src/api/profile.py` — POST /portal/gdpr/delete, POST /portal/gdpr/delete/confirm
- `src/services/profile_service.py` — request_account_deletion, confirm_account_deletion
- `src/schemas/profile.py` — AccountDeleteRequest, AccountDeleteResponse, AccountDeleteConfirm, AccountDeleteConfirmResponse
- `frontend/src/lib/api.ts` — API client pattern to follow
- `frontend/src/app/donate/confirmation/page.tsx` — example confirmation page pattern
