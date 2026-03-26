---
name: changelog
description: Generate or update CHANGELOG.md from git history since last release
allowed-tools: Bash, Read, Write, Edit
---

Generate a structured CHANGELOG entry from git commits since the last tag.

## Steps

**Step 1** — Find the last release tag and commits since then:
```bash
git describe --tags --abbrev=0  # last tag
git log [last-tag]..HEAD --oneline --no-merges
```

**Step 2** — Categorize commits into changelog sections:

| Section | Commit prefix / keywords |
|---------|--------------------------|
| `### Added` | `feat:`, `add`, `new`, `implement` |
| `### Changed` | `refactor:`, `update`, `improve`, `change` |
| `### Fixed` | `fix:`, `bug`, `resolve`, `patch` |
| `### Security` | `security:`, `auth`, `GDPR`, `CVE`, `vuln` |
| `### Deprecated` | `deprecate:`, `remove:` |
| `### Removed` | `remove:`, `delete:`, `drop:` |

**Step 3** — Format as Keep a Changelog 1.0.0 format:

```markdown
## [Unreleased]

## [X.Y.Z] — YYYY-MM-DD

### Added
- Brief description (TICKET-ID)

### Fixed
- Brief description (TICKET-ID)
```

**Step 4** — Update `CHANGELOG.md`:
- If CHANGELOG.md doesn't exist, create it with standard header
- If it exists, insert new section after `## [Unreleased]`
- Keep `## [Unreleased]` section at top for future additions

## Rules

- Every entry links back to a ticket ID if available (from commit messages)
- Skip merge commits and automated commits (e.g., from pre-commit hooks)
- Write entries in past tense: "Added", "Fixed", "Updated" (not "Add", "Fix")
- One line per change — link ticket ID in parentheses
- If no CHANGELOG.md exists, create it

## Output Format

```markdown
# Changelog

All notable changes to this project will be documented here.
Format: [Keep a Changelog](https://keepachangelog.com/en/1.0.0/)
Versioning: [Semantic Versioning](https://semver.org/spec/v2.0.0.html)

## [Unreleased]

## [1.2.0] — 2026-03-25

### Added
- Adoption application status tracking for adopters (RAP-042)
- Email notification on application status change (RAP-043)

### Fixed
- Email validation for international EU donor addresses (RAP-044)

## [1.1.0] — 2026-02-10
...
```
