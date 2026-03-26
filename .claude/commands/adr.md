# Command: /adr

Create an Architecture Decision Record for a significant technical decision.

## Usage

```
/adr "Use FastAPI over Django REST Framework for the backend API"
/adr "Choose PostgreSQL with JSONB for flexible animal metadata storage"
/adr "Integrate Stripe for EU donor payments with SEPA support"
```

## What This Command Does

ADRs capture *why* architectural decisions were made, not just what was decided. They are permanent records — once accepted, they are never deleted, only superseded.

## Read First

- `.claude/exemplars/adr/adr-good.md` — reference example of a complete ADR

## Steps

### 1. Gather context

Ask or infer:
- What decision is being made?
- What alternatives were considered?
- What constraints apply (EU regulations, budget, team skills, timeline)?
- What is the business/technical risk of each option?

### 2. Determine ADR number

```bash
ls docs/adr/ | grep -E '^[0-9]+' | sort -n | tail -1
```

Next ADR = highest number + 1. If directory is empty, start at `0001`.

### 3. Create the ADR file

File path: `docs/adr/NNNN-kebab-case-title.md`

Use this structure:

```markdown
# ADR-NNNN: [Decision Title]

**Date**: YYYY-MM-DD
**Status**: Proposed | Accepted | Superseded by ADR-MMMM | Deprecated

## Context

What is the problem or situation that requires a decision?
What forces are at play (technical, business, regulatory, team)?

## Decision

State the decision clearly in one sentence.
"We will use X for Y because Z."

## Alternatives Considered

### Option A: [Name]
- Pro: ...
- Con: ...

### Option B: [Name]
- Pro: ...
- Con: ...

### Option C: [Name] ← chosen
- Pro: ...
- Con: ...

## Consequences

**Positive outcomes:**
- ...

**Negative outcomes / trade-offs:**
- ...

**Risks and mitigations:**
- Risk: ... → Mitigation: ...

## Compliance Notes (if applicable)
EU GDPR, Paraguayan law, or financial regulation implications of this decision.

## Related ADRs
- ADR-NNNN: [title] (precondition / successor)
```

### 4. Update ADR index

Append to `docs/adr/README.md`:

```markdown
| ADR-NNNN | [Title] | Accepted | YYYY-MM-DD |
```

### 5. Reference in CLAUDE.md tech stack

If the ADR resolves a TBD in the Project Tech Stack table, update it.

## When to Write an ADR

Write an ADR when:
- Choosing a framework, database, or hosting platform
- Making an API design decision that affects multiple services
- Deciding on an authentication/authorization approach
- Choosing a payment processor or donation platform
- Any decision that would be hard or costly to reverse
- Any decision driven by EU/Paraguayan regulatory requirements

Do NOT write ADRs for:
- Implementation details (how to structure a function)
- Reversible decisions (library version, naming)
- Obvious choices with no real alternatives

## ADR Lifecycle

```
Proposed → Accepted → [Deprecated | Superseded]
```

- **Proposed**: Under discussion
- **Accepted**: Decision made, implementation proceeds
- **Superseded**: Replaced by a newer ADR (reference it)
- **Deprecated**: No longer relevant (explain why)

Never delete an ADR. The history of decisions is as important as the current state.
