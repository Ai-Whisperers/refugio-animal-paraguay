---
name: generate-missing-tests
description: Find uncovered code and generate missing tests to meet coverage threshold
allowed-tools: Bash, Read, Write, Glob, Grep
---

@.claude/rules/quality-standards.md

Find code lacking test coverage and generate tests for the most critical uncovered paths.

## Steps

**Step 1** — Run coverage analysis:
```bash
# Python
python3 -m pytest --cov=src --cov-report=term-missing --no-header -q 2>/dev/null || \
python3 -m pytest --cov=. --cov-report=term-missing --no-header -q 2>/dev/null

# Node.js
npx jest --coverage --coverageReporters=text 2>/dev/null || \
npm test -- --coverage 2>/dev/null
```

**Step 2** — Identify uncovered lines:
- Parse coverage output for files below 80% threshold
- Note specific uncovered line ranges
- Prioritize: business logic > utility functions > config

**Step 3** — Read uncovered code sections:
- Read each flagged file
- Identify what the uncovered code does
- Note: function signatures, expected inputs/outputs, error conditions

**Step 4** — Generate tests:

For each uncovered function/path, generate a test following the AAA pattern:

```python
# Python — pytest style
def test_[function_name]_[scenario]() -> None:
    """[One line: what this tests]"""
    # Arrange
    [setup code]

    # Act
    result = [call the code]

    # Assert
    assert result == [expected]


def test_[function_name]_[error_scenario]() -> None:
    """[One line: what error condition this tests]"""
    # Arrange
    [setup — bad input or broken dependency]

    # Act + Assert
    with pytest.raises(SomeException, match="expected message"):
        [call the code]
```

```typescript
// TypeScript — vitest/jest style
describe('[ClassName/module]', () => {
  it('[function name] [scenario]', () => {
    // Arrange
    const input = ...;

    // Act
    const result = functionUnderTest(input);

    // Assert
    expect(result).toEqual(expected);
  });

  it('[function name] throws on [error scenario]', () => {
    expect(() => functionUnderTest(badInput)).toThrow('expected message');
  });
});
```

**Step 5** — Verify tests pass:
```bash
# Run new tests only
python3 -m pytest [new test file] -v
# or
npx jest [new test file] --verbose
```

**Step 6** — Re-run coverage:
```bash
# Confirm coverage improved
python3 -m pytest --cov=src --cov-report=term-missing -q
```

## Rules

- Prioritize uncovered: error paths, validation, edge cases over happy paths
- One test per behavior — not one test per function
- Never write tests that just call code without asserting anything
- Tests must be independent — no shared mutable state between tests
- If code is untestable as written (too many dependencies), note it — don't write a test that requires 5 mocks
- If a test requires a database or external service: mark it as integration test
- Match the existing test file naming convention in the project
