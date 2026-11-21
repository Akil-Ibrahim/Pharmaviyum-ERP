import re
from pathlib import Path

CANONICAL_DEMO_ENVIRONMENT = "demo-pharmaviyum-erp"
DEMO_DEPLOY_WORKFLOW = Path(".github/workflows/deploy-fastapi-cloud.yml")
PRODUCTION_MIGRATION_WORKFLOW = Path(".github/workflows/migrate-production-database.yml")
workflow_dir = Path(".github/workflows")
errors = []
environment_count = 0

# Match a job-level GitHub Environment block (4-space job property,
# 6-space nested name). Do not allow a vacuous pass when no environment
# declaration is present.
environment_name = re.compile(
    r"^ {4}environment:[ \t]*\n^ {6}name:[ \t]*([A-Za-z0-9_.-]+)[ \t]*$",
    re.MULTILINE,
)

for path in sorted((*workflow_dir.rglob("*.yml"), *workflow_dir.rglob("*.yaml"))):
    content = path.read_text(encoding="utf-8")
    for match in environment_name.finditer(content):
        environment_count += 1
        actual = match.group(1)
        if actual != CANONICAL_DEMO_ENVIRONMENT:
            errors.append(
                f"{path}: public workflows may use only {CANONICAL_DEMO_ENVIRONMENT!r}; "
                f"found {actual!r}"
            )
        if path != DEMO_DEPLOY_WORKFLOW:
            errors.append(
                f"{path}: only the Demo deployment workflow may bind a protected environment"
            )

if environment_count != 1:
    errors.append(
        "Expected exactly one protected GitHub Environment declaration for the public Demo; "
        f"found {environment_count}"
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
    )
    for marker in forbidden_markers:
        if marker in deploy_content:
            errors.append(f"{DEMO_DEPLOY_WORKFLOW}: forbidden Production/legacy marker found: {marker}")

if errors:
    print("ERROR: public deployment boundary validation failed:")
    for error in errors:
        print(f" - {error}")
    raise SystemExit(1)

print(
    "Environment guard passed: the only protected deployment environment is "
    f"the isolated Demo environment {CANONICAL_DEMO_ENVIRONMENT!r}; "
    "Production deployment and migration workflows are not exposed here."
)
