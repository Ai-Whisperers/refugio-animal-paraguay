# T01: Setup Test Pipeline

## Overview

The test pipeline is a GitHub Actions workflow that automatically runs the full test suite whenever code is pushed to any branch or when a pull request is opened or updated. This workflow ensures that no code can be merged into main without passing all tests, establishing a baseline of quality for every commit that enters the repository.

## Workflow Trigger Conditions

The test pipeline triggers in two scenarios. First, it runs whenever a push event occurs on any branch in the repository, regardless of which branch receives the commit. Second, it runs whenever a pull request is opened or when additional commits are pushed to an open pull request. This dual trigger strategy means developers get immediate feedback on their code quality during development, and reviewers can see test results directly in the pull request interface before deciding whether to approve and merge.

## Job Execution Order and Dependencies

The workflow defines three sequential jobs that must complete in order: lint, type-check, and test. Each job declares an explicit dependency on the previous job, creating a strict fail-fast pipeline where the entire workflow stops if any job fails. This design prioritizes fast feedback on common errors.

The lint job executes first. Linting catches formatting inconsistencies, unused imports, and common style violations quickly. By failing fast on lint errors, developers get immediate feedback on basic issues before the more computationally intensive type checking and testing jobs run.

The type-check job runs only after lint passes. Type checking validates that all Python code respects type annotations and that no type errors exist. Type checking is faster than running tests but slower than linting, so it runs second.

The test job runs last and only if both previous jobs pass. Testing is the slowest phase because it requires spinning up a PostgreSQL service container, loading test fixtures, and executing the full test suite. By running it last, the workflow minimizes the time spent on expensive test execution when lint or type errors would have failed the build anyway.

## Python Version and Environment

The workflow specifies Python 3.12 explicitly in the runs-on configuration and the setup-python action. The project targets a single Python version, so no matrix strategy across multiple versions is needed. Explicitly pinning version 3.12 prevents drift where developers might use different Python versions locally than in CI, which can lead to subtle version-specific bugs.

The workflow sets up a fresh Python environment on every run, ensuring a clean slate without any accumulated state from previous runs. This reproducibility is critical for detecting intermittent failures.

## Dependency Caching

The workflow uses the actions/cache action to cache pip dependencies across runs. The cache key is derived from the hash of requirements.txt, which means if requirements.txt hasn't changed, subsequent workflow runs skip the pip install step entirely and reuse the cached virtual environment.

This caching mechanism dramatically reduces CI time. On the first run after a dependency change, pip installs all dependencies from PyPI, which takes several minutes depending on network latency and package size. On subsequent runs without dependency changes, the cached environment is restored in seconds. For projects with many dependencies or slow network connections, this optimization reduces feedback time significantly and reduces load on PyPI servers.

## PostgreSQL Service Container

The test suite includes integration tests that require a real PostgreSQL database instance. Rather than expecting developers to manually start a PostgreSQL container or relying on a shared test database, the workflow declares a PostgreSQL 16 service container within GitHub Actions.

GitHub Actions supports service containers that run alongside the main job runner in a dedicated network. The workflow configures the PostgreSQL 16 image with a test database name, test username, and test password. These credentials are passed to the main job as environment variables so that tests can read them and connect to the service.

The database URL is constructed as an environment variable using the standard format: the service container hostname (which GitHub Actions sets to the service name), the port (PostgreSQL's default 5432), the database name, username, and password. The test suite reads this DATABASE_URL and creates a connection pool to the service container.

The service container starts before the test job begins and remains running for the duration of the job. If tests modify the database state (insert test data, create tables, etc.), those changes persist for the duration of the job but are cleaned up when the service container stops at the end of the job.

## Test Execution and Coverage

The test job runs pytest with the full test suite specified. The pytest configuration includes coverage reporting enabled. Coverage tracking measures what percentage of the application code is executed by the test suite, giving developers visibility into whether tests are exercising all code paths or only a subset.

The coverage report is generated in multiple formats. The terminal output shows a summary percentage. An XML report is generated in Cobertura format, which GitHub Actions and other tools can parse and visualize. An HTML coverage report can be generated for detailed line-by-line coverage inspection.

## Coverage Threshold Enforcement

The pytest configuration includes a coverage threshold setting that causes the test job to fail if the overall test coverage falls below 80 percent. This threshold is enforced automatically in CI, which means a pull request that deletes tested code and reduces overall coverage will have a failing test job, and reviewers will see that coverage has decreased.

The 80 percent threshold balances comprehensiveness with practicality. It ensures the majority of code is tested without requiring 100 percent coverage, which would be unachievable and unnecessary (not all code paths, such as error handling in rare scenarios, must be tested). Setting this threshold in CI prevents coverage from degrading over time as the codebase grows.

## Artifact Upload and Reporting

After tests run, the workflow uploads coverage reports as artifacts to GitHub Actions. This allows any developer or reviewer to download the coverage report from the Actions page and inspect which files have low coverage or which specific lines are not covered by tests.

The workflow also uploads a JUnit XML report from pytest. GitHub Actions can parse this report and display test results directly in the pull request interface, showing a summary of passed and failed tests without requiring reviewers to click through to the full CI log.

## Environment Variables and Secrets

All environment variables needed by the test suite are declared in the workflow. These include the DATABASE_URL for accessing the PostgreSQL service container, a TEST_JWT_SECRET for testing JWT authentication, and other test-specific configuration values.

For any integration tests that interact with Stripe, the workflow provides a STRIPE_TEST_KEY, which is a test-mode API key from Stripe. Test-mode keys allow API calls to be made without charging real credit cards; they are safe to store in version control, though it is best practice to define them in GitHub Actions secrets rather than checking them into the repository.

Production credentials and secrets are never used in CI. The workflow uses only test-mode credentials and test data. This separation ensures that CI failures cannot corrupt production data or trigger real payments.

## Recap: Key Design Decisions

The test pipeline is designed for speed, feedback quality, and reliability. Speed is achieved through dependency caching and fail-fast job execution. Feedback quality is achieved through test result reporting and coverage metrics. Reliability is achieved through a clean PostgreSQL service container and explicit version pinning. The workflow runs on every push and pull request, ensuring continuous validation of code quality throughout development.
