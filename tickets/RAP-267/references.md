# RAP-267 References

## Files
- `/src/services/donor_impact.py` - Service logic for impact calculations
- `/src/api/donor_impact.py` - API endpoints
- `/tests/unit/test_donor_impact.py` - Unit tests (need integration tests)
- `/src/app.py` - Router registration

## Story
- `/planning/epics/EPIC-54-impact-report-generator/stories/S3-donor-specific-impact-summaries/STORY.md`

## Related PRs
- PR #390: RAP-265 (Impact report data aggregation)
- PR #391: RAP-266 (Impact report PDF template)

## Endpoints
- GET `/api/portal/impact` - Full donor impact summary
- GET `/api/portal/impact/statements` - Impact statements only
