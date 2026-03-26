# T02: Add Linting Checks

## Overview

The linting checks job is a dedicated GitHub Actions job that validates code quality through automated analysis tools. This job runs before the expensive test job and provides fast feedback on common code style and quality issues. By catching lint errors early, developers receive immediate notification of issues without waiting for the full test suite to execute.

## Code Quality Checks Job Structure

The linting checks are organized in a separate GitHub Actions job that executes on every push and pull request, just like the test pipeline. This job runs in parallel with other quality checks but must complete successfully before code can be merged to main. The job follows a fail-fast pattern where if the first check fails, subsequent checks do not run, giving developers the most important error information first.

## Ruff for Linting

Ruff is a fast Python linter that consolidates functionality from many traditional tools into a single, highly optimized binary. The linting job runs ruff check against the entire src directory and fails immediately if any lint error or warning is discovered. The workflow runs ruff in check mode only, never in auto-fix mode, which means developers must fix lint violations locally before pushing code.

The ruff configuration is defined in pyproject.toml or a separate ruff.toml file. The configuration specifies which rule sets are enabled, at minimum including pyflakes for detecting logical errors, pycodestyle for style compliance, and isort rules for import ordering. By consolidating these checks, ruff provides more consistent results than running multiple separate tools, and it executes much faster than traditional tools like flake8.

The ruff linter catches issues such as unused variables, undefined names, syntax errors that Python would only discover at runtime, missing parentheses around comparisons, and many other common mistakes. These are among the fastest checks to perform, which is why ruff runs first in the quality pipeline.

## Mypy for Type Checking

Mypy performs static type checking on Python code by analyzing type annotations and inferring types. The type-check job runs mypy in strict mode against the src directory, reading its configuration from pyproject.toml. Any type error detected by mypy causes the job to fail.

Type checking is faster than running tests but slower than linting because mypy must analyze the entire call graph and track types through the codebase. By running mypy after linting, the workflow ensures that lint errors are fixed before spending time on more complex type checking.

In strict mode, mypy enforces that every function has proper type annotations, that all variables are typed, and that no implicit any types are allowed. This strict approach prevents subtle type-related bugs and makes the codebase more maintainable because types serve as inline documentation.

The mypy cache is stored between workflow runs to speed up incremental type checking. When developers make small changes to a few files, mypy can reuse analysis results from unchanged files instead of re-analyzing the entire codebase.

## Black for Formatting

Black is an opinionated code formatter that enforces a consistent code style automatically. The linting job runs black with the check flag, which verifies that all Python files conform to black's style without actually modifying the files. If any file would be reformatted by black, the job fails.

The workflow never uses black's auto-fix mode in CI. Instead, developers are expected to run black locally before pushing code. This approach makes developers aware of formatting issues and ensures they consciously apply consistent formatting rather than having it silently applied by CI.

Black's opinionated approach means developers do not debate style issues; the style is predetermined by black's rules. This consistency reduces context switching and makes code reviews focus on logic and design rather than formatting preferences.

## Isort for Import Ordering

Isort automatically orders and formats import statements according to a standard convention: standard library imports first, then third-party imports, then local imports. The linting job runs isort with the check and diff flags, which reports which files have imports in the wrong order without modifying them.

The isort configuration in pyproject.toml must be compatible with black's import formatting. If isort and black disagree on import formatting, developers cannot satisfy both tools. The configuration carefully balances the two to ensure they work together without conflicts.

Import ordering is a minor style issue but becomes important in larger projects where consistent import organization makes it easier to scan code and identify which external dependencies are used.

## Fail-Fast Behavior

The linting job uses fail-fast to maximize feedback speed. If ruff finds any errors, mypy and black are not executed. This means developers get feedback on the most fundamental errors first without waiting for the slower type checking and formatting checks to run.

This fail-fast approach applies at the command level as well. If ruff returns a non-zero exit code, the workflow step fails immediately and does not proceed to subsequent checks.

## Reviewdog Integration

The workflow integrates reviewdog, a tool that parses linter output and posts inline comments directly on the pull request diff. When ruff detects an unused variable on line 42, reviewdog parses that output and posts a comment on line 42 of the PR, making it immediately obvious to the developer where the issue is.

This integration eliminates the need for developers to dig through CI logs to find error locations. Reviewdog displays errors where they occur in the code, making the feedback actionable and easy to understand.

## Python Environment Caching

The linting job uses the same dependency caching strategy as the test pipeline. The actions/cache action caches the pip-installed Python environment based on the hash of requirements.txt. If dependencies have not changed, the cached environment is restored, and the linting tools run immediately without waiting for pip to install dependencies.

The mypy cache is also cached between runs so that incremental type checking builds on previous analysis and runs faster for small changes.

## Continuous Validation

The linting job runs on every push to any branch and on every pull request update. This ensures that code quality never regresses. If a developer pushes code with lint errors, the workflow fails immediately and blocks the PR from being merged until the errors are fixed.

This continuous validation creates a culture of quality where developers expect automated checks to catch common issues before code review. Reviewers can then focus on architectural and logical issues rather than style problems that machines can catch.

## Summary: Quality Gates

The linting checks represent the first quality gate in the pipeline. Code must pass ruff, mypy, black, and isort checks before proceeding to the type-check and test jobs. By failing fast on common errors, the linting job saves time and provides immediate feedback to developers on issues that are easy to fix locally.
