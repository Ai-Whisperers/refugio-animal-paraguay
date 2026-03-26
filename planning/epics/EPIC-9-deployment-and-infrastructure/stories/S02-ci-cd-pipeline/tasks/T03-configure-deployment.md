# T03: Configure Deployment

## Overview

The deployment workflow is a separate GitHub Actions workflow that automatically deploys new versions of the application to the hosting environment. Unlike the test and linting workflows which run on every push and pull request, the deployment workflow triggers only when code is merged to main or when a release tag is created. This separation ensures that only vetted, tested code is deployed to production.

## Deployment Trigger Conditions

The deployment workflow has two trigger conditions. First, it runs automatically when a commit is merged to the main branch, indicating that code has passed all quality checks and been approved by reviewers. Second, it triggers when a release tag matching the pattern release-X.Y.Z is pushed, allowing for planned releases with specific version numbers.

Feature branch pushes do not trigger deployment. This ensures that work-in-progress code is never deployed, even if a developer accidentally pushes directly to a feature branch. The workflow design enforces that only main branch commits and explicit release tags trigger deployment, creating a clear deployment path.

## GitHub Environments for Secrets Management

The deployment workflow uses GitHub Environments to manage environment-specific secrets. GitHub Environments are a feature that allows separation of secrets and configuration between different target environments. A staging environment holds staging credentials such as a staging database URL, staging Stripe API keys, and staging authentication secrets. A production environment holds production credentials.

Each GitHub Environment can be configured to require manual approval before workflow steps execute. For the production environment, manual approval is enabled, which means when the deployment workflow reaches the production deployment step, a human reviewer must approve the deployment before it proceeds. This approval step provides a safety mechanism to prevent accidental deployments and allows teams to coordinate deployment windows.

## Deployment Steps in Sequence

The deployment workflow executes a series of steps in order to ensure code quality before deploying and to provide quick rollback capability if something goes wrong. First, the workflow runs the full test suite identical to the test pipeline. This reconfirms that the merged code passes all tests. If tests fail at this point, the deployment stops and an alert is sent.

Second, the workflow builds a Docker image containing the application and all dependencies. The image is tagged with the git commit SHA, a unique identifier for that specific version of code. Building the image at deployment time ensures that the exact code being deployed is what was tested and reviewed.

Third, the workflow pushes the Docker image to a container registry. The registry serves as a repository of known-good images. If a deployment fails and rollback is needed, the workflow can quickly re-pull the previous image without rebuilding it.

Fourth, the workflow deploys the new image to the target hosting provider. The provider is configurable and TBD, with candidates including Fly.io, Render, and Railway, all of which support API-driven deployments. The deployment step instructs the hosting provider to replace the running container with the new image.

Fifth, after the new image is running, the workflow runs smoke tests against the newly deployed instance. Smoke tests verify that the application is alive and functioning at a basic level before declaring the deployment successful.

## Rolling Deployment Strategy

The hosting provider should be configured to use a rolling deployment strategy, which means starting the new container, waiting for its health check to pass, and then stopping the old container. This approach ensures zero downtime during deployments because the application is always available while the old container is running.

The health check endpoint is a critical part of rolling deployment. The hosting provider repeatedly requests GET /health on the new container and waits for it to return HTTP 200 before considering the new container ready. Once the health check passes, the provider stops the old container.

The application implements the health check endpoint to verify that critical systems are operational. The health check not only confirms the server is running but also tests database connectivity, confirming that the database connection pool is healthy and the database is reachable. This prevents a deployment from being marked successful if the application starts but cannot connect to the database.

## Smoke Tests Post-Deployment

After the new version is live, the workflow executes smoke tests that verify the application is functioning. Smoke tests are minimal sanity checks, not comprehensive testing. The test suite already confirms functionality; smoke tests just verify that the deployed instance is reachable and responding.

The first smoke test sends a request to GET /health and verifies the response is HTTP 200 with a response body indicating database health. If the health endpoint returns an error or times out, the smoke test fails, indicating that the deployment did not succeed in bringing up a healthy instance.

The second smoke test sends a request to GET /animals, which is a public endpoint that retrieves the list of animals from the database. This request confirms that the application can serve real data from the database, not just that the server is running. If this request fails, the deployment is marked as failed.

If either smoke test fails, the deployment is considered failed, and a rollback is triggered immediately.

## Rollback on Failure

If smoke tests fail after deployment, the workflow automatically triggers a rollback. Rollback re-deploys the previous known-good image tag, which was recorded before the deployment started. The workflow queries the hosting provider to determine what image was running before the new deployment, then instructs it to re-deploy that image.

After rollback completes, the workflow runs smoke tests again against the rolled-back version. If the rolled-back version passes smoke tests, the rollback is successful, and the deployment is marked as failed with the new version. If rollback itself fails or the rolled-back version's smoke tests also fail, the workflow posts an alert and requires manual intervention because the situation indicates a deeper problem that automation cannot resolve.

Rollback capability is critical because it limits the blast radius of a bad deployment. If code introduces a critical bug that only manifests in production, automatic rollback ensures the outage is short and the system reverts to the last known-good state.

## Secrets Management

All secrets required for deployment are stored in GitHub Actions secrets scoped to the appropriate environment. Database URLs, Stripe API keys, JWT secrets, container registry credentials, and hosting provider API keys are all stored as secrets.

The workflow never logs secret values. Any step that uses a secret is configured to mask the secret value in logs, which means if the secret appears in output, it is replaced with asterisks before the log is stored. This prevents accidental credential leakage through log files.

Environment variable names are documented in a .env.example file that is checked into the repository. This documentation shows what secrets are needed and what format they should be in without exposing actual values. Developers new to the project can read .env.example to understand what configuration is required.

Production credentials are never used in CI. The test and linting workflows use only test-mode credentials and test databases, ensuring that CI failures or rogue scripts in CI cannot corrupt production data. Only the deployment workflow, which runs after human approval, has access to production credentials.

## Changelog and Version Management

The deployment workflow does not automatically update the CHANGELOG. Maintaining a CHANGELOG is a developer responsibility that should be done before tagging a release. The CHANGELOG documents what changed in each version and serves as human-readable release notes.

The workflow does record the deployed commit SHA and deployment timestamp in a deployment log for audit purposes. This log provides a historical record of which versions were deployed when, which is useful for debugging issues that occur after deployment or for understanding which features were live at a specific point in time.

## Summary: Production Readiness

The deployment workflow enforces a disciplined deployment process. Code must be merged to main and pass all tests and linting checks before deployment is possible. Manual approval is required before production deployment. Smoke tests verify the deployed instance is healthy. Automatic rollback limits the impact of failed deployments. Together, these mechanisms ensure that Refugio Animal Paraguay's platform remains operational and available to users and staff even when bugs slip through testing or production environments behave unexpectedly.
