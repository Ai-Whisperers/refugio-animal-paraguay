---
name: domain-spec
description: Document domain objects, enumerations, business rules, and invariants from the codebase
allowed-tools: Bash, Read, Glob, Grep, Write
---

Extract and document domain knowledge from the codebase: models, enumerations, business rules, and invariants. Output is a reference document, not code.

## Steps

**Step 1** — Discover domain models:
```bash
# Python — find model/entity files
find . -name "models.py" -o -name "entities.py" -o -name "domain.py" 2>/dev/null | head -10
find . -path "*/models/*.py" -o -path "*/entities/*.py" 2>/dev/null | head -10

# TypeScript — find interfaces and enums
find . -name "*.ts" -path "*/types/*" -o -name "*.ts" -path "*/models/*" 2>/dev/null | head -10
grep -rn "^export interface\|^export enum\|^export type" src/ 2>/dev/null | head -20
```

**Step 2** — Read identified model files:
- Read each file found in Step 1
- Extract: class/interface names, fields, enumerations, validation rules, relationships

**Step 3** — Find business rules in services/use cases:
```bash
grep -rn "raise ValueError\|raise ValidationError\|if.*raise\|assert " src/ 2>/dev/null | head -30
grep -rn "def validate\|def check\|def ensure\|def verify" src/ 2>/dev/null | head -20
```

**Step 4** — Generate domain specification:

```markdown
# Domain Specification — [Project Name]
_Generated from source code on [date]_

## Core Entities

### [EntityName]
**Purpose**: [what this entity represents in the domain]

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| id | UUID | Yes | Primary identifier |
| [field] | [type] | [Yes/No] | [meaning] |

**Relationships**:
- Has many: [EntityName]
- Belongs to: [EntityName]
- References: [EntityName]

**Invariants** (always true):
- [Invariant 1: business rule that must hold]
- [Invariant 2]

---

## Enumerations

### [EnumName]
| Value | Meaning | Transitions allowed to |
|-------|---------|----------------------|
| `PENDING` | [what this state means] | APPROVED, REJECTED |
| `APPROVED` | [what this state means] | COMPLETED, CANCELLED |

---

## Business Rules

### [Rule Name]
**Context**: [when does this rule apply]
**Rule**: [the rule in plain language]
**Enforced in**: `[file:line]`

```python
# The implementation
[relevant code snippet]
```

---

## Validation Rules

| Field | Validation | Error if violated |
|-------|-----------|-------------------|
| email | RFC 5322 format | "Invalid email format" |
| [field] | [rule] | [error message] |

---

## Glossary

| Term | Definition |
|------|-----------|
| [Domain term] | [What it means in this system] |
```

**Step 5** — Write output:
- If argument provided: write to that path
- Otherwise: write to `docs/domain-spec.md`

## Rules

- Extract from code — do not invent business rules
- If a rule is unclear from code, note "[inferred from implementation]"
- Include file references for every business rule
- State enumerations exhaustively — list every value
- Glossary should capture domain-specific language, not general terms
