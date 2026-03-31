# RAP-215 References

## Key Files
- `src/db/models/email_list.py` — EmailList and EmailListMember models
- `src/db/alembic/versions/083_create_email_lists_tables.py` — migration
- `src/api/email_lists.py` — API router
- `src/services/email_list_service.py` — segmentation service
- `tests/unit/test_email_list_service.py` — unit tests
- `tests/integration/test_email_lists.py` — integration tests

## Pattern References
- `src/db/models/campaign.py` — similar model structure
- `src/api/admin_campaigns.py` — similar router pattern
