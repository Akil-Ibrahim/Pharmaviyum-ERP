import re
from pathlib import Path

CANONICAL_DEMO_ENVIRONMENT = "demo-pharmaviyum-erp"
workflow_dir = Path(".github/workflows")
errors = []

# The public repository may target only the isolated Demo GitHub Environment.
# Production hosting, deployment and database operations are maintained outside
# this repository and must not be referenced by a public workflow.
environment_name = re.compile(
    r"^\s{6}environment:\s*\n\s{8}name:\s*([A-Za-z0-9_.-]+)\s*$",
    re.MULTILINE,
)

for path in sorted((*workflow_dir.rglob("*.yml"), *workflow_dir.rglob("*.yaml"))):
    content = path.read_text(encoding="utf-8")
    for match in environment_name.finditer(content):
        actual = match.group(1)
        if actual != CANONICAL_DEMO_ENVIRONMENT:
            errors.append(
                f"{path}: public workflows may use only {CANONICAL_DEMO_ENVIRONMENT!r}; "
                f"found {actual!r}"
            )

if errors:
    print("ERROR: non-Demo GitHub Environment reference detected:")
    for error in errors:
        print(f" - {error}")
    raise SystemExit(1)

print(
    "Environment guard passed: all declared GitHub Environments are scoped "
    f"to the public Demo environment {CANONICAL_DEMO_ENVIRONMENT!r}."
)
