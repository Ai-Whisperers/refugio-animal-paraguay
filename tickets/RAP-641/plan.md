# RAP-641 Plan

## Objective
Extend volunteer profiles with editable skills/availability management and a frontend profile page.

## Description
S1 (RAP-640) built the volunteer registration form and basic profile model. S2 adds:
1. Extended profile fields: bio and languages_spoken
2. New API endpoint allowing approved volunteers to update skills and availability
3. A frontend volunteer profile page at /volunteer/profile

## Acceptance Criteria
- [ ] Profile model extended with: bio (text, optional), languages_spoken (JSON list, optional)
- [ ] New migration 072 for new columns
- [ ] PUT /api/volunteers/profile endpoint for approved volunteers to update skills/availability/bio
- [ ] GET /api/volunteers/profile/options endpoint returning available skill + availability options
- [ ] Frontend page /volunteer/profile showing profile data, skills chips, availability badges
- [ ] Profile page allows editing skills/availability for all non-rejected volunteers
- [ ] Unit tests for new endpoint (80%+ coverage)
- [ ] Integration tests: update skills as approved volunteer, get options

## Complexity Assessment
**Track**: Fullstack — Backend + Frontend

### Simple Fix Criteria
- [ ] Single, clear root cause identified — N/A, new feature
- [x] Solution affects ≤3 files — Backend: volunteer.py + volunteer_profile.py + migration. Frontend: 1 page.
- [x] Change impact ≤10 lines of actual code — No, extends model and adds endpoint
- [x] Low risk of side effects

**Assessment result**: Complex — extends model, new migration, new endpoint, new frontend page

## Approach
1. Add bio + languages_spoken to VolunteerProfile model
2. Create migration 072
3. Add PUT /api/volunteers/profile endpoint (allows approved volunteers to update skills/availability/bio)
4. Add GET /api/volunteers/profile/options endpoint
5. Update VolunteerProfileResponse to include new fields
6. Create /volunteer/profile Next.js page
7. Write tests

## Dependencies
- Depends on: RAP-640 (DONE, volunteer_profiles table exists)

## Risks
- Migration 071 already exists — need to be careful with numbering (072)
