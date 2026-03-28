# RAP-538 References

## Key Files
- `src/services/community_feed_service.py` — feed aggregation service
- `src/api/community_feed.py` — GET /api/community/feed router
- `src/app.py` — router registration (line ~435)
- `frontend/src/app/community/page.tsx` — public community feed page
- `tests/unit/test_community_feed_service.py` — 27 unit tests
- `tests/integration/test_community_feed.py` — 8 integration tests

## Data Sources
- `src/db/models/animal.py` — AnimalStatus enum
- `src/db/models/campaign.py` — CampaignStatus enum
- `src/db/models/community_need.py` — NeedStatus enum
- `src/db/models/success_story.py` — SuccessStory model

## Related
- EPIC-80-rescuer-network/stories/S6-community-feed/STORY.md
