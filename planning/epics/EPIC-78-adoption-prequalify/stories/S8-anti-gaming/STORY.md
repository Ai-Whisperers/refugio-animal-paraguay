---
story: S8
epic: EPIC-78
ticket: RAP-524
title: "Anti-gaming protection"
status: ready
points: 2
priority: P2
track: Backend
sprint: 11
version: V1
created: 2026-03-27T20:00:00
---

# S8: Anti-gaming protection

## Story
As a **system**, I want **to prevent gaming of pre-qualification** so that **unqualified adopters can't repeatedly attempt to game the system**.

## Description
Implement rate limiting and fingerprinting to detect and prevent attempts to bypass pre-qualification checks.

## Acceptance Criteria
- [ ] Rate limiting per animal: max 3 pre-qualification attempts per email per animal per day
- [ ] Rate limiting enforcement: return HTTP 429 if limit exceeded, with message "Too many qualification attempts for this animal today. Please try again tomorrow."
- [ ] Rate limiting key: Redis key pattern "prequal:{email}:{animal_id}:{date_YYYY-MM-DD}", increment on each attempt, set TTL to 24h
- [ ] Fingerprinting: track attempts by IP + User-Agent combination (browser fingerprint), calculate hash: sha256(ip + user_agent)
- [ ] Suspicious pattern detection: if same email submits same answers multiple times within 1 hour, flag as suspicious
- [ ] Admin notification: log suspicious attempts to admin dashboard at /admin/suspicious-activities, show: email, animal_id, attempt_count, timestamps, IP addresses
- [ ] Automatic blocking: if same email makes 10+ attempts on same animal within 24h, automatically block further attempts and email admin
- [ ] Reset on application: if user actually applies after pre-qual, reset attempt counter (legitimate user)
- [ ] Whitelist: admin can whitelist emails/IPs if needed for legitimate reasons
- [ ] Logging: log all pre-qual attempts with email, IP, animal_id, timestamp, answers_hash (not full answers)
- [ ] Response headers: include X-RateLimit-Remaining header showing remaining attempts

## Definition of Done
- [ ] Code complete, peer reviewed
- [ ] Unit tests written and passing (80%+ coverage) - test rate limiting, pattern detection
- [ ] Integration test: rate limiting enforced after 3 attempts
- [ ] Integration test: different users can attempt independently
- [ ] Integration test: suspicious pattern flagged
- [ ] Integration test: automatic block after 10 attempts
- [ ] Integration test: whitelist bypasses rate limiting
- [ ] Manual testing: verify rate limiting works as expected
- [ ] Deployed to staging and verified

## Technical Notes
- Rate limiting: use Redis with keys "prequal:{email}:{animal_id}:{date}"
- Increment: use INCR command with EX 86400 (24h TTL)
- Fingerprinting: hash IP + User-Agent, store in suspicious_attempts table
- Suspicious detection: query attempts for (email, animal_id) within last 1h, flag if count > 1
- Automatic block: create admin alert and set flag in suspicious_patterns table
- Whitelist: table whitelist_entries with email/ip, check before rate limiting
- Logging: log to pre_qualification_attempts table with email, ip, animal_id, fingerprint, timestamp
- Answer hashing: hash answers to detect identical submissions without storing answers
- Admin dashboard: query suspicious_patterns and suspicious_attempts tables
- Email to admin: when automatic block triggered, send alert

## Story Points: 2
