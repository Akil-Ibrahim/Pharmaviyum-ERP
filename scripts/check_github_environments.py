import re
from pathlib import Path

CANONICAL_DEMO_ENVIRONMENT = "demo-pharmaviyum-erp"
MIGRATION_VALIDATION_ENVIRONMENT = "demo-migration-validation"
DEMO_DEPLOY_WORKFLOW = Path(".github/workflows/deploy-fastapi-cloud.yml")
MIGRATION_VALIDATION_WORKFLOW = Path(".github/workflows/validate-demo-migrations.yml")
PRODUCTION_MIGRATION_WORKFLOW = Path(".github/workflows/migrate-production-database.yml")
workflow_dir = Path(".github/workflows")
errors = []
environment_counts = {
    CANONICAL_DEMO_ENVIRONMENT: 0,
    MIGRATION_VALIDATION_ENVIRONMENT: 0,
}

# Match a job-level GitHub Environment block (4-space job property,
# 6-space nested name). Each approved environment is bound to one exact
# workflow so validation credentials cannot leak into deployment workflows.
environment_name = re.compile(
    r"^ {4}environment:[ \\t]*\\n^ {6}name:[ \\t]*([A-Za-z0-9_.-]+)[ \\t]*$",
    re.MULTILINE,
)
approved_workflows = {
    CANONICAL_DEMO_ENVIRONMENT: DEMO_DEPLOY_WORKFLOW,
    MIGRATION_VALIDATION_ENVIRONMENT: MIGRATION_VALIDATION_WORKFLOW,
}

for path in sorted((*workflow_dir.rglob("*.yml"), *workflow_dir.rglob("*.yaml"))):
    content = path.read_text(encoding="utf-8")
    for match in environment_name.finditer(content):
        actual = match.group(1)
        if actual not in approved_workflows:
            errors.append(
                f"{path}: unapproved GitHub Environment {actual!r}; "
                "only the isolated Demo and migration-validation environments are allowed"
            )
            continue

        environment_counts[actual] += 1
        expected_workflow = approved_workflows[actual]
        if path != expected_workflow:
            errors.append(
                f"{path}: environment {actual!r} may be used only by "
                f"{expected_workflow}"
            )

for environment, count in environment_counts.items():
    if count != 1:
        errors.append(
            f"Expected exactly one declaration of GitHub Environment "
            f"{environment!r}; found {count}"
        )

if PRODUCTION_MIGRATION_WORKFLOW.exists():
    errors.append(
        f"{PRODUCTION_MIGRATION_WORKFLOW}: Production database migration automation "
        "must remain outside the public repository"
    )

if not DEMO_DEPLOY_WORKFLOW.exists():
    errors.append(f"{DEMO_DEPLOY_WORKFLOW}: Demo deployment workflow is missing")
else:
    deploy_content = DEMO_DEPLOY_WORKFLOW.read_text(encoding="utf-8")
    required_markers = (
        "name: Deploy Demo to FastAPI Cloud",
        "name: demo-pharmaviyum-erp",
        "secrets.FASTAPI_CLOUD_DEMO_TOKEN",
        "secrets.FASTAPI_CLOUD_DEMO_APP_ID",
        "secrets.DEMO_DATABASE_URL",
        "https://pharmaviyum-erp.fastapicloud.dev",
        "ENVIRONMENT=staging",
    )
    for marker in required_markers:
        if marker not in deploy_content:
            errors.append(f"{DEMO_DEPLOY_WORKFLOW}: required Demo-only marker missing: {marker}")

    forbidden_markers = (
        "secrets.FASTAPI_CLOUD_TOKEN",
        "secrets.FASTAPI_CLOUD_APP_ID",
        "secrets.DATABASE_URL",
        "pharmaviyum-erp-crm.fastapicloud.dev",
        "c350a85c",
        "MIGRATION_VALIDATION_DATABASE_URL",
    )
    for marker in forbidden_markers:
        if marker in deploy_content:
            errors.append(f"{DEMO_DEPLOY_WORKFLOW}: forbidden Production/validation marker found: {marker}")

if not MIGRATION_VALIDATION_WORKFLOW.exists():
    errors.append(f"{MIGRATION_VALIDATION_WORKFLOW}: isolated migration validation workflow is missing")
else:
    migration_content = MIGRATION_VALIDATION_WORKFLOW.read_text(encoding="utf-8")
    required_migration_markers = (
        "name: Validate Demo Database Migrations",
        "name: demo-migration-validation",
        "secrets.MIGRATION_VALIDATION_DATABASE_URL",
        "vars.MIGRATION_VALIDATION_EXPECTED_HOST",
        "MIGRATE-ISOLATED-DEMO-BRANCH",
        "uv run alembic upgrade head",
    )
    for marker in required_migration_markers:
        if marker not in migration_content:
            errors.append(
                f"{MIGRATION_VALIDATION_WORKFLOW}: required isolated-validation marker missing: {marker}"
            )

    forbidden_migration_markers = (
        "secrets.DEMO_DATABASE_URL",
        "secrets.FASTAPI_CLOUD_DEMO_TOKEN",
        "secrets.FASTAPI_CLOUD_TOKEN",
        "fastapicloud.dev",
    )
    for marker in forbidden_migration_markers:
        if marker in migration_content:
            errors.append(
                f"{MIGRATION_VALIDATION_WORKFLOW}: forbidden deployment/Demo marker found: {marker}"
            )

if errors:
    print("ERROR: public deployment boundary validation failed:")
    for error in errors:
        print(f" - {error}")
    raise SystemExit(1)

print(
    "Environment guard passed: the Demo deployment environment is bound only "
    f"to {DEMO_DEPLOY_WORKFLOW}, and the isolated migration-validation environment "
    f"is bound only to {MIGRATION_VALIDATION_WORKFLOW}. "
    "Production deployment and migration workflows remain outside the public repository."
)
