# Architecture Decision Records

This directory contains Architecture Decision Records (ADRs) for Refugio Animal Paraguay.

ADRs capture *why* decisions were made, not just what was decided. They are permanent records — once accepted, they are never deleted, only superseded.

## How to Create an ADR

```
/adr "Decision title"
```

See `.claude/commands/adr.md` for the full workflow and `.claude/exemplars/adr/adr-good.md` for a calibration example.

## Record Index

| ADR | Title | Status | Date |
|-----|-------|--------|------|
| ADR-001 | Core Tech Stack Selection | Accepted | 2026-03-25 |

## ADR Lifecycle

```
Proposed → Accepted → [Deprecated | Superseded by ADR-NNNN]
```

- **Proposed**: Under discussion, not yet implemented
- **Accepted**: Decision made, implementation may proceed
- **Superseded**: Replaced by a newer ADR (reference it)
- **Deprecated**: No longer relevant (explain why)

Never delete an ADR. The history of decisions is as valuable as the current state.

## Pending Decisions (Tech Stack TBDs)

The following tech stack choices are currently TBD in `CLAUDE.md` and should each get an ADR when decided:

- [ ] Frontend framework
- [ ] Hosting platform (Paraguay + EU latency considerations)
- [ ] Payment processor (local PYG option TBD — Stripe confirmed for EU)
- [ ] Email service provider
