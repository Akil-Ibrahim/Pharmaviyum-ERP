# CircleCI diagnostics

CircleCI writes the latest failed lint-job output to:

`ci-diagnostics/circleci-lint.log`

The file is generated in the CI workspace and uploaded as a CircleCI artifact.
It is intentionally not committed back to GitHub because CI logs may contain
repository-specific paths and diagnostic data.

Secrets and CI tokens are never written to the diagnostics file.
